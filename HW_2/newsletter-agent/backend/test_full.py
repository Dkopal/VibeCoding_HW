"""Run the full run_pipeline generator to catch the exact crash."""
import asyncio
import json
import sys
sys.path.insert(0, ".")

from orchestrator import run_pipeline


async def main():
    event_count = 0
    async for chunk in run_pipeline(["AI"], "casual", "EN"):
        if chunk.startswith("data: "):
            event = json.loads(chunk[6:])
            event_count += 1
            if event["type"] == "output:ready":
                print(f"  {event['type']} — HTML {len(event['payload']['html'])} chars")
            else:
                print(f"  {event['type']}")
    print(f"\nDone — {event_count} SSE events")


asyncio.run(main())
