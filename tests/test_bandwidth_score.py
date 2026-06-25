from clr.core.bandwidth_score import compute_score, score_label, bandwidth_report
from clr.models.message import IncomingMessage, ProcessedMessage, MessageCategory


def _msg(id: str, cost: int, filtered: bool = False) -> ProcessedMessage:
    raw = IncomingMessage(id=id, source="test", content="x", category=MessageCategory.information)
    return ProcessedMessage(original=raw, cognitive_cost=cost, filtered_out=filtered)


def test_empty_messages_returns_100():
    assert compute_score([]) == 100


def test_all_filtered_returns_100():
    msgs = [_msg("1", 10, filtered=True), _msg("2", 8, filtered=True)]
    assert compute_score(msgs) == 100


def test_high_cost_lowers_score():
    msgs = [_msg("1", 9), _msg("2", 8), _msg("3", 10)]
    score = compute_score(msgs)
    assert score < 50


def test_low_cost_high_score():
    msgs = [_msg("1", 1), _msg("2", 2)]
    score = compute_score(msgs)
    assert score >= 70


def test_score_label_clear():
    assert score_label(80) == "clear"


def test_score_label_moderate():
    assert score_label(50) == "moderate"


def test_score_label_overloaded():
    assert score_label(20) == "overloaded"


def test_bandwidth_report_structure():
    msgs = [_msg("1", 8), _msg("2", 2, filtered=True), _msg("3", 9)]
    report = bandwidth_report(msgs)
    assert "score" in report
    assert "label" in report
    assert report["active_items"] == 2
    assert report["filtered_items"] == 1
    assert "1" in report["high_cost_items"]
    assert "3" in report["high_cost_items"]