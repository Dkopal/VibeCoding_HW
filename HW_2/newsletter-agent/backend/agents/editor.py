import anthropic

MODEL = "claude-haiku-4-5-20251001"
MAX_ITERATIONS = 3

SYSTEM_PROMPT = """You are a newsletter editor. Evaluate the draft against these criteria:
1. Minimum 100 words per section
2. Consistent tone throughout
3. All requested topics are covered
4. No repetition between sections

If ALL criteria are met, respond with exactly: APPROVED
Otherwise respond with specific, numbered revision instructions only — no preamble."""


async def edit_loop(
    client: anthropic.AsyncAnthropic,
    draft: str,
    topics: list[str],
    writer_fn,
    emit,
) -> str:
    current_draft = draft
    topics_list = ", ".join(topics)

    for iteration in range(1, MAX_ITERATIONS + 1):
        await emit({"type": f"editor:iteration:{iteration}", "payload": {"iteration": iteration}})

        response = await client.messages.create(
            model=MODEL,
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Required topics: {topics_list}\n\n"
                        f"Draft:\n{current_draft}"
                    ),
                }
            ],
        )

        feedback = response.content[0].text.strip()

        if feedback == "APPROVED":
            await emit({"type": "editor:approved", "payload": {"iterations": iteration}})
            return current_draft

        current_draft = await writer_fn(revision_instructions=feedback)

    await emit({"type": "editor:approved", "payload": {"iterations": MAX_ITERATIONS, "forced": True}})
    return current_draft
