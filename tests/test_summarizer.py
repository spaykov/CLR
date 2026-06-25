from unittest.mock import MagicMock, patch
from clr.core.summarizer import summarize, summarize_raw, summarize_batch
from clr.models.message import IncomingMessage, ProcessedMessage, MessageCategory


def _make_processed(filtered_out: bool = False) -> ProcessedMessage:
    msg = IncomingMessage(id="1", source="news", content="The quarterly results exceeded analyst expectations by 12%.", category=MessageCategory.information)
    return ProcessedMessage(original=msg, filtered_out=filtered_out)


@patch("clr.core.summarizer._get_client")
def test_summarize_adds_summary(mock_client):
    mock_response = MagicMock()
    mock_response.choices[0].message.content ="Q results beat expectations by 12%."
    mock_client.return_value.chat.completions.create.return_value = mock_response

    result = summarize(_make_processed())
    assert result.summary == "Q results beat expectations by 12%."


def test_summarize_skips_filtered():
    result = summarize(_make_processed(filtered_out=True))
    assert result.summary == ""


@patch("clr.core.summarizer._get_client")
def test_summarize_raw(mock_client):
    mock_response = MagicMock()
    mock_response.choices[0].message.content ="One sentence summary."
    mock_client.return_value.chat.completions.create.return_value = mock_response

    assert summarize_raw("Long article text...") == "One sentence summary."


@patch("clr.core.summarizer._get_client")
def test_summarize_batch(mock_client):
    mock_response = MagicMock()
    mock_response.choices[0].message.content ="Summary."
    mock_client.return_value.chat.completions.create.return_value = mock_response

    results = summarize_batch(["text one", "text two"])
    assert len(results) == 2
    assert all(r == "Summary." for r in results)