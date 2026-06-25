import re

_SAFETY_PATTERN = re.compile(
    r"evacuat\w*"
    r"|active shooter"
    r"|fire alarm"
    r"|building (?:is |on )?fire"
    r"|gas leak"
    r"|bomb threat"
    r"|lockdown"
    r"|leave the building"
    r"|explosion"
    r"|life[- ]threatening"
    r"|call 911"
    r"|emergency services",
    re.IGNORECASE,
)


def is_safety_critical(content: str) -> bool:
    """Detect content describing an immediate physical-safety emergency.

    Acts as a deterministic backstop for the LLM filter, which can
    occasionally misclassify or rationalize away genuine emergencies.
    """
    return bool(_SAFETY_PATTERN.search(content))