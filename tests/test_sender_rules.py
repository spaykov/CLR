from clr.core import sender_rules, storage


def test_no_rules_matches_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")
    assert sender_rules.match_sender_rule("someone@example.com") is None


def test_matches_pattern_as_case_insensitive_substring(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")
    storage.add_sender_rule("deeplearning.ai", "digest")

    rule = sender_rules.match_sender_rule('"The Batch @ DeepLearning.AI" <thebatch@deeplearning.ai>')
    assert rule is not None
    assert rule["action"] == "digest"


def test_no_match_when_pattern_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")
    storage.add_sender_rule("deeplearning.ai", "digest")

    assert sender_rules.match_sender_rule("someone-else@example.com") is None


def test_ignore_takes_precedence_over_digest_on_overlap(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")
    storage.add_sender_rule("example.com", "digest")
    storage.add_sender_rule("spam@example.com", "ignore")

    rule = sender_rules.match_sender_rule("spam@example.com")
    assert rule["action"] == "ignore"
