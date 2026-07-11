# meldlane-tasks

[English version](README.md)

![Python](https://img.shields.io/badge/python-3.11%2B-blue) ![License](https://img.shields.io/badge/license-MIT-green)

Одна модель `Task`, три места, где она может жить: markdown-таблица, локальный SQLite-файл или проект в Plane — всё через один и тот же интерфейс `push()`/`list()`, так что твоему коду не нужно знать, куда именно попадает задача.

Библиотека, не сервис — без сервера, без конфиг-файла, только функции.

## Зачем

- **Меняй хранилище, не трогая места вызова.** Начни с markdown-файла, перейди на SQLite, синхронизируй в Plane позже — вызывающий код остаётся `await sink.push(task)`.
- **Идемпотентность по конструкции.** `PlaneSink` использует стабильный `external_id`, полученный из id задачи; повторный push той же задачи обновляет её, а не плодит дубль. Проверено вживую: 13 задач запушены дважды, issues по-прежнему 13.
- **Честность про то, что не решено.** Plane ожидает, что `assignee` — реальный аккаунт пользователя workspace'а — библиотека не изображает поддержку «агент как assignee». Имя исполнителя, story points и источник идут в описание issue текстом, не в нативное поле.

## Установка

```bash
pip install meldlane-tasks
```

Python 3.11+.

## Использование

```python
from meldlane_tasks import Task, MarkdownSink, SqliteSink, PlaneSink

task = Task(id="MEL-100", title="Починить баг логина", story_points=3)

# одна задача, три назначения
await MarkdownSink("backlog.md").push(task, assignee_name="Roman")
await SqliteSink("tasks.db").push(task)
await PlaneSink(
    base_url="http://localhost:8090", api_token="...",
    workspace="my-workspace", project_id="...",
).push(task, assignee_name="Roman")
```

## Контракт Task

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

`push()` возвращает специфичный для sink'а внешний id (id задачи для markdown/SQLite, UUID issue для Plane) — он намеренно не хранится в самой `Task`, чтобы одну задачу можно было синхронизировать сразу в несколько sink'ов без конфликта полей.

## Sinks

| Sink | Хранилище | Заметки |
|---|---|---|
| `MarkdownSink` | markdown-файл | Пишет/обновляет строку таблицы `\| ID \| Title \| Priority \| Status \| Area \| Notes \|`. Человекочитаемо, не полный round-trip (description/story_points не восстанавливаются через `list()`). |
| `SqliteSink` | локальный SQLite-файл | Полный round-trip — каждое поле `Task` переживает `push()` → `list()`. |
| `PlaneSink` | REST API [Plane](https://plane.so) (self-hosted или cloud) | Идемпотентно через `external_id`/`external_source`. `list()` возвращает только issues, созданные этой библиотекой (фильтр по `external_source`). |

Адаптеров Jira и YouTrack нет — писать интеграцию против API, который негде проверить на живом инстансе, значит писать код, которому нельзя доверять. Интерфейс `TaskSink` достаточно стабилен, чтобы добавить их позже, не сломав существующие sinks.

## Лицензия

MIT
