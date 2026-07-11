import httpx
import pytest

from meldlane_tasks import PlaneSink, Task


@pytest.mark.asyncio
async def test_push_creates_issue_on_success(monkeypatch):
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(201, json={"id": "issue-1"})

    transport = httpx.MockTransport(handler)
    real_client = httpx.AsyncClient

    def patched_client(*args, **kwargs):
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", patched_client)

    sink = PlaneSink(base_url="http://localhost:8090", api_token="tok", workspace="ws", project_id="proj")
    issue_id = await sink.push(Task(id="t1", title="Fix the bug"), assignee_name="Roman")

    assert issue_id == "issue-1"
    assert len(calls) == 1
    assert calls[0].method == "POST"


@pytest.mark.asyncio
async def test_push_patches_on_409_conflict(monkeypatch):
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.method == "POST":
            return httpx.Response(409, json={"id": "existing-issue"})
        return httpx.Response(200, json={"id": "existing-issue"})

    transport = httpx.MockTransport(handler)
    real_client = httpx.AsyncClient

    def patched_client(*args, **kwargs):
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", patched_client)

    sink = PlaneSink(base_url="http://localhost:8090", api_token="tok", workspace="ws", project_id="proj")
    issue_id = await sink.push(Task(id="t1", title="Fix the bug"))

    assert issue_id == "existing-issue"
    assert [c.method for c in calls] == ["POST", "PATCH"]


def test_requires_all_config_values():
    with pytest.raises(ValueError):
        PlaneSink(base_url="", api_token="tok", workspace="ws", project_id="proj")
