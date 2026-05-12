"""Quick SDK connectivity check — run once to verify ANTHROPIC_API_KEY works."""
import asyncio
import os
from dotenv import load_dotenv
import anthropic

load_dotenv(dotenv_path=r"C:\Work\Projects\VibeCoding\HomeWorks\HW_2\.env", override=True)


async def main() -> None:
    client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=64,
        messages=[{"role": "user", "content": "Reply with: SDK connection OK"}],
    )
    print(message.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())
