import io
import pytest
from PIL import Image
from unittest.mock import patch, MagicMock

def _make_png_bytes():
    import numpy as np
    import cv2
    img = np.zeros((100, 200, 3), dtype=np.uint8)
    _, buf = cv2.imencode('.png', img)
    return buf.tobytes()

def _make_webp_bytes():
    import numpy as np
    import cv2
    img = np.zeros((80, 160, 3), dtype=np.uint8)
    ok, buf = cv2.imencode('.webp', img)
    assert ok
    return buf.tobytes()

@pytest.fixture
def client():
    with patch("main.recognize_service") as mock_rec, \
         patch("main.db") as mock_db:
        mock_rec.recognize.return_value = {
            "plates": [], "used_sr": False,
            "multi_vehicle": False, "duration_ms": 50
        }
        mock_db.insert_record.return_value = 1
        mock_db.list_records.return_value = {"total": 0, "items": []}
        mock_db.export_csv.return_value = "id,created_at\n"
        mock_db.delete_record.return_value = "img/test.jpg"
        mock_db.delete_all_records.return_value = ["img/test.jpg"]
        mock_db.get_record.return_value = {
            "id": 1,
            "created_at": "2026-01-01",
            "plates": [],
            "used_sr": False,
            "image_path": "test.jpg",
            "user_feedback": None,
        }
        mock_db.update_feedback = MagicMock(return_value=True)
        from fastapi.testclient import TestClient
        from main import app
        yield TestClient(app)

def test_recognize_returns_200(client):
    resp = client.post(
        "/api/recognize",
        files={"image": ("test.png", _make_png_bytes(), "image/png")}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "record_id" in data
    assert "plates" in data

def test_recognize_invalid_format(client):
    resp = client.post(
        "/api/recognize",
        files={"image": ("test.txt", b"not an image", "text/plain")}
    )
    assert resp.status_code == 400

def test_recognize_webp_returns_200(client):
    resp = client.post(
        "/api/recognize",
        files={"image": ("test.webp", _make_webp_bytes(), "image/webp")}
    )
    assert resp.status_code == 200

def test_records_list(client):
    resp = client.get("/api/records")
    assert resp.status_code == 200
    assert "total" in resp.json()

def test_records_export_csv(client):
    resp = client.get("/api/records/export")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]

def test_get_record(client):
    resp = client.get("/api/records/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 1

def test_delete_record(client):
    resp = client.delete("/api/records/1")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

def test_delete_all_records(client):
    resp = client.delete("/api/records")
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert "deleted" in data


def test_patch_record_feedback(client):
    import main

    main.db.get_record.side_effect = [
        {
            "id": 1,
            "created_at": "2026-01-01",
            "plates": [],
            "used_sr": False,
            "image_path": "test.jpg",
            "user_feedback": None,
        },
        {
            "id": 1,
            "created_at": "2026-01-01",
            "plates": [],
            "used_sr": False,
            "image_path": "test.jpg",
            "user_feedback": "accurate",
        },
    ]
    try:
        resp = client.patch("/api/records/1/feedback", json={"feedback": "accurate"})
        assert resp.status_code == 200
        assert resp.json()["user_feedback"] == "accurate"
        main.db.update_feedback.assert_called_with(1, "accurate")
    finally:
        main.db.get_record.side_effect = None
        main.db.get_record.return_value = {
            "id": 1,
            "created_at": "2026-01-01",
            "plates": [],
            "used_sr": False,
            "image_path": "test.jpg",
            "user_feedback": None,
        }
