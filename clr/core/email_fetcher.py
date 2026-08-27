import hashlib
import imaplib
from datetime import datetime, timedelta, timezone
from email import message_from_bytes
from email.message import Message
from email.utils import parsedate_to_datetime

from clr.config import settings
from clr.models.message import IncomingMessage, MessageCategory

IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993
BODY_LIMIT = 2000
MAX_MESSAGES = 50  # safety cap: each fetched message costs 3 LLM calls in the pipeline


def has_credentials() -> bool:
    return bool(settings.gmail_address and settings.gmail_app_password)


def fetch_emails(hours: int = 24) -> list[IncomingMessage]:
    if not has_credentials():
        raise ValueError(
            "Gmail not configured. Set CLR_GMAIL_ADDRESS and CLR_GMAIL_APP_PASSWORD in .env."
        )

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    # IMAP's SINCE is date-only (no time-of-day), so search a day early and
    # filter precisely against `cutoff` below using the real Date header.
    search_since = (cutoff - timedelta(days=1)).strftime("%d-%b-%Y")

    conn = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    try:
        conn.login(settings.gmail_address, settings.gmail_app_password)
        conn.select("INBOX", readonly=True)

        status, data = conn.search(None, f'(SINCE "{search_since}")')
        if status != "OK" or not data or not data[0]:
            return []

        messages = []
        for msg_id in reversed(data[0].split()):  # newest sequence number first
            status, msg_data = conn.fetch(msg_id, "(RFC822)")
            if status != "OK" or not msg_data or not msg_data[0]:
                continue
            parsed = message_from_bytes(msg_data[0][1])

            received_at = _parse_date(parsed.get("Date", ""))
            if received_at < cutoff:
                continue  # SINCE only narrowed by day; skip anything outside the real window

            messages.append(_to_incoming_message(parsed, received_at))
            if len(messages) >= MAX_MESSAGES:
                break
        return messages
    finally:
        conn.logout()


def _parse_date(date_str: str) -> datetime:
    try:
        parsed = parsedate_to_datetime(date_str)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except Exception:
        return datetime.now(timezone.utc)


def _to_incoming_message(msg: Message, received_at: datetime) -> IncomingMessage:
    subject = msg.get("Subject", "(no subject)")
    from_addr = msg.get("From", "unknown")

    body = _extract_body(msg)
    content = f"{subject}\n\n{body}".strip() if body else subject

    return IncomingMessage(
        id=_stable_id(msg, subject, from_addr),
        source=from_addr,
        content=content,
        category=MessageCategory.email,
        received_at=received_at,
        metadata={"subject": subject, "from": from_addr},
    )


def _stable_id(msg: Message, subject: str, from_addr: str) -> str:
    # Message-ID is unique per email and stable across refetches; without it
    # (rare, but some senders omit it) fall back to a composite of fields that
    # together identify "the same email" closely enough for dedup purposes.
    message_id = msg.get("Message-ID") or msg.get("Message-Id")
    basis = message_id.strip() if message_id else f"{from_addr}|{msg.get('Date', '')}|{subject}"
    return hashlib.sha256(basis.encode("utf-8", errors="replace")).hexdigest()


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