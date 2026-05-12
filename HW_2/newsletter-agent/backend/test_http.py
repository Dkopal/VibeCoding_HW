"""Test the HTTP SSE endpoint end-to-end."""
import json
import httpx
import asyncio


async def main():
    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream(
            "POST",
            "http://localhost:8000/generate",
            json={"topics": ["AI"], "style": "casual", "language": "EN"},
        ) as response:
            print(f"Status: {response.status_code}")
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event = json.loads(line[6:])
                    if event["type"] == "output:ready":
                        print(f"  {event['type']} — HTML length: {len(event['payload']['html'])}")
                    else:
                        print(f"  {event['type']}")


asyncio.run(main())
