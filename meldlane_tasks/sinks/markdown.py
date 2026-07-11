"""MarkdownSink — задачи как строки таблицы в markdown-файле, формат backlog.md
(| ID | Title | Priority | Status | Area | Notes |). Приоритет и Area не входят
в Task, поэтому Priority всегда P2, Area — "backend"; заполняются вручную
человеком после синка, если нужна точность.
"""
import re
from pathlib import Path

from ..models import Task, TaskStatus
from .base import TaskSink

_HEADER = "| ID | Title | Priority | Status | Area | Notes |\n|----|-------|----------|--------|------|-------|\n"
_ROW_RE = re.compile(r"^\|\s*([^\s|]+)\s*\|")

_STATUS_LABEL = {
    TaskStatus.todo: "TODO",
    TaskStatus.in_progress: "IN PROGRESS",
    TaskStatus.awaiting_confirm: "IN PROGRESS",
    TaskStatus.testing: "IN PROGRESS",
    TaskStatus.done: "DONE",
    TaskStatus.blocked: "BLOCKED",
}


def _row(task: Task, assignee_name: str | None) -> str:
    notes = task.description or task.evidence_quote or ""
    who = f" (-> {assignee_name})" if assignee_name else ""
    sp = f" [{task.story_points} SP]" if task.story_points else ""
    return f"| {task.id} | {task.title}{who}{sp} | P2 | {_STATUS_LABEL[task.status]} | backend | {notes} |\n"


class MarkdownSink(TaskSink):
    def __init__(self, path: str | Path):
        self.path = Path(path)

    async def push(self, task: Task, assignee_name: str | None = None) -> str:
        text = self.path.read_text(encoding="utf-8") if self.path.exists() else _HEADER
        lines = text.splitlines(keepends=True)

        new_row = _row(task, assignee_name)
        for i, line in enumerate(lines):
            m = _ROW_RE.match(line)
            if m and m.group(1) == task.id:
                lines[i] = new_row
                break
        else:
            if not lines:
                lines = [_HEADER]
            lines.append(new_row)

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("".join(lines), encoding="utf-8")
        return task.id

    async def list(self) -> list[Task]:
        """Читает id/title/status обратно. Остальные поля markdown не хранит
        полно (это человекочитаемый экспорт, не источник истины) — description
        пуст, source остаётся дефолтным."""
        if not self.path.exists():
            return []
        tasks = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            m = _ROW_RE.match(line)
            if not m or m.group(1) in ("ID", "----"):
                continue
            cols = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cols) < 4:
                continue
            task_id, title, _priority, status_label = cols[0], cols[1], cols[2], cols[3]
            status = next((s for s, label in _STATUS_LABEL.items() if label == status_label), TaskStatus.todo)
            tasks.append(Task(id=task_id, title=title, status=status))
        return tasks
