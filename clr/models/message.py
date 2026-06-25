from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class MessageCategory(str, Enum):
    notification = "notification"
    email = "email"
    task = "task"
    decision = "decision"
    information = "information"


class IncomingMessage(BaseModel):
    id: str = Field(..., description="Unique identifier for the message")
    source: str = Field(..., description="Where the message came from (app, person, service)")
    content: str = Field(..., description="Raw message content")
    category: MessageCategory = MessageCategory.information
    received_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)


class ProcessedMessage(BaseModel):
    original: IncomingMessage
    summary: str = ""
    simplified: str = ""
    priority: Priority = Priority.medium
    action_required: bool = False
    suggested_action: str = ""
    filtered_out: bool = False
    filter_reason: str = ""
    cognitive_cost: int = Field(0, ge=0, le=10, description="Estimated cognitive load units (0–10)")