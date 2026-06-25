import poplib
import uuid
from datetime import datetime, timezone
from email import message_from_bytes
from email.message import Message
from email.utils import parsedate_to_datetime

from clr.config import settings
from clr.models.message import IncomingMessage, MessageCategory

POP3_HOST = "pop.gmail.com"
POP3_PORT = 995
BODY_LIMIT = 2000


def has_credentials() -> bool:
    return bool(settings.gmail_address and settings.gmail_app_password)


def fetch_emails(limit: int = 10) -> list[IncomingMessage]:
    if not has_credentials():
        raise ValueError(
            "Gmail not configured. Set CLR_GMAIL_ADDRESS and CLR_GMAIL_APP_PASSWORD in .env."
        )

    conn = poplib.POP3_SSL(POP3_HOST, POP3_PORT)
    try:
        conn.user(settings.gmail_address)
        conn.pass_(settings.gmail_app_password)

        total = len(conn.list()[1])
        first = max(1, total - limit + 1)

        messages = []
        for i in range(total, first - 1, -1):
            _, lines, _ = conn.retr(i)
            raw = b"\n".join(lines)
            messages.append(_to_incoming_message(message_from_bytes(raw)))
        return messages
    finally:
        conn.quit()


def _to_incoming_message(msg: Message) -> IncomingMessage:
    subject = msg.get("Subject", "(no subject)")
    from_addr = msg.get("From", "unknown")
    date_str = msg.get("Date", "")

    try:
        received_at = parsedate_to_datetime(date_str)
        if received_at.tzinfo is None:
            received_at = received_at.replace(tzinfo=timezone.utc)
    except Exception:
        received_at = datetime.now(timezone.utc)

    body = _extract_body(msg)
    content = f"{subject}\n\n{body}".strip() if body else subject

    return IncomingMessage(
        id=str(uuid.uuid4()),
        source=from_addr,
        content=content,
        category=MessageCategory.email,
        received_at=received_at,
        metadata={"subject": subject, "from": from_addr},
    )


def _extract_body(msg: Message) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and not part.get_filename():
                return _decode_part(part)[:BODY_LIMIT]
        return ""
    return _decode_part(msg)[:BODY_LIMIT]


def _decode_part(part: Message) -> str:
    payload = part.get_payload(decode=True)
    if not payload:
        return ""
    charset = part.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace")