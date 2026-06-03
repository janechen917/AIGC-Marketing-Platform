"""STEP 10 视频 API 测试（第一版）。"""

from __future__ import annotations

from app.models.video_task import VideoTask


def _register_and_login(client) -> str:
    client.post(
        "/api/auth/register",
        json={"email": "video@example.com", "password": "Password123"},
    )
    r = client.post(
        "/api/auth/login",
        data={"username": "video@example.com", "password": "Password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return r.json()["access_token"]


def test_video_start_creates_row_and_enqueues(client, monkeypatch):
    import app.api.video as video_module

    calls: list[tuple[tuple, dict]] = []

    def fake_apply_async(args=None, task_id=None, **_kwargs):
        calls.append((tuple(args or ()), {"task_id": task_id}))

    monkeypatch.setattr(video_module.generate_video_task, "apply_async", fake_apply_async)

    token = _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post(
        "/api/video/start",
        json={"prompt": "夏日饮料短视频", "shot_count": 3},
        headers=headers,
    )
    assert r.status_code == 202
    data = r.json()
    assert data["status"] == "pending"
    assert data["stage"] == "pending"
    assert len(calls) == 1
    assert calls[0][0][1] == "start"

    video_id = data["id"]
    r2 = client.get(f"/api/video/{video_id}", headers=headers)
    assert r2.status_code == 200
    assert r2.json()["id"] == video_id


def test_video_confirm_enqueues_next_stage(client, test_db, monkeypatch):
    import app.api.video as video_module

    calls: list[tuple] = []

    def fake_delay(video_id, action, payload):
        calls.append((video_id, action, payload))

    monkeypatch.setattr(video_module.generate_video_task, "delay", fake_delay)
    monkeypatch.setattr(
        video_module.generate_video_task,
        "apply_async",
        lambda *a, **kw: None,
    )

    token = _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    created = client.post(
        "/api/video/start",
        json={"prompt": "护肤品短视频", "shot_count": 2},
        headers=headers,
    )
    video_id = created.json()["id"]

    # 模拟第一阶段已完成，允许 confirm script
    row = test_db.get(VideoTask, video_id)
    assert row is not None
    row.stage = "script_done"
    row.status = "waiting_confirm"
    test_db.commit()

    r = client.post(
        "/api/video/confirm",
        json={"video_id": video_id, "stage": "script_done", "payload": {}},
        headers=headers,
    )
    assert r.status_code == 202
    assert len(calls) == 1
    assert calls[0][0] == video_id
    assert calls[0][1] == "confirm_script"
