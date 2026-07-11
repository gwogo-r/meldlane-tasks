# meldlane-tasks

[Русская версия](README.ru.md)

![Python](https://img.shields.io/badge/python-3.11%2B-blue) ![License](https://img.shields.io/badge/license-MIT-green)

Push tasks into [Plane](https://plane.so) programmatically without re-solving the same problem everyone hits first: **how do you sync the same task twice without creating a duplicate issue?** `PlaneSink` answers that with a stable `external_id` derived from your task's own id — push it again and it updates the existing issue instead. Verified live against a real Plane instance: 13 tasks pushed twice, still 13 issues.

`MarkdownSink` and `SqliteSink` are included as lightweight, no-dependency destinations for the same `Task` — useful if you want a local record before (or instead of) syncing to Plane, behind the same `push()`/`list()` interface.

A library, not a service — no server, no config file, just functions.

## Why

- **The idempotent Plane sync, done once.** `external_id`/`external_source` + handling Plane's 409-on-duplicate by PATCHing instead — a few lines that are easy to get subtly wrong the first time you write them. This library got them right and tested against a live instance, so you don't have to rediscover it.
- **Swap the backend without touching call sites.** Same `Task`, same `push()`/`list()`, whether it lands in a markdown file, SQLite, or Plane.
- **Honest about what it doesn't solve.** Plane expects an `assignee` to be a real workspace user account — this library doesn't fake agent-as-assignee support. Assignee name, story points and source go into the issue description as text instead of a native field.

## Install

```bash
pip install meldlane-tasks
```

Python 3.11+.

## Usage

```python
from meldlane_tasks import Task, MarkdownSink, SqliteSink, PlaneSink

task = Task(id="MEL-100", title="Fix the login bug", story_points=3)

# same task, three destinations
await MarkdownSink("backlog.md").push(task, assignee_name="Roman")
await SqliteSink("tasks.db").push(task)
await PlaneSink(
    base_url="http://localhost:8090", api_token="...",
    workspace="my-workspace", project_id="...",
).push(task, assignee_name="Roman")
```

## The Task contract

```python
class Task(BaseModel):
    id: str
    title: str
    description: str = ""
    assignee_id: str | None = None
    assignee_hint: str | None = None
    status: TaskStatus = TaskStatus.todo   # todo/in_progress/awaiting_confirm/testing/done/blocked
    story_points: float | None = None
    source: TaskSource = TaskSource.meeting  # meeting/feedback/manual
    source_ref: str | None = None
    evidence_quote: str = ""
    created_at: datetime
```

`push()` returns a sink-specific external id (task id for markdown/SQLite, issue UUID for Plane) — it's intentionally not stored on `Task` itself, so one task can be synced to several sinks at once without the id fields colliding.

## Sinks

| Sink | Backend | Notes |
|---|---|---|
| `MarkdownSink` | a markdown file | Writes/updates a `\| ID \| Title \| Priority \| Status \| Area \| Notes \|` table row. Human-readable, not a full round-trip (description/story_points aren't recovered by `list()`). |
| `SqliteSink` | local SQLite file | Full round-trip — every `Task` field survives `push()` → `list()`. |
| `PlaneSink` | [Plane](https://plane.so) (self-hosted or cloud) REST API | Idempotent via `external_id`/`external_source`. `list()` only returns issues created by this library (filtered by `external_source`). |

Jira and YouTrack adapters aren't included — writing an integration against an API you can't test live against a real instance produces code nobody should trust. The `TaskSink` interface is stable enough to add them later without breaking existing sinks.

## License

MIT
