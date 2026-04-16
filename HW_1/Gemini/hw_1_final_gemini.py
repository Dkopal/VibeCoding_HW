"""
LLM + Tool Use CLI – Google Gemini (jen kalkulačka)
====================================================
Ekvivalent Anthropic skriptu, ale běží nad Google Gemini API.
Gemini má štědrý free tier – stačí API klíč z https://aistudio.google.com.

Funkce
------
- Vstup od uživatele: jednorázový dotaz přes CLI (-p / --prompt),
  nebo interaktivní REPL (bez argumentu) s historií konverzace.
- Konfigurace přes CLI flagy, proměnné prostředí i .env soubor.
- Jediný registrovaný nástroj: `calculator`. Vše ostatní je normální chat.
- Logování přes `logging`, typové anotace, dataclasses.

Instalace
---------
    pip install google-genai python-dotenv

Získání API klíče (zdarma)
--------------------------
    1) Jdi na https://aistudio.google.com
    2) Přihlaš se Google účtem
    3) Klikni "Get API key" → "Create API key"
    4) Ulož do proměnné prostředí GEMINI_API_KEY nebo .env

Spuštění
--------
    setx GEMINI_API_KEY "AIza..."   # Windows (pak nové okno PS)
    export GEMINI_API_KEY="AIza..." # macOS/Linux

    # jednorázově – matematika (použije calculator)
    python hw_1_final_gemini.py -p "Kolik je (17*24) + 2**10?"

    # jednorázově – běžný chat (bez nástroje)
    python hw_1_final_gemini.py -p "Napiš mi haiku o Pythonu."

    # interaktivně (zachová historii)
    python hw_1_final_gemini.py

Struktura .env (nepovinné)
--------------------------
    GEMINI_API_KEY=AIza...
    GEMINI_MODEL=gemini-2.5-flash
    LOG_LEVEL=INFO
"""

from __future__ import annotations

import argparse
import ast
import json
import logging
import operator as op
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Callable

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # .env je nepovinný

from google import genai
from google.genai import types


# ======================================================================
# Konfigurace
# ======================================================================

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
DEFAULT_SYSTEM_PROMPT = (
    "Jsi přátelský asistent. Pro matematické výpočty VŽDY použij nástroj "
    "`calculator` místo toho, abys počítal/a zpaměti. Všechno ostatní "
    "(vysvětlování, kreativní psaní, konverzace, kódování…) řeš jako "
    "běžný chat bez volání nástrojů."
)

log = logging.getLogger("llm-tool-use-gemini")


# ======================================================================
# Nástroj: kalkulačka
# ======================================================================

_ALLOWED_OPERATORS = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
    ast.Div: op.truediv, ast.Pow: op.pow, ast.Mod: op.mod,
    ast.FloorDiv: op.floordiv, ast.USub: op.neg, ast.UAdd: op.pos,
}


def _safe_eval(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](
            _safe_eval(node.left), _safe_eval(node.right)
        )
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_safe_eval(node.operand))
    raise ValueError(f"Nepovolený uzel: {ast.dump(node)}")


def tool_calculator(expression: str) -> str:
    """Bezpečný kalkulačkový nástroj (bez eval())."""
    tree = ast.parse(expression, mode="eval")
    return str(_safe_eval(tree.body))


# ======================================================================
# Registr nástrojů
# ======================================================================

