from dataclasses import dataclass


@dataclass
class _FakeAsyncTask:
    id: str
    state: str


def test_enqueue_endpoints(client, monkeypatch):
    import app.api.tasks as tasks_module

    class _PingTask:
        @staticmethod
        def delay():
            return _FakeAsyncTask(id="ping-task-id", state="PENDING")

    class _PosterTask:
        @staticmethod
        def delay(_payload):
            return _FakeAsyncTask(id="poster-task-id", state="PENDING")

    class _VideoTask:
        @staticmethod
        def delay(_payload):
            return _FakeAsyncTask(id="video-task-id", state="PENDING")

    monkeypatch.setattr(tasks_module, "ping_task", _PingTask())
    monkeypatch.setattr(tasks_module, "generate_poster_task", _PosterTask())
    monkeypatch.setattr(tasks_module, "generate_video_task", _VideoTask())

    r1 = client.post("/api/tasks/ping")
    assert r1.status_code == 202
    assert r1.json()["task_id"] == "ping-task-id"

    r2 = client.post("/api/tasks/poster-demo")
    assert r2.status_code == 202
    assert r2.json()["task_id"] == "poster-task-id"

    r3 = client.post("/api/tasks/video-demo")
    assert r3.status_code == 202
    assert r3.json()["task_id"] == "video-task-id"


def test_get_task_status_ready_success(client, monkeypatch):
    import app.api.tasks as tasks_module

    class _Result:
        state = "SUCCESS"
        result = {"message": "pong"}

        @staticmethod
        def ready():
            return True

        @staticmethod
        def successful():
            return True

    monkeypatch.setattr(tasks_module, "AsyncResult", lambda _id, app=None: _Result())

    resp = client.get("/api/tasks/abc")
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "SUCCESS"
    assert data["ready"] is True
    assert data["successful"] is True
    assert data["result"] == {"message": "pong"}
