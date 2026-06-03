from app.services.video_script import _extract_json_object, _normalize_script


def test_extract_json_object_with_fence():
    text = """```json
    {"title":"t","narration":"n","shots":[{"index":1,"scene_desc":"a","duration_sec":3}]}
    ```"""
    obj = _extract_json_object(text)
    assert obj["title"] == "t"
    assert obj["shots"][0]["scene_desc"] == "a"


def test_normalize_script_fill_missing_shots():
    payload = {"title": "x", "shots": [{"scene_desc": "s1"}]}
    normalized = _normalize_script(payload, shot_count=3)
    assert normalized["title"] == "x"
    assert len(normalized["shots"]) == 3
    assert normalized["shots"][1]["index"] == 2
