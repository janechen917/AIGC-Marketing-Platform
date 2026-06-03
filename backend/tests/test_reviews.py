def _register_and_login(client, email: str = "review@example.com", password: str = "Password123") -> str:
    r1 = client.post("/api/auth/register", json={"email": email, "password": password})
    assert r1.status_code == 201

    r2 = client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r2.status_code == 200
    return r2.json()["access_token"]


def test_reviews_generate_success(client, monkeypatch):
    import app.api.reviews as reviews_api
    from app.schemas.reviews import ReviewsGenerateResponse

    def _fake_generate_reviews(*, req, db, user_id):
        return ReviewsGenerateResponse(
            reviews=["好喝不腻，已经回购", "通勤带一杯很方便"],
            total_generated=2,
            rounds=1,
            deduped_dropped=0,
            compliance_dropped=0,
            csv_content="index,review\n1,好喝不腻，已经回购\n2,通勤带一杯很方便\n",
        )

    monkeypatch.setattr(reviews_api, "generate_reviews", _fake_generate_reviews)

    token = _register_and_login(client)
    payload = {
        "product_name": "品牌A咖啡",
        "selling_points": ["低糖", "高香气"],
        "platform": "小红书",
        "target_count": 10,
    }

    resp = client.post(
        "/api/reviews/generate",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_generated"] == 2
    assert len(data["reviews"]) == 2
    assert data["compliance_dropped"] == 0
    assert "csv_content" in data


def test_reviews_generate_unauthorized(client):
    payload = {
        "product_name": "品牌A咖啡",
        "selling_points": ["低糖", "高香气"],
        "platform": "小红书",
    }
    resp = client.post("/api/reviews/generate", json=payload)
    assert resp.status_code == 401


def test_reviews_generate_missing_required_field(client):
    token = _register_and_login(client, email="review2@example.com")
    payload = {
        "selling_points": ["低糖", "高香气"],
        "platform": "小红书",
    }

    resp = client.post(
        "/api/reviews/generate",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


def test_reviews_generate_invalid_ranges(client):
    token = _register_and_login(client, email="review3@example.com")

    payload = {
        "product_name": "品牌A咖啡",
        "selling_points": ["低糖"],
        "platform": "小红书",
        "target_count": 0,
        "batch_size": 21,
        "max_rounds": 0,
        "similarity_threshold": 0.1,
    }
    resp = client.post(
        "/api/reviews/generate",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


def test_reviews_generate_minimal_payload_defaults(client, monkeypatch):
    import app.api.reviews as reviews_api
    from app.schemas.reviews import ReviewsGenerateResponse

    captured = {}

    def _fake_generate_reviews(*, req, db, user_id):
        captured["style"] = req.style
        captured["target_count"] = req.target_count
        captured["batch_size"] = req.batch_size
        captured["max_rounds"] = req.max_rounds
        captured["similarity_threshold"] = req.similarity_threshold
        captured["persona_pool"] = req.persona_pool
        captured["require_hashtag"] = req.require_hashtag
        captured["require_cta"] = req.require_cta
        return ReviewsGenerateResponse(
            reviews=["样例"],
            total_generated=1,
            rounds=1,
            deduped_dropped=0,
            compliance_dropped=0,
            csv_content="index,review\n1,样例\n",
        )

    monkeypatch.setattr(reviews_api, "generate_reviews", _fake_generate_reviews)

    token = _register_and_login(client, email="review4@example.com")
    payload = {
        "product_name": " 品牌A咖啡 ",
        "selling_points": [" 低糖 ", ""],
        "platform": " 小红书 ",
    }

    resp = client.post(
        "/api/reviews/generate",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert captured["style"] == "真实口碑"
    assert captured["target_count"] == 50
    assert captured["batch_size"] == 8
    assert captured["max_rounds"] == 20
    assert captured["similarity_threshold"] == 0.85
    assert captured["persona_pool"]
    assert captured["require_hashtag"] is False
    assert captured["require_cta"] is False
