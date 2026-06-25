from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class TaskComplexity(str, Enum):
    trivial = "trivial"
    simple = "simple"
    moderate = "moderate"
    complex = "complex"


class Task(BaseModel):
    id: str
    title: str
    description: str = ""
    due_at: datetime | None = None
    complexity: TaskComplexity = TaskComplexity.simple
    cognitive_cost: int = Field(0, ge=0, le=10)


class DecisionTask(BaseModel):
    id: str
    question: str
    options: list[str]
    context: str = ""
    auto_decided: bool = False
    decision: str = ""
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    reasoning: str = ""