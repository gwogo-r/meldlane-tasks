"""SqliteSink — минимальное хранилище задач в SQLite. Независимо от
storage-слоя сервиса, который его использует (тот обычно шире — там ещё
участники, встречи и т.п.); этот sink знает только про Task."""
from pathlib import Path

import aiosqlite

from ..models import Task
from .base import TaskSink

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    data TEXT NOT NULL
);
"""


class SqliteSink(TaskSink):
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)

    async def _ensure_schema(self, db: aiosqlite.Connection) -> None:
        await db.executescript(_SCHEMA)
        await db.commit()

    async def push(self, task: Task, assignee_name: str | None = None) -> str:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            await self._ensure_schema(db)
            await db.execute(
                "INSERT INTO tasks (id, data) VALUES (?, ?) "
                "ON CONFLICT(id) DO UPDATE SET data=excluded.data",
                (task.id, task.model_dump_json()),
            )
            await db.commit()
        return task.id

    async def list(self) -> list[Task]:
        if not self.db_path.exists():
            return []
        async with aiosqlite.connect(self.db_path) as db:
            await self._ensure_schema(db)
            rows = await db.execute_fetchall("SELECT data FROM tasks")
        return [Task.model_validate_json(row[0]) for row in rows]
