from unittest.mock import MagicMock, patch
from clr.core.rewriter import rewrite, rewrite_raw
from clr.models.message import IncomingMessage, ProcessedMessage, MessageCategory


def _make_processed(filtered_out: bool = False) -> ProcessedMessage:
    msg = IncomingMessage(id="1", source="email", content="Please be advised that due to unforeseen circumstances we must reschedule.", category=MessageCategory.email)
    return ProcessedMessage(original=msg, filtered_out=filtered_out)


@patch("clr.core.rewriter._get_client")
def test_rewrite_simplifies(mock_client):
    mock_response = MagicMock()
    mock_response.choices[0].message.content ="We need to reschedule."
    mock_client.return_value.chat.completions.create.return_value = mock_response

    result = rewrite(_make_processed())
    assert result.simplified == "We need to reschedule."


def test_rewrite_skips_filtered():
    result = rewrite(_make_processed(filtered_out=True))
    assert result.simplified == ""


@patch("clr.core.rewriter._get_client")
def test_rewrite_raw(mock_client):
    mock_response = MagicMock()
    mock_response.choices[0].message.content ="Short version."
    mock_client.return_value.chat.completions.create.return_value = mock_response

    assert rewrite_raw("Long complicated text here.") == "Short version."