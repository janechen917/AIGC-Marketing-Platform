def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "AIGC Marketing Platform"
    assert data["docs"] == "/docs"


def test_health_ok_with_monkeypatch(client, monkeypatch):
    import app.main as main_module

    class _ConnCtx:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def execute(self, _sql):
            return 1

    class _FakeEngine:
        def connect(self):
            return _ConnCtx()

    class _FakeRedis:
        def ping(self):
            return True

    monkeypatch.setattr(main_module, "engine", _FakeEngine())
    monkeypatch.setattr(main_module.redis, "from_url", lambda _url: _FakeRedis())

    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["api"] == "ok"
    assert data["postgres"] == "ok"
    assert data["redis"] == "ok"
