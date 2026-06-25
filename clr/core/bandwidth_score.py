from clr.config import settings
from clr.models.message import ProcessedMessage


def compute_score(messages: list[ProcessedMessage]) -> int:
    """
    Return a mental bandwidth score from 0 (overloaded) to 100 (clear).

    Score drops with each unfiltered, high-cognitive-cost item.
    """
    if not messages:
        return 100

    active = [m for m in messages if not m.filtered_out]
    if not active:
        return 100

    total_cost = sum(m.cognitive_cost for m in active)
    max_cost = len(active) * 10

    # Invert: high cost → low bandwidth
    raw = 1.0 - (total_cost / max_cost)
    score = max(0, min(100, int(raw * 100)))
    return score


def score_label(score: int) -> str:
    if score >= settings.bandwidth_high_threshold:
        return "clear"
    if score >= settings.bandwidth_low_threshold:
        return "moderate"
    return "overloaded"


def bandwidth_report(messages: list[ProcessedMessage]) -> dict:
    score = compute_score(messages)
    active = [m for m in messages if not m.filtered_out]
    filtered = [m for m in messages if m.filtered_out]

    return {
        "score": score,
        "label": score_label(score),
        "active_items": len(active),
        "filtered_items": len(filtered),
        "high_cost_items": [m.original.id for m in active if m.cognitive_cost >= 7],
    }