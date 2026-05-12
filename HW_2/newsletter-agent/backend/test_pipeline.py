"""Test each agent step individually to pinpoint failures."""
import asyncio
import json
import os
from dotenv import load_dotenv
import anthropic

load_dotenv(dotenv_path=r"C:\Work\Projects\VibeCoding\HomeWorks\HW_2\.env", override=True)

client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


async def test_supervisor():
    print("\n--- Supervisor ---")
    from agents.supervisor import plan_topics

    async def emit(e): print("  SSE:", e["type"])

    tasks = await plan_topics(client, ["AI", "Space"], emit)
    print("  Tasks:", json.dumps(tasks, indent=2))
    return tasks


async def test_researcher(tasks):
    print("\n--- Researcher ---")
    from agents.researcher import research_topic

    async def emit(e): print("  SSE:", e["type"], e["payload"].get("topic", ""))

    result = await research_topic(client, tasks[0]["topic"], tasks[0]["search_query"], emit)
    print("  found:", result.get("found"))
    print("  summary[:100]:", str(result.get("summary", ""))[:100])
    return [result]


async def test_writer(results):
    print("\n--- Writer ---")
    from agents.writer import write_draft

    async def emit(e): print("  SSE:", e["type"])

    draft = await write_draft(client, results, "casual", "EN", emit)
    print("  draft[:150]:", draft[:150])
    return draft


async def test_editor(results, draft):
    print("\n--- Editor loop ---")
    from agents.editor import edit_loop
    from agents.writer import write_draft

    async def emit(e): print("  SSE:", e["type"])

    async def writer_fn(revision_instructions=None):
        return await write_draft(client, results, "casual", "EN", emit, revision_instructions)

    final = await edit_loop(client, draft, ["AI"], writer_fn, emit)
    print("  final draft[:100]:", final[:100])


async def main():
    tasks = await test_supervisor()
    results = await test_researcher(tasks)
    draft = await test_writer(results)
    await test_editor(results, draft)
    print("\nAll steps OK")


asyncio.run(main())
