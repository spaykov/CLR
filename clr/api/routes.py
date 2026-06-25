from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from clr.models.message import IncomingMessage, ProcessedMessage
from clr.models.notification import Notification
from clr.models.task import DecisionTask
from clr.core import filter, rewriter, summarizer, predictor, decision_handler, bandwidth_score, advisor

router = APIRouter(prefix="/api/v1")


# --- Request/response schemas ---

class ProcessRequest(BaseModel):
    message: IncomingMessage

class BatchProcessRequest(BaseModel):
    messages: list[IncomingMessage]

class RewriteRequest(BaseModel):
    text: str

class SummarizeRequest(BaseModel):
    text: str

class NotificationFilterRequest(BaseModel):
    notification: Notification

class DecisionRequest(BaseModel):
    task: DecisionTask

class EmailFetchRequest(BaseModel):
    limit: int = 10


# --- Endpoints ---

@router.post("/process", response_model=ProcessedMessage)
def process_message(req: ProcessRequest):
    """Filter, summarize, and rewrite a single incoming message."""
    processed = filter.filter_message(req.message)
    processed = summarizer.summarize(processed)
    processed = rewriter.rewrite(processed)
    return processed


@router.post("/process/batch")
def process_batch(req: BatchProcessRequest):
    """Process multiple messages and return bandwidth report."""
    results = []
    for msg in req.messages:
        p = filter.filter_message(msg)
        p = summarizer.summarize(p)
        p = rewriter.rewrite(p)
        results.append(p)

    report = bandwidth_score.bandwidth_report(results)
    suggestions = advisor.suggest_reductions(results, report["score"])
    needs = predictor.predict_needs(req.messages)

    return {
        "processed": results,
        "bandwidth": report,
        "predicted_needs": needs,
        "suggestions": suggestions,
    }


@router.post("/rewrite")
def rewrite_text(req: RewriteRequest):
    return {"result": rewriter.rewrite_raw(req.text)}


@router.post("/summarize")
def summarize_text(req: SummarizeRequest):
    return {"result": summarizer.summarize_raw(req.text)}


@router.post("/filter/notification")
def filter_notification(req: NotificationFilterRequest):
    return filter.filter_notification(req.notification)


@router.post("/decide")
def decide(req: DecisionRequest):
    return decision_handler.handle_decision(req.task)


@router.post("/email/fetch")
def fetch_email(req: EmailFetchRequest):
    """Fetch recent Gmail emails and run them through the batch pipeline."""
    from clr.core import email_fetcher
    try:
        messages = email_fetcher.fetch_emails(req.limit)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email fetch failed: {e}")

    if not messages:
        return {
            "processed": [],
            "bandwidth": {"score": 100, "label": "clear", "active_items": 0, "filtered_items": 0, "high_cost_items": []},
            "predicted_needs": [],
            "suggestions": [],
            "fetched": 0,
        }

    results = []
    for msg in messages:
        p = filter.filter_message(msg)
        p = summarizer.summarize(p)
        p = rewriter.rewrite(p)
        results.append(p)

    report = bandwidth_score.bandwidth_report(results)
    suggestions_list = advisor.suggest_reductions(results, report["score"])
    needs = predictor.predict_needs(messages)

    return {
        "processed": results,
        "bandwidth": report,
        "predicted_needs": needs,
        "suggestions": suggestions_list,
        "fetched": len(messages),
    }


@router.get("/email/status")
def email_status():
    from clr.core import email_fetcher
    return {"configured": email_fetcher.has_credentials()}


@router.get("/health")
def health():
    return {"status": "ok"}