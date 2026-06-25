from openai import OpenAI
from clr.config import settings
from clr.core.json_utils import extract_json_object
from clr.models.task import DecisionTask


_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(base_url=settings.ollama_base_url, api_key="ollama")
    return _client


def handle_decision(task: DecisionTask) -> DecisionTask:
    """Evaluate a low-stakes decision and, if confident enough, decide automatically."""
    options_str = "\n".join(f"  {i+1}. {opt}" for i, opt in enumerate(task.options))
    prompt = f"""You are a cognitive assistant helping make low-value decisions to save mental energy.

Question: {task.question}
Context: {task.context or 'None provided'}
Options:
{options_str}

Evaluate whether this is a low-stakes decision you can make automatically.
Respond with JSON:
{{
  "can_auto_decide": true/false,
  "decision": "chosen option text or empty string",
  "confidence": 0.0-1.0,
  "reasoning": "one sentence"
}}"""

    response = _get_client().chat.completions.create(
        model=settings.model,
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )

    data = extract_json_object(response.choices[0].message.content or "{}")
    confidence = float(data.get("confidence", 0.0))

    if data.get("can_auto_decide") and confidence >= settings.auto_decision_confidence:
        task.auto_decided = True
        task.decision = data.get("decision", "")
        task.confidence = confidence
        task.reasoning = data.get("reasoning", "")

    return task