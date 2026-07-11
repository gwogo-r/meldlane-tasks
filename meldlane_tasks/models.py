"""Task — контракт между meldlane-tasks и вызывающим сервисом. Не ломать:
источники задач (митинги, фидбек) и сервисы-потребители (агенты, дашборд)
полагаются на эту форму."""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    awaiting_confirm = "awaiting_confirm"
    testing = "testing"
    done = "done"
    blocked = "blocked"


class TaskSource(str, Enum):
    meeting = "meeting"
    feedback = "feedback"
    manual = "manual"


class Task(BaseModel):
    id: str
    title: str
    description: str = ""
    assignee_id: str | None = None  # id участника (человек или агент) — единая модель
    assignee_hint: str | None = None  # как назначение прозвучало в источнике (транскрипт и т.п.)
    status: TaskStatus = TaskStatus.todo
    story_points: float | None = None
    source: TaskSource = TaskSource.meeting
    source_ref: str | None = None  # meeting_id / feedback_id
    evidence_quote: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
