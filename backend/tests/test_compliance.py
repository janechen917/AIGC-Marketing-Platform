def test_compliance_check_pass(client):
    payload = {
        "text": "品牌A新品发布，欢迎点击了解更多 #新品",
        "brand_name": "品牌A",
        "required_phrases": ["品牌A"],
        "require_hashtag": True,
        "require_cta": True,
        "max_length": 100,
        "max_emojis": 2,
    }
    resp = client.post("/api/compliance/check", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["passed"] is True
    assert data["issue_count"] == 0


def test_compliance_check_blocked(client):
    payload = {
        "text": "这是第一、最佳产品，100%有效，竞品X也比不过。",
        "brand_name": "品牌A",
        "forbidden_competitors": ["竞品X"],
        "require_hashtag": True,
        "require_cta": True,
        "max_length": 20,
    }
    resp = client.post("/api/compliance/check", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["passed"] is False
    assert data["issue_count"] >= 3

    rules = {item["rule"] for item in data["issues"]}
    assert "ad_law" in rules
    assert "brand" in rules
    assert "format" in rules
