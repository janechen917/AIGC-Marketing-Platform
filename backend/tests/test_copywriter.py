def _register_and_login(client, email: str = "copy@example.com", password: str = "Password123") -> str:
    r1 = client.post("/api/auth/register", json={"email": email, "password": password})
    assert r1.status_code == 201

    r2 = client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r2.status_code == 200
    return r2.json()["access_token"]


def test_copy_generate_success(client, monkeypatch):
    import app.api.copywriter as copy_api
    from app.schemas.compliance import ComplianceCheckResponse
    from app.schemas.copywriter import CopyGenerateResponse

    def _fake_generate_copy(*, req, db, user_id):
        return CopyGenerateResponse(
            draft_text="初稿",
            polished_text="润色稿 #新品 立即咨询",
            draft_model="deepseek-v4",
            polish_model="qwen-plus",
            compliance=ComplianceCheckResponse(passed=True, issue_count=0, issues=[]),
        )

    monkeypatch.setattr(copy_api, "generate_copy", _fake_generate_copy)

    token = _register_and_login(client)
    payload = {
        "product_name": "品牌A咖啡",
        "selling_points": ["低糖", "高香气"],
        "target_audience": "上班族",
        "platform": "小红书",
        "style": "专业",
        "length_hint": "中等",
        "title_count": 3,
        "brand_name": "品牌A",
    }

    resp = client.post(
        "/api/copy/generate",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["draft_model"] == "deepseek-v4"
    assert data["polish_model"] == "qwen-plus"
    assert data["compliance"]["passed"] is True


def test_copy_generate_unauthorized(client):
    payload = {
        "product_name": "品牌A咖啡",
        "selling_points": ["低糖", "高香气"],
        "target_audience": "上班族",
        "platform": "小红书",
    }
    resp = client.post("/api/copy/generate", json=payload)
    assert resp.status_code == 401
