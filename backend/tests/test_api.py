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

def test_records_list(client):
    resp = client.get("/api/records")
    assert resp.status_code == 200
    assert "total" in resp.json()

def test_records_export_csv(client):
    resp = client.get("/api/records/export")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
