import anthropic

MODEL = "claude-haiku-4-5-20251001"


def _build_system_prompt(style: str, language: str) -> str:
    return (
        f"You are a newsletter writer. Write a {style} newsletter in {language}. "
        "Given research summaries, write a section per topic with a punchy headline and 2-3 paragraphs. "
        "Output markdown only — no JSON, no preamble."
    )


async def write_draft(
    client: anthropic.AsyncAnthropic,
    research_results: list[dict],
    style: str,
    language: str,
    emit,
    revision_instructions: str | None = None,
) -> str:
    content_parts = []
    for r in research_results:
        content_parts.append(f"### {r['topic']}\n{r['summary']}")
        if r.get("sources"):
            content_parts.append("Sources: " + ", ".join(r["sources"]))

    user_message = "Write the newsletter based on these research summaries:\n\n" + "\n\n".join(content_parts)
    if revision_instructions:
        user_message += f"\n\n---\nRevision instructions:\n{revision_instructions}"

    response = await client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=_build_system_prompt(style, language),
        messages=[{"role": "user", "content": user_message}],
    )

    draft = response.content[0].text
    await emit({"type": "writer:draft_ready", "payload": {"length": len(draft)}})
    return draft
