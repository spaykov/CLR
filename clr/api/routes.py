import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field

from clr.api.auth import SESSION_COOKIE_NAME, require_api_key
from clr.api.rate_limit import rate_limited
from clr.config import settings
from clr.models.message import IncomingMessage, ProcessedMessage
from clr.models.notification import Notification
from clr.models.task import DecisionTask
from clr.core import filter, rewriter, summarizer, predictor, decision_handler, bandwidth_score, advisor, storage, sessions

# /health is intentionally excluded from require_api_key so monitoring/load
# balancers can probe liveness without a key. A default per-client rate limit
# applies to every other /api/v1/* route; the expensive ones (LLM/Gmail-
# backed) get a tighter limit added on top via the route's own dependencies.
router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_api_key), Depends(rate_limited(60, 60))])
public_router = APIRouter(prefix="/api/v1")

# Set once at import time; changes whenever uvicorn --reload restarts the
# worker process, so the UI can prove it's talking to a freshly loaded backend.
STARTED_AT = datetime.now(timezone.utc)


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
    hours: int = Field(24, ge=1, le=168)

class SenderRuleRequest(BaseModel):
    pattern: str = Field(..., min_length=1)
    action: str = Field(..., pattern="^(ignore|digest)$")

class LoginRequest(BaseModel):
    password: str


# --- Endpoints ---

@router.post("/process", response_model=ProcessedMessage)
def process_message(req: ProcessRequest):
    """Filter, summarize, and rewrite a single incoming message."""
    processed = filter.filter_message(req.message)
    processed = summarizer.summarize(processed)
    processed = rewriter.rewrite(processed)
    return processed


@router.post("/process/batch", dependencies=[Depends(rate_limited(10, 60))])
def process_batch(req: BatchProcessRequest):
    """Process multiple messages and return bandwidth report."""
    results = []
    for msg in req.messages:
        p = filter.filter_message(msg)
        p = summarizer.summarize(p)
        p = rewriter.rewrite(p)
        storage.save_processed(p)
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


@router.post("/email/fetch", dependencies=[Depends(rate_limited(5, 300))])
def fetch_email(req: EmailFetchRequest):
    """Fetch Gmail emails from the last N hours and run them through the batch pipeline."""
    from clr.core import email_fetcher
    try:
        messages = email_fetcher.fetch_emails(hours=req.hours)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email fetch failed: {e}")

    fetched_count = len(messages)
    deleted_ids = storage.get_deleted_ids([m.id for m in messages])
    messages = [m for m in messages if m.id not in deleted_ids]

    if not messages:
        return {
            "processed": [],
            "bandwidth": {"score": 100, "label": "clear", "active_items": 0, "filtered_items": 0, "high_cost_items": []},
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


@router.get("/email/status")
def email_status():
    from clr.core import email_fetcher
    return {"configured": email_fetcher.has_credentials()}


@public_router.get("/health")
def health():
    return {"status": "ok"}


@public_router.post("/auth/login", dependencies=[Depends(rate_limited(5, 300, by_ip=True))])
def login(req: LoginRequest, request: Request, response: Response):
    if not settings.login_password:
        raise HTTPException(status_code=400, detail="Login is not configured")
    if not secrets.compare_digest(req.password, settings.login_password):
        raise HTTPException(status_code=401, detail="Incorrect password")
    token = sessions.create_session()
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=request.url.scheme == "https",
        max_age=12 * 60 * 60,
        path="/",
    )
    return {"ok": True}


@public_router.post("/auth/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        sessions.destroy(token)
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return {"ok": True}


@public_router.get("/auth/status")
def auth_status(request: Request):
    if not settings.login_password:
        return {"auth_required": False, "authenticated": True}
    token = request.cookies.get(SESSION_COOKIE_NAME)
    return {"auth_required": True, "authenticated": bool(token and sessions.is_valid(token))}


@router.get("/version")
def version():
    return {"started_at": STARTED_AT.isoformat()}


@router.get("/history")
def history(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    return {"items": storage.get_history(limit=limit, offset=offset)}


@router.delete("/history/{message_id}")
def delete_history_item(message_id: str):
    if not storage.delete_processed(message_id):
        raise HTTPException(status_code=404, detail="Message not found")
    return {"ok": True}


@router.delete("/history")
def clear_all_history():
    return {"ok": True, "deleted": storage.clear_history()}


@router.get("/sender-rules")
def list_sender_rules():
    return {"items": storage.list_sender_rules()}


@router.post("/sender-rules")
def add_sender_rule(req: SenderRuleRequest):
    return storage.add_sender_rule(req.pattern, req.action)


@router.put("/sender-rules/{rule_id}")
def update_sender_rule(rule_id: int, req: SenderRuleRequest):
    if not storage.update_sender_rule(rule_id, req.pattern, req.action):
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"ok": True}


@router.delete("/sender-rules/{rule_id}")
def delete_sender_rule(rule_id: int):
    if not storage.delete_sender_rule(rule_id):
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"ok": True}