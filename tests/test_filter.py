from unittest.mock import MagicMock, patch
from clr.core.filter import filter_message, filter_notification
from clr.models.message import IncomingMessage, MessageCategory
from clr.models.notification import Notification


def _make_message(**kwargs) -> IncomingMessage:
    defaults = dict(id="1", source="email", content="Test content", category=MessageCategory.email)
    defaults.update(kwargs)
    return IncomingMessage(**defaults)


def _make_notification(**kwargs) -> Notification:
    defaults = dict(id="n1", app="Slack", title="Hey", body="Got a minute?")
    defaults.update(kwargs)
    return Notification(**defaults)


@patch("clr.core.filter._get_client")
def test_filter_message_kept(mock_client):
    mock_response = MagicMock()
    mock_response.choices[0].message.content ='{"keep": true, "reason": "Important", "priority": "high", "action_required": true, "cognitive_cost": 6}'
    mock_client.return_value.chat.completions.create.return_value = mock_response

    result = filter_message(_make_message())

    assert not result.filtered_out
    assert result.priority.value == "high"
    assert result.action_required is True
    assert result.cognitive_cost == 6


@patch("clr.core.filter._get_client")
def test_filter_message_safety_override(mock_client):
    result = filter_message(_make_message(content="Everybody needs to leave the building right now"))

    assert not result.filtered_out
    assert result.priority.value == "critical"
    assert result.action_required is True
    assert result.cognitive_cost == 10
    mock_client.assert_not_called()


@patch("clr.core.filter._get_client")
def test_filter_message_filtered_out(mock_client):
    mock_response = MagicMock()
    mock_response.choices[0].message.content ='{"keep": false, "reason": "Marketing email", "priority": "low", "action_required": false, "cognitive_cost": 2}'
    mock_client.return_value.chat.completions.create.return_value = mock_response

    result = filter_message(_make_message(content="50% OFF TODAY ONLY!!!"))

    assert result.filtered_out
    assert result.filter_reason == "Marketing email"


@patch("clr.core.filter._get_client")
def test_filter_notification_kept(mock_client):
    mock_response = MagicMock()
    mock_response.choices[0].message.content ='{"keep": true, "reason": "Direct message from colleague"}'
    mock_client.return_value.chat.completions.create.return_value = mock_response

    result = filter_notification(_make_notification())
    assert result.kept is True


@patch("clr.core.filter._get_client")
def test_filter_notification_dropped(mock_client):
    mock_response = MagicMock()
    mock_response.choices[0].message.content ='{"keep": false, "reason": "Low-value system alert"}'
    mock_client.return_value.chat.completions.create.return_value = mock_response

    result = filter_notification(_make_notification(title="Build #4521 passed", body="CI succeeded"))
    assert result.kept is False