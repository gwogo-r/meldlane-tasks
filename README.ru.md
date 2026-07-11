# meldlane-tasks

[English version](README.md)

![Python](https://img.shields.io/badge/python-3.11%2B-blue) ![License](https://img.shields.io/badge/license-MIT-green)

Пуш задач в [Plane](https://plane.so) программно, без повторного решения проблемы, в которую все упираются первой: **как синхронизировать одну и ту же задачу дважды, не наплодив дублей issue?** `PlaneSink` отвечает на это стабильным `external_id`, полученным из id самой задачи — повторный push обновляет существующий issue вместо создания нового. Проверено вживую на реальном инстансе Plane: 13 задач запушены дважды, issues по-прежнему 13.

`MarkdownSink` и `SqliteSink` — лёгкие destination'ы без внешних зависимостей для той же `Task`, полезны, если нужна локальная запись до (или вместо) синка в Plane — через тот же интерфейс `push()`/`list()`.

Библиотека, не сервис — без сервера, без конфиг-файла, только функции.

## Зачем

- **Идемпотентный синк в Plane, сделанный один раз.** `external_id`/`external_source` + обработка 409-на-дубль через PATCH — несколько строк, которые легко сделать неправильно с первого раза. Здесь они уже сделаны верно и проверены на живом инстансе — не нужно набивать ту же шишку самому.
- **Меняй хранилище, не трогая места вызова.** Одна и та же `Task`, тот же `push()`/`list()`, попадает ли она в markdown-файл, SQLite или Plane.
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
