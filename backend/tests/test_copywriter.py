import pytest


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


def test_copy_generate_missing_required_field(client):
    token = _register_and_login(client, email="copy2@example.com")
    payload = {
        "selling_points": ["低糖", "高香气"],
        "target_audience": "上班族",
        "platform": "小红书",
    }

    resp = client.post(
        "/api/copy/generate",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert any(item.get("loc") == ["body", "product_name"] for item in detail)


def test_copy_generate_empty_values_validation(client):
    token = _register_and_login(client, email="copy3@example.com")
    payload = {
        "product_name": "",
        "selling_points": [],
        "target_audience": "上班族",
        "platform": "小红书",
    }

    resp = client.post(
        "/api/copy/generate",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


def test_copy_generate_title_count_out_of_range(client):
    token = _register_and_login(client, email="copy4@example.com")

    for bad_count in [0, 9]:
        payload = {
            "product_name": "品牌A咖啡",
            "selling_points": ["低糖", "高香气"],
            "target_audience": "上班族",
            "platform": "小红书",
            "title_count": bad_count,
        }
        resp = client.post(
            "/api/copy/generate",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422


def test_copy_generate_minimal_payload_uses_defaults(client, monkeypatch):
    import app.api.copywriter as copy_api
    from app.schemas.compliance import ComplianceCheckResponse
    from app.schemas.copywriter import CopyGenerateResponse

    captured_req = {}

    def _fake_generate_copy(*, req, db, user_id):
        captured_req["style"] = req.style
        captured_req["length_hint"] = req.length_hint
        captured_req["title_count"] = req.title_count
        captured_req["require_hashtag"] = req.require_hashtag
        captured_req["require_cta"] = req.require_cta
        captured_req["max_emojis"] = req.max_emojis
        return CopyGenerateResponse(
            draft_text="初稿",
            polished_text="润色稿 #新品 立即咨询",
            draft_model="deepseek-v4",
            polish_model="qwen-plus",
            compliance=ComplianceCheckResponse(passed=True, issue_count=0, issues=[]),
        )

    monkeypatch.setattr(copy_api, "generate_copy", _fake_generate_copy)

    token = _register_and_login(client, email="copy5@example.com")
    payload = {
        "product_name": "品牌A咖啡",
        "selling_points": ["低糖"],
        "target_audience": "上班族",
        "platform": "小红书",
    }

    resp = client.post(
        "/api/copy/generate",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert captured_req["style"] == "专业"
    assert captured_req["length_hint"] == "中等"
    assert captured_req["title_count"] == 3
    assert captured_req["require_hashtag"] is True
    assert captured_req["require_cta"] is True
    assert captured_req["max_emojis"] == 6


@pytest.mark.parametrize(
    "email,payload",
    [
        (
            "copy6@example.com",
            {
                "product_name": "品牌A咖啡液",
                "selling_points": ["低糖", "冷萃香气", "便携即饮"],
                "target_audience": "通勤上班族",
                "platform": "小红书",
                "style": "专业",
                "length_hint": "中等",
                "title_count": 3,
                "brand_name": "品牌A",
            },
        ),
        (
            "copy7@example.com",
            {
                "product_name": "品牌B防晒喷雾",
                "selling_points": ["清爽不黏", "快速成膜"],
                "target_audience": "户外通勤人群",
                "platform": "微博",
                "style": "活泼",
                "length_hint": "短",
                "title_count": 2,
                "brand_name": "品牌B",
                "require_hashtag": True,
                "require_cta": True,
            },
        ),
        (
            "copy8@example.com",
            {
                "product_name": "品牌C空气炸锅",
                "selling_points": ["大容量", "少油健康", "多菜单"],
                "target_audience": "家庭用户",
                "platform": "公众号",
                "style": "专业",
                "length_hint": "长",
                "title_count": 4,
                "brand_name": "品牌C",
                "max_length": 1200,
                "max_emojis": 3,
            },
        ),
    ],
)
def test_copy_generate_acceptance_samples_structure(client, monkeypatch, email, payload):
    import app.api.copywriter as copy_api
    from app.schemas.compliance import ComplianceCheckResponse
    from app.schemas.copywriter import CopyGenerateResponse

    def _fake_generate_copy(*, req, db, user_id):
        return CopyGenerateResponse(
            draft_text=f"初稿-{req.product_name}",
            polished_text=f"润色稿-{req.platform}",
            draft_model="deepseek-v4",
            polish_model="qwen-plus",
            compliance=ComplianceCheckResponse(passed=True, issue_count=0, issues=[]),
        )

    monkeypatch.setattr(copy_api, "generate_copy", _fake_generate_copy)

    token = _register_and_login(client, email=email)
    resp = client.post(
        "/api/copy/generate",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200
    data = resp.json()
    for key in ["draft_text", "polished_text", "draft_model", "polish_model", "compliance"]:
        assert key in data
    assert isinstance(data["draft_text"], str) and data["draft_text"]
    assert isinstance(data["polished_text"], str) and data["polished_text"]
    assert isinstance(data["draft_model"], str) and data["draft_model"]
    assert isinstance(data["polish_model"], str) and data["polish_model"]
    assert isinstance(data["compliance"], dict)
    for key in ["passed", "issue_count", "issues"]:
        assert key in data["compliance"]
