from app.schemas.reviews import ReviewsGenerateRequest
from app.services.llm_router import ChatResult
from app.services import review_generator


def _fake_chat_result(text: str) -> ChatResult:
    return ChatResult(
        text=text,
        model_used="qwen-plus",
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
        raw={},
    )


def test_generate_reviews_dedupe_and_compliance_counts(test_db, monkeypatch):
    outputs = [
        """1. 好喝不腻 #推荐
2. 好喝不腻#推荐
3. 通勤携带很方便
4. 含违禁词内容""",
        """1. 真香值得回购
2. 家里人都说不错""",
    ]

    def fake_chat(**kwargs):
        return _fake_chat_result(outputs.pop(0))

    def fake_check_all(text: str, **kwargs):
        if "违禁" in text:
            return {"passed": False, "issue_count": 1, "issues": [{"rule": "sensitive", "message": "bad", "level": "high"}]}
        return {"passed": True, "issue_count": 0, "issues": []}

    monkeypatch.setattr(review_generator.llm_router, "chat", fake_chat)
    monkeypatch.setattr(review_generator, "check_all", fake_check_all)

    req = ReviewsGenerateRequest(
        product_name="品牌A咖啡",
        selling_points=["低糖", "高香气"],
        platform="小红书",
        target_count=3,
        batch_size=4,
        max_rounds=3,
        similarity_threshold=0.9,
    )

    resp = review_generator.generate_reviews(req=req, db=test_db, user_id=1)

    assert resp.total_generated == 3
    assert len(resp.reviews) == 3
    assert resp.deduped_dropped >= 1
    assert resp.compliance_dropped >= 1
    assert resp.csv_content.startswith("index,review")


def test_generate_reviews_target_100_finishes_within_5_rounds(test_db, monkeypatch):
    call_count = {"n": 0}

    def fake_chat(**kwargs):
        call_count["n"] += 1
        batch_lines = [f"第{call_count['n']}轮-第{i}条好评" for i in range(1, 21)]
        return _fake_chat_result("\n".join(batch_lines))

    def fake_check_all(text: str, **kwargs):
        return {"passed": True, "issue_count": 0, "issues": []}

    monkeypatch.setattr(review_generator.llm_router, "chat", fake_chat)
    monkeypatch.setattr(review_generator, "check_all", fake_check_all)

    req = ReviewsGenerateRequest(
        product_name="品牌A咖啡",
        selling_points=["低糖", "高香气"],
        platform="小红书",
        target_count=100,
        batch_size=20,
        max_rounds=5,
        similarity_threshold=0.95,
    )

    resp = review_generator.generate_reviews(req=req, db=test_db, user_id=1)

    assert resp.total_generated == 100
    assert len(resp.reviews) == 100
    assert resp.rounds == 5
    assert call_count["n"] == 5
    assert resp.deduped_dropped == 0
    assert resp.compliance_dropped == 0
