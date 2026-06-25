from openai import OpenAI
from clr.config import settings
from clr.core.json_utils import extract_json_object
from clr.core.safety import is_safety_critical
from clr.models.message import IncomingMessage, ProcessedMessage, Priority
from clr.models.notification import Notification, FilteredNotification


_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(base_url=settings.ollama_base_url, api_key="ollama")
    return _client


def filter_message(message: IncomingMessage) -> ProcessedMessage:
    """Decide whether a message deserves the user's attention and why."""
    if is_safety_critical(message.content):
        return ProcessedMessage(
            original=message,
            priority=Priority.critical,
            action_required=True,
            filtered_out=False,
            filter_reason="Safety override: message matches an emergency/evacuation pattern.",
            cognitive_cost=10,
        )

    prompt = f"""You are a cognitive firewall. Evaluate this incoming message and decide if it needs the user's attention.

Source: {message.source}
Category: {message.category}
Content: {message.content}

Rules:
- Judge based on the actual content, not just the category label.
- Anything indicating immediate physical danger, an emergency, or an evacuation must be kept (keep: true) with priority "critical" and action_required true, regardless of category or source.
- In "reason", briefly explain what in the content led to your decision (e.g. the specific request, deadline, or risk — or why it's safe to ignore).

Respond with a JSON object. Values must be plain JSON (no comments or extra text after numbers):
{{
  "keep": true/false,
  "reason": "brief reason referencing the content",
  "priority": "low|medium|high|critical",
  "action_required": true/false,
  "cognitive_cost": 0-10
}}"""

    response = _get_client().chat.completions.create(
        model=settings.model,
        max_tokens=256,
        messages=[{"role": "user", "content": prompt}],
    )

    data = extract_json_object(response.choices[0].message.content or "{}")

    return ProcessedMessage(
        original=message,
        priority=Priority(data.get("priority", "medium")),
        action_required=data.get("action_required", False),
        filtered_out=not data.get("keep", True),
        filter_reason=data.get("reason", ""),
        cognitive_cost=data.get("cognitive_cost", 5),
    )


def filter_notification(notification: Notification) -> FilteredNotification:
    """Filter a single app notification."""
    prompt = f"""You are a cognitive firewall. Should the user see this notification?

App: {notification.app}
Title: {notification.title}
Body: {notification.body}
Urgent: {notification.is_urgent}

Rules:
- If Urgent is true, keep the notification (keep: true) unless it is obviously spam, a test message, or automated noise unrelated to the user.
- Base your decision only on the information given above. Do not assume or invent details about the user (e.g. their team, role, or on-call status).

Reply with JSON: {{"keep": true/false, "reason": "brief reason"}}"""

    response = _get_client().chat.completions.create(
        model=settings.model,
        max_tokens=128,
        messages=[{"role": "user", "content": prompt}],
    )

    data = extract_json_object(response.choices[0].message.content or "{}")

    return FilteredNotification(
        original=notification,
        kept=data.get("keep", True),
        reason=data.get("reason", ""),
    )