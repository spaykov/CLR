from email.message import EmailMessage

from clr.core.email_fetcher import _stable_id


def _msg(**headers) -> EmailMessage:
    msg = EmailMessage()
    for key, value in headers.items():
        msg[key.replace("_", "-")] = value
    return msg


def test_stable_id_is_deterministic_for_same_message_id():
    msg = _msg(Message_ID="<abc123@mail.gmail.com>")
    assert _stable_id(msg, "Subject", "a@b.com") == _stable_id(msg, "Subject", "a@b.com")


def test_stable_id_matches_across_separate_fetches_of_same_email():
    # Two independently-constructed messages with the same Message-ID (as a
    # refetch of the same email would produce) must resolve to the same id.
    first = _msg(Message_ID="<same@mail.gmail.com>")
    second = _msg(Message_ID="<same@mail.gmail.com>")
    assert _stable_id(first, "Subject", "a@b.com") == _stable_id(second, "Subject", "a@b.com")


def test_stable_id_differs_for_different_message_ids():
    first = _msg(Message_ID="<one@mail.gmail.com>")
    second = _msg(Message_ID="<two@mail.gmail.com>")
    assert _stable_id(first, "Subject", "a@b.com") != _stable_id(second, "Subject", "a@b.com")


def test_stable_id_falls_back_to_composite_fields_when_message_id_missing():
    msg = _msg(Date="Mon, 1 Jan 2026 00:00:00 +0000")
    id1 = _stable_id(msg, "Hello", "a@b.com")
    id2 = _stable_id(msg, "Hello", "a@b.com")
    assert id1 == id2

    different_subject = _stable_id(msg, "Different", "a@b.com")
    assert different_subject != id1
