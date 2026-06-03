"""STEP 9 海报 API 测试。

不真实调用 DashScope；只验证：
1. POST /api/poster/generate 创建 DB 行 + 触发 apply_async（被 mock）
2. GET /api/poster/{id} 能读到刚创建的行
"""

from __future__ import annotations


def _register_and_login(client) -> str:
    client.post(
        "/api/auth/register",
        json={"email": "poster@example.com", "password": "Password123"},
    )
    r = client.post(
        "/api/auth/login",
        data={"username": "poster@example.com", "password": "Password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    return r.json()["access_token"]


def test_poster_generate_creates_row_and_enqueues(client, monkeypatch):
    import app.api.poster as poster_module

    calls: list[tuple[str, dict]] = []

    def fake_apply_async(args=None, task_id=None, **_kwargs):
        calls.append((task_id, {"args": args}))

    monkeypatch.setattr(
        poster_module.generate_poster_task,
        "apply_async",
        fake_apply_async,
    )

    token = _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post(
        "/api/poster/generate",
        json={"prompt": "夏日清凉饮料海报，蓝色背景"},
        headers=headers,
    )
    assert r.status_code == 202
    data = r.json()
    assert data["status"] == "pending"
    assert data["prompt"].startswith("夏日清凉")
    assert data["image_url"] is None
    poster_id = data["id"]

    # apply_async 被调用一次，task_id 与 poster_id 一致
    assert len(calls) == 1
    assert calls[0][0] == poster_id
    assert calls[0][1]["args"] == [poster_id]

    # GET 能读到
    r2 = client.get(f"/api/poster/{poster_id}", headers=headers)
    assert r2.status_code == 200
    assert r2.json()["id"] == poster_id


def test_poster_get_not_found(client, monkeypatch):
    import app.api.poster as poster_module

    monkeypatch.setattr(
        poster_module.generate_poster_task,
        "apply_async",
        lambda *a, **kw: None,
    )

    token = _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    r = client.get("/api/poster/does-not-exist", headers=headers)
    assert r.status_code == 404
