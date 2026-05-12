import asyncio
import json
import re

import anthropic

MODEL = "claude-haiku-4-5-20251001"


def _extract_json(text: str) -> str:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    return match.group(1).strip() if match else text


SYSTEM_PROMPT = """You are a research assistant. Search for the latest news and insights on the given topic.
Summarize findings in 3-5 bullet points. List up to 5 source URLs.
Output ONLY valid JSON with keys: topic, summary (string with bullet points), sources (array of strings), found (bool).
If nothing relevant is found, set found=false and leave summary/sources empty."""


async def research_topic(
    client: anthropic.AsyncAnthropic,
    topic: str,
    search_query: str,
    emit,
) -> dict:
    await emit({"type": "research:started", "payload": {"topic": topic}})

    response = await client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
        messages=[
            {
                "role": "user",
                "content": f"Research topic: {topic}\nSearch query: {search_query}",
            }
        ],
    )

    raw = next(
        (block.text for block in response.content if hasattr(block, "text")),
        None,
    )

    if raw:
        try:
            result = json.loads(_extract_json(raw))
        except json.JSONDecodeError:
            result = {"topic": topic, "summary": raw, "sources": [], "found": True}
    else:
        result = {"topic": topic, "summary": "", "sources": [], "found": False}

    await emit({"type": "research:done", "payload": result})
    return result


async def research_all(
    client: anthropic.AsyncAnthropic,
    tasks: list[dict],
    emit,
) -> list[dict]:
    return await asyncio.gather(
        *[research_topic(client, t["topic"], t["search_query"], emit) for t in tasks]
    )
