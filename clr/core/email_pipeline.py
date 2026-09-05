from clr.core import advisor, bandwidth_score, email_fetcher, filter, predictor, rewriter, storage, summarizer

EMPTY_BANDWIDTH = {"score": 100, "label": "clear", "active_items": 0, "filtered_items": 0, "high_cost_items": []}


def run_email_fetch(hours: int) -> dict:
    """Fetch Gmail messages from the last N hours and run them through the
    full CLR pipeline (filter -> summarize -> rewrite -> persist).

    Shared by the manual /email/fetch route and the background auto-fetch
    loop in main.py, so both go through identical logic.
    """
    messages = email_fetcher.fetch_emails(hours=hours)

    fetched_count = len(messages)
    deleted_ids = storage.get_deleted_ids([m.id for m in messages])
    messages = [m for m in messages if m.id not in deleted_ids]

    if not messages:
        return {
            "processed": [],
            "bandwidth": EMPTY_BANDWIDTH,
            "predicted_needs": [],
            "suggestions": [],
            "fetched": fetched_count,
            "skipped_deleted": len(deleted_ids),
        }

    results = []
    for msg in messages:
        p = filter.filter_message(msg)
        p = summarizer.summarize(p)
        p = rewriter.rewrite(p)
        storage.save_processed(p)
        results.append(p)

    report = bandwidth_score.bandwidth_report(results)
    suggestions_list = advisor.suggest_reductions(results, report["score"])
    needs = predictor.predict_needs(messages)

    return {
        "processed": results,
        "bandwidth": report,
        "predicted_needs": needs,
        "suggestions": suggestions_list,
        "fetched": fetched_count,
        "skipped_deleted": len(deleted_ids),
    }
