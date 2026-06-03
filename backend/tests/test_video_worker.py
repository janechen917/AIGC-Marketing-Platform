from app.models.video_task import VideoTask
from app.workers.video_worker import generate_video_task


def test_confirm_script_generates_images(client, test_db, monkeypatch):
    import app.workers.video_worker as worker_module

    # 创建一条 video task
    row = VideoTask(
        id="v1",
        user_id=None,
        prompt="夏日饮料短视频",
        shot_count=2,
        script_model="m1",
        image_model="m2",
        clip_model="m3",
        status="waiting_confirm",
        stage="script_done",
        script_data={
            "shots": [
                {"index": 1, "scene_desc": "海边饮料特写", "duration_sec": 3},
                {"index": 2, "scene_desc": "冰块飞溅", "duration_sec": 3},
            ]
        },
    )
    test_db.add(row)
    test_db.commit()

    class _Generated:
        def __init__(self, image_bytes: bytes):
            self.image_bytes = image_bytes
            self.image_url = "http://dashscope-temp"
            self.model_used = "qwen-image-2.0"

    monkeypatch.setattr(worker_module, "generate_image", lambda **kwargs: _Generated(b"PNG"))
    monkeypatch.setattr(
        worker_module,
        "upload_bytes",
        lambda key, data, content_type: f"http://minio/{key}",
    )
    monkeypatch.setattr(worker_module, "SessionLocal", lambda: test_db)

    result = generate_video_task.run("v1", "confirm_script", None)
    assert result["status"] == "ok"

    refreshed = test_db.get(VideoTask, "v1")
    assert refreshed is not None
    assert refreshed.stage == "images_done"
    assert refreshed.image_urls is not None
    assert len(refreshed.image_urls) == 2


def test_confirm_images_generates_clips_and_final(client, test_db, monkeypatch):
    import app.workers.video_worker as worker_module

    row = VideoTask(
        id="v2",
        user_id=None,
        prompt="夏日饮料短视频",
        shot_count=2,
        script_model="m1",
        image_model="m2",
        clip_model="m3",
        status="waiting_confirm",
        stage="images_done",
        script_data={
            "shots": [
                {"index": 1, "scene_desc": "海边饮料特写", "duration_sec": 3},
                {"index": 2, "scene_desc": "冰块飞溅", "duration_sec": 3},
            ]
        },
        image_urls=["http://minio/i1.png", "http://minio/i2.png"],
    )
    test_db.add(row)
    test_db.commit()

    monkeypatch.setattr(worker_module, "SessionLocal", lambda: test_db)
    monkeypatch.setattr(
        worker_module,
        "_generate_clips_and_final",
        lambda **kwargs: ([b"c1", b"c2"], b"final"),
    )

    def fake_upload_bytes(*, key, data, content_type):
        return f"http://minio/{key}"

    monkeypatch.setattr(worker_module, "upload_bytes", fake_upload_bytes)

    result = generate_video_task.run("v2", "confirm_images", None)
    assert result["status"] == "ok"

    refreshed = test_db.get(VideoTask, "v2")
    assert refreshed is not None
    assert refreshed.stage == "done"
    assert refreshed.status == "done"
    assert refreshed.final_video_url is not None
    assert refreshed.clip_urls is not None
    assert len(refreshed.clip_urls) == 2
