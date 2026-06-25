from openai import OpenAI
from clr.config import settings
from clr.models.message import ProcessedMessage


_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(base_url=settings.ollama_base_url, api_key="ollama")
    return _client


def suggest_reductions(messages: list[ProcessedMessage], score: int) -> list[str]:
    """Suggest concrete ways to reduce cognitive load given the current state."""
    active = [m for m in messages if not m.filtered_out]
    high_cost = [m for m in active if m.cognitive_cost >= 7]

    summary_lines = "\n".join(
        f"- [{m.original.source}] cost={m.cognitive_cost}: {m.original.content[:100]}"
        for m in high_cost[:10]
    )

    prompt = f"""You are a cognitive load advisor. The user's mental bandwidth score is {score}/100 ({_label(score)}).

High-cost active items:
{summary_lines or '(none)'}

Suggest 3–5 practical, specific actions the user can take right now to reduce cognitive load.
Each suggestion should be one short sentence. Output one per line."""

    response = _get_client().chat.completions.create(
        model=settings.model,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )

    lines = (response.choices[0].message.content or "").strip().splitlines()
    return [line.lstrip("•-–1234567890. ").strip() for line in lines if line.strip()]


def _label(score: int) -> str:
    if score >= settings.bandwidth_high_threshold:
        return "clear"
    if score >= settings.bandwidth_low_threshold:
        return "moderate"
    return "overloaded"