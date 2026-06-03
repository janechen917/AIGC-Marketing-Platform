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
            csv_content="review\n好喝不腻，已经回购\n通勤带一杯很方便\n",
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
    assert "csv_content" in data


def test_reviews_generate_unauthorized(client):
    payload = {
        "product_name": "品牌A咖啡",
        "selling_points": ["低糖", "高香气"],
        "platform": "小红书",
    }
    resp = client.post("/api/reviews/generate", json=payload)
    assert resp.status_code == 401
