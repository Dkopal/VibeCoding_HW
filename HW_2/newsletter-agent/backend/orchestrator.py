import json
import os
from collections.abc import AsyncGenerator

import anthropic
import markdown as md
from dotenv import load_dotenv

from agents.editor import edit_loop
from agents.researcher import research_all
from agents.supervisor import plan_topics
from agents.writer import write_draft

load_dotenv(dotenv_path=r"C:\Work\Projects\VibeCoding\HomeWorks\HW_2\.env", override=True)


def _to_html(markdown_text: str) -> str:
    body = md.markdown(markdown_text, extensions=["extra"])
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: Georgia, serif; max-width: 680px; margin: 40px auto; color: #222; line-height: 1.7; }}
  h1 {{ font-size: 2rem; border-bottom: 2px solid #e63946; padding-bottom: 8px; }}
  h2, h3 {{ color: #1d3557; }}
  a {{ color: #e63946; }}
  p {{ margin: 0.8em 0; }}
</style>
</head>
<body>{body}</body>
</html>"""


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"


async def run_pipeline(topics: list[str], style: str, language: str) -> AsyncGenerator[str, None]:  # noqa: C901
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    pending: list[dict] = []

    async def emit(event: dict) -> None:
        pending.append(event)

    def flush() -> list[str]:
        chunks = [_sse(e) for e in pending]
        pending.clear()
        return chunks

    # Step 2 — Supervisor
    tasks = await plan_topics(client, topics, emit)
    for chunk in flush():
        yield chunk

    # Step 3 — Parallel research
    results = await research_all(client, tasks, emit)
    for chunk in flush():
        yield chunk

    # Step 4 — Conditional gate
    valid = [r for r in results if r.get("found", False)]
    skipped = [r for r in results if not r.get("found", False)]
    for r in skipped:
        yield _sse({"type": "research:skipped", "payload": {"topic": r["topic"]}})

    if not valid:
        yield _sse({"type": "error", "payload": {"message": "No research results found for any topic."}})
        return

    # Step 5 — Writer (initial draft)
    draft = await write_draft(client, valid, style, language, emit)
    for chunk in flush():
        yield chunk

    # Step 6 — Editor loop; writer_fn is a plain coroutine returning a new draft
    async def writer_fn(revision_instructions: str | None = None) -> str:
        return await write_draft(client, valid, style, language, emit, revision_instructions)

    final_draft = await edit_loop(client, draft, topics, writer_fn, emit)
    for chunk in flush():
        yield chunk

    # Step 7 — Output formatter
    html = _to_html(final_draft)
    yield _sse({"type": "output:ready", "payload": {"html": html}})
