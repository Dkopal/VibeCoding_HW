import json
import re

import anthropic

MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = """You are a newsletter planning coordinator. Given a list of topics, create a structured research plan.
For each topic produce a focused search query and assign a priority (1 = highest).
Output ONLY a raw JSON array — no markdown, no code fences, no explanation.
Example: [{"topic":"AI","search_query":"latest AI news 2025","priority":1}]"""


def _extract_json(text: str) -> str:
    """Strip markdown code fences if present."""
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    return match.group(1).strip() if match else text


async def plan_topics(
    client: anthropic.AsyncAnthropic,
    topics: list[str],
    emit,
) -> list[dict]:
    response = await client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Topics: {json.dumps(topics)}",
            }
        ],
    )

    raw = _extract_json(response.content[0].text)
    tasks: list[dict] = json.loads(raw)

    await emit({"type": "supervisor:plan_ready", "payload": {"tasks": tasks}})
    return tasks
