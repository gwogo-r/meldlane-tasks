import pytest

from meldlane_tasks import MarkdownSink, Task, TaskStatus


@pytest.mark.asyncio
async def test_push_creates_new_row(tmp_path):
    sink = MarkdownSink(tmp_path / "backlog.md")
    task = Task(id="MEL-100", title="Do the thing")

    await sink.push(task, assignee_name="Roman")

    content = (tmp_path / "backlog.md").read_text(encoding="utf-8")
    assert "MEL-100" in content
    assert "Do the thing" in content
    assert "Roman" in content


@pytest.mark.asyncio
async def test_push_updates_existing_row_not_duplicate(tmp_path):
    sink = MarkdownSink(tmp_path / "backlog.md")
    task = Task(id="MEL-100", title="Do the thing")

    await sink.push(task)
    task.status = TaskStatus.done
    await sink.push(task)

    content = (tmp_path / "backlog.md").read_text(encoding="utf-8")
    assert content.count("MEL-100") == 1
    assert "DONE" in content


@pytest.mark.asyncio
async def test_list_reads_back_id_title_status(tmp_path):
    sink = MarkdownSink(tmp_path / "backlog.md")
    await sink.push(Task(id="MEL-1", title="First", status=TaskStatus.done))
    await sink.push(Task(id="MEL-2", title="Second"))

    tasks = await sink.list()

    by_id = {t.id: t for t in tasks}
    assert by_id["MEL-1"].status == TaskStatus.done
    assert by_id["MEL-2"].status == TaskStatus.todo


@pytest.mark.asyncio
async def test_list_on_missing_file_returns_empty(tmp_path):
    sink = MarkdownSink(tmp_path / "nope.md")
    assert await sink.list() == []
