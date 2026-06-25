from openai import OpenAI
from clr.config import settings
from clr.models.message import IncomingMessage


_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(base_url=settings.ollama_base_url, api_key="ollama")
    return _client


def predict_needs(messages: list[IncomingMessage], user_context: str = "") -> list[str]:
    """Given recent messages, predict what the user actually needs to know or act on."""
    if not messages:
        return []

    content_block = "\n".join(
        f"- [{m.category}] {m.source}: {m.content[:200]}" for m in messages
    )
    context_block = f"\nUser context: {user_context}" if user_context else ""

    prompt = f"""You are a cognitive assistant. Based on these recent incoming items, predict what the user actually needs to know or do right now.{context_block}

Incoming items:
{content_block}

List up to 5 specific, actionable insights or needs (one per line). Be concise."""

    response = _get_client().chat.completions.create(
        model=settings.model,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )

    lines = (response.choices[0].message.content or "").strip().splitlines()
    return [line.lstrip("•-–1234567890. ").strip() for line in lines if line.strip()]