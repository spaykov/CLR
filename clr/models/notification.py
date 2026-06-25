from datetime import datetime
from pydantic import BaseModel, Field


class Notification(BaseModel):
    id: str
    app: str
    title: str
    body: str
    received_at: datetime = Field(default_factory=datetime.utcnow)
    is_urgent: bool = False


class FilteredNotification(BaseModel):
    original: Notification
    kept: bool
    reason: str
    simplified_title: str = ""
    simplified_body: str = ""