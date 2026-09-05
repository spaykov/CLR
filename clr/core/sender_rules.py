from clr.core import storage


def match_sender_rule(source: str) -> dict | None:
    """Find a user-defined rule for this message's sender, if any.

    Matching is a case-insensitive substring check of the rule's pattern
    against the raw `From`-style source string, so a pattern like
    "deeplearning.ai" matches '"The Batch @ DeepLearning.AI" <thebatch@deeplearning.ai>'.
    `ignore` rules are checked before `digest` rules so an overlapping
    pattern resolves toward the cheaper/safer outcome.
    """
    source_lower = source.lower()
    rules = storage.list_sender_rules()

    for action in ("ignore", "digest"):
        for rule in rules:
            if rule["action"] == action and rule["pattern"].lower() in source_lower:
                return rule
    return None