@dataclass
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., str]

    def to_gemini(self) -> dict[str, Any]:
        """Gemini očekává function_declaration ve formátu OpenAPI subset."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


TOOLS: dict[str, Tool] = {
    "calculator": Tool(
        name="calculator",
        description=(
            "Vyhodnotí matematický výraz a vrátí numerický výsledek. "
            "Používej pro jakoukoliv aritmetiku. "
            "Podporuje +, -, *, /, **, %, // a závorky."
        ),
        parameters={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Výraz, např. '(2+3)*4' nebo '2**10'.",
                }
            },
            "required": ["expression"],
        },
        handler=tool_calculator,
    ),
}


def dispatch_tool(name: str, arguments: dict[str, Any]) -> tuple[str, bool]:
    """Spustí nástroj. Vrací (výsledek_jako_string, is_error)."""
    tool = TOOLS.get(name)
    if tool is None:
        return f"Neznámý nástroj: {name}", True
    try:
        return tool.handler(**arguments), False
    except Exception as exc:  # noqa: BLE001
        log.exception("Chyba při volání nástroje %s", name)
        return f"Chyba nástroje {name}: {exc}", True


# ======================================================================
# Klient & konverzační smyčka
# ======================================================================

@dataclass
class ChatConfig:
    model: str = DEFAULT_MODEL
    system: str = DEFAULT_SYSTEM_PROMPT


@dataclass
class ChatSession:
    config: ChatConfig
    client: genai.Client = field(default_factory=genai.Client)
    # historie v Gemini formátu: list[types.Content]
    history: list[types.Content] = field(default_factory=list)

    def _gemini_config(self) -> types.GenerateContentConfig:
        gemini_tool = types.Tool(
            function_declarations=[t.to_gemini() for t in TOOLS.values()]
        )
        return types.GenerateContentConfig(
            system_instruction=self.config.system,
            tools=[gemini_tool],
        )

    def ask(self, user_input: str) -> str:
        """Pošle zprávu, dořeší případná volání nástroje a vrátí text."""
        self.history.append(
            types.Content(role="user", parts=[types.Part(text=user_input)])
        )

        while True:
            log.debug("Odesílám %d zpráv do modelu %s",
                      len(self.history), self.config.model)
            response = self.client.models.generate_content(
                model=self.config.model,
                contents=self.history,
                config=self._gemini_config(),
            )

            candidate = response.candidates[0]
            self.history.append(candidate.content)

            # Posbírej volání nástrojů
            function_calls = [
                p.function_call for p in candidate.content.parts
                if getattr(p, "function_call", None) is not None
            ]

            # Žádné volání -> běžná chatová odpověď
            if not function_calls:
                text_parts = [
                    p.text for p in candidate.content.parts
                    if getattr(p, "text", None)
                ]
                return "".join(text_parts).strip()

            # Zpracuj všechna volání a pošli výsledky zpět
            response_parts = []
            for fc in function_calls:
                args = dict(fc.args) if fc.args else {}
                log.info("tool_use  -> %s(%s)",
                         fc.name, json.dumps(args, ensure_ascii=False))
                result, is_error = dispatch_tool(fc.name, args)
                log.info("tool_result <- %s", result)

                payload = (
                    {"error": result} if is_error else {"result": result}
                )
                response_parts.append(
                    types.Part.from_function_response(
                        name=fc.name, response=payload,
                    )
                )

            self.history.append(
                types.Content(role="user", parts=response_parts)
            )


# ======================================================================
# CLI
# ======================================================================

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="LLM tool-use demo (Google Gemini API) – jen kalkulačka.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-p", "--prompt",
        help="Jednorázový dotaz. Bez tohoto argumentu se spustí interaktivní REPL.",
    )
    parser.add_argument(
        "-m", "--model", default=DEFAULT_MODEL,
        help="ID modelu (GEMINI_MODEL v .env). Free tier: gemini-2.5-flash.",
    )
    parser.add_argument(
        "--system", default=DEFAULT_SYSTEM_PROMPT,
        help="Systémový prompt.",
    )
    parser.add_argument(
        "-v", "--verbose", action="count", default=0,
        help="-v = INFO, -vv = DEBUG.",
    )
    return parser.parse_args(argv)


def setup_logging(verbose: int) -> None:
    level = {0: "WARNING", 1: "INFO", 2: "DEBUG"}.get(verbose, "DEBUG")
    level = os.getenv("LOG_LEVEL", level)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-5s %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("httpcore").setLevel("WARNING")
    logging.getLogger("httpx").setLevel("WARNING")


def ensure_api_key() -> None:
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
        sys.exit(
            "Chyba: chybí GEMINI_API_KEY.\n"
            "  1) Jdi na https://aistudio.google.com a vygeneruj API key\n"
            "  2) setx GEMINI_API_KEY \"AIza...\"  (Windows)\n"
            "     export GEMINI_API_KEY=\"AIza...\" (macOS/Linux)\n"
            "     nebo vlož do .env souboru"
        )


def run_repl(session: ChatSession) -> None:
    print("Interaktivní režim (Gemini) – ukonči ':q' nebo Ctrl+D.")
    print("Matematiku model spočítá přes `calculator`, vše ostatní jako chat.\n")
    while True:
        try:
            user = input("» ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if user in {":q", ":quit", "exit"}:
            return
        if not user:
            continue
        try:
            answer = session.ask(user)
        except Exception as exc:  # noqa: BLE001
            log.exception("Volání API selhalo")
            print(f"[chyba] {exc}\n")
            continue
        print(f"\n{answer}\n")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    setup_logging(args.verbose)
    ensure_api_key()

    config = ChatConfig(model=args.model, system=args.system)
    session = ChatSession(config=config)

    log.info("Model=%s, tools=%s", config.model, list(TOOLS))

    if args.prompt:
        print(session.ask(args.prompt))
    else:
        run_repl(session)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())