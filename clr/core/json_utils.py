import json
import re

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def extract_json_object(text: str) -> dict:
    """Parse a JSON object out of an LLM response.

    Models often wrap JSON in markdown code fences and/or follow it with
    explanatory prose, neither of which `json.loads` tolerates. This strips
    a fence if present and decodes only the leading JSON object, ignoring
    any trailing text.
    """
    text = text.strip()

    fence_match = _FENCE_RE.search(text)
    if fence_match:
        text = fence_match.group(1).strip()

    start = text.find("{")
    if start == -1:
        return {}

    try:
        obj, _ = json.JSONDecoder().raw_decode(text, start)
    except json.JSONDecodeError:
        return {}

    return obj if isinstance(obj, dict) else {}