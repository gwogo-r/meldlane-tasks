"""PlaneSink — синк Task -> issue в Plane (self-hosted или cloud).

Честная граница: Plane ожидает assignee = реальный аккаунт пользователя
workspace'а. Агенты (не-человеческие участники) обычно таких аккаунтов не
имеют — "агент как equal assignee" в Plane не реализовано этим sink'ом,
это открытый вопрос на стороне Plane. Имя исполнителя, SP и источник кладём
в описание issue текстом, не в нативные поля.

Идемпотентность: external_id (хэш от task.id) + external_source, 409 на
дубль означает "уже есть", тогда PATCH существующей задачи вместо создания
новой. Проверено вживую (Meldlane, 2026-07-11): 13 задач, повторный push
не создаёт дублей.
"""
import hashlib
import html

import httpx

from ..models import Task
from .base import TaskSink

EXTERNAL_SOURCE = "meldlane-tasks"


def _external_id(task: Task) -> str:
    return hashlib.sha256(task.id.encode()).hexdigest()[:32]


def _description(task: Task, assignee_name: str | None) -> str:
    esc = html.escape
    parts = [f"<p>{esc(task.description)}</p>" if task.description else ""]

    meta = [f"<strong>Источник:</strong> {esc(task.source.value)}"]
    if assignee_name:
        meta.append(f"<strong>Назначено:</strong> {esc(assignee_name)}")
    if task.story_points:
        meta.append(f"<strong>Story points:</strong> {task.story_points}")
    parts.append("<p>" + " · ".join(meta) + "</p>")

    if task.evidence_quote:
        parts.append(f"<blockquote>{esc(task.evidence_quote)}</blockquote>")
    return "".join(parts)


class PlaneSink(TaskSink):
    def __init__(self, base_url: str, api_token: str, workspace: str, project_id: str):
        if not (base_url and api_token and workspace and project_id):
            raise ValueError("PlaneSink: base_url, api_token, workspace и project_id обязательны")
        self.base_url = base_url.rstrip("/")
        self.workspace = workspace
        self.project_id = project_id
        self.headers = {"x-api-key": api_token, "Content-Type": "application/json"}

    def _issues_url(self, issue_id: str = "") -> str:
        base = f"{self.base_url}/api/v1/workspaces/{self.workspace}/projects/{self.project_id}/issues/"
        return f"{base}{issue_id}/" if issue_id else base

    async def push(self, task: Task, assignee_name: str | None = None) -> str:
        external_id = _external_id(task)
        payload = {
            "name": task.title[:255],
            "description_html": _description(task, assignee_name or task.assignee_hint),
            "external_id": external_id,
            "external_source": EXTERNAL_SOURCE,
        }

        async with httpx.AsyncClient(headers=self.headers, timeout=20) as client:
            resp = await client.post(self._issues_url(), json=payload)
            if resp.status_code == 409:
                existing_id = resp.json()["id"]
                resp = await client.patch(self._issues_url(existing_id), json=payload)
            if resp.status_code not in (200, 201):
                resp.raise_for_status()
            data = resp.json()
        return data["id"]

    async def list(self) -> list[Task]:
        """Возвращает issues этого проекта, созданные этим sink'ом (по external_source).
        Обратное преобразование неполное: Plane не хранит story_points/source в
        структурированном виде для наших задач — только title и статус."""
        async with httpx.AsyncClient(headers=self.headers, timeout=20) as client:
            resp = await client.get(self._issues_url())
            resp.raise_for_status()
            data = resp.json()
        items = data.get("results", data) if isinstance(data, dict) else data
        return [
            Task(id=i["id"], title=i["name"])
            for i in items
            if i.get("external_source") == EXTERNAL_SOURCE
        ]
