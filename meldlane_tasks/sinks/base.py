"""TaskSink — единый интерфейс для мест, куда попадают задачи (файл, БД, трекер).

Каждый sink реализует push()/list() для своего хранилища; вызывающая сторона
не знает и не должна знать, markdown это, SQLite или Plane. push() возвращает
внешний id (для markdown/SQLite — обычно совпадает с task.id, для Plane —
UUID issue) — id sink-специфичен и намеренно не хранится в самой модели Task,
чтобы одна задача могла быть синхронизирована в несколько sink'ов одновременно
без конфликта полей.
"""
from abc import ABC, abstractmethod

from ..models import Task


class TaskSink(ABC):
    @abstractmethod
    async def push(self, task: Task, assignee_name: str | None = None) -> str:
        """Создаёт или обновляет задачу в хранилище. Возвращает внешний id."""

    @abstractmethod
    async def list(self) -> list[Task]:
        """Возвращает все задачи из хранилища."""
