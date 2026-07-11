import pytest

from meldlane_tasks import SqliteSink, Task, TaskStatus


@pytest.mark.asyncio
async def test_push_then_list_roundtrips(tmp_path):
    sink = SqliteSink(tmp_path / "tasks.db")
    task = Task(id="t1", title="Write tests", story_points=3)

    await sink.push(task)
    tasks = await sink.list()

    assert len(tasks) == 1
    assert tasks[0].id == "t1"
    assert tasks[0].title == "Write tests"
    assert tasks[0].story_points == 3


@pytest.mark.asyncio
async def test_push_upserts_not_duplicates(tmp_path):
    sink = SqliteSink(tmp_path / "tasks.db")
    task = Task(id="t1", title="Write tests")

    await sink.push(task)
    task.status = TaskStatus.done
    await sink.push(task)

    tasks = await sink.list()
    assert len(tasks) == 1
    assert tasks[0].status == TaskStatus.done


@pytest.mark.asyncio
async def test_list_on_missing_db_returns_empty(tmp_path):
    sink = SqliteSink(tmp_path / "nope.db")
    assert await sink.list() == []
