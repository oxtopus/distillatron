from __future__ import annotations

from openai import OpenAI

RAW_TOPICS_PROMPT = """Analyze the following news article and generate 3-7 concise topic tags.
Return ONLY a JSON array of strings, nothing else.

Example: ["climate change", "renewable energy", "policy"]

Article:
{content}"""

NORMALIZE_PROMPT = """\
Given these topic tags, normalize them by merging synonyms and removing duplicates.
Use consistent terminology. Return ONLY a JSON array of strings, nothing else.

Tags: {tags}

Normalized:"""


def _generate_raw_topics(content: str, client: OpenAI, model: str) -> list[str]:
    """Generate raw topic tags from article content using DeepSeek."""
    prompt = RAW_TOPICS_PROMPT.format(content=content[:8000])
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content
    import json

    return json.loads(raw) if raw else []


def _normalize_topics(tags: list[str], client: OpenAI, model: str) -> list[str]:
    """Normalize topic tags by merging synonyms via a second LLM pass."""
    if not tags:
        return []
    prompt = NORMALIZE_PROMPT.format(tags=", ".join(tags))
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content
    import json

    return json.loads(raw) if raw else tags


def classify_content(content: str, client: OpenAI, model: str) -> list[str]:
    """Classify article content into normalized topic tags.

    Two-pass approach:
    1. Raw topic generation from content
    2. Normalization to merge synonyms and deduplicate
    """
    raw_topics = _generate_raw_topics(content, client, model)
    return _normalize_topics(raw_topics, client, model)
