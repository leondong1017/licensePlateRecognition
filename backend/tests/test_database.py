import pytest, json, os
from database import Database
from models import PlateResult, PlateType

SAMPLE_PLATE = PlateResult(
    text="粤B88888", province="粤", city_code="B", number="88888",
    type=PlateType.blue, type_label="普通蓝牌", confidence=0.95, bbox=[0,0,80,30]
)

@pytest.fixture
def db(tmp_path):
    d = Database(str(tmp_path / "test.db"), str(tmp_path / "images"))
    d.init()
    return d

def test_insert_and_retrieve(db):
    rid = db.insert_record("img/test.jpg", [SAMPLE_PLATE], used_sr=False)
    assert rid == 1
    result = db.get_record(1)
    assert result["id"] == 1
    assert result["plates"][0]["text"] == "粤B88888"

def test_list_records_pagination(db):
    for i in range(5):
        db.insert_record(f"img/{i}.jpg", [SAMPLE_PLATE], used_sr=False)
    result = db.list_records(page=1, limit=3)
    assert result["total"] == 5
    assert len(result["items"]) == 3

def test_filter_by_plate(db):
    db.insert_record("img/1.jpg", [SAMPLE_PLATE], used_sr=False)
    plate2 = SAMPLE_PLATE.model_copy(update={"text": "京A12345"})
    db.insert_record("img/2.jpg", [plate2], used_sr=False)
    result = db.list_records(plate_filter="京A")
    assert result["total"] == 1

def test_export_csv(db):
    db.insert_record("img/1.jpg", [SAMPLE_PLATE], used_sr=False)
    csv_str = db.export_csv()
    assert "粤B88888" in csv_str
    assert "id,created_at" in csv_str

def test_delete_record(db):
    rid = db.insert_record("img/1.jpg", [SAMPLE_PLATE], used_sr=False)
    image_path = db.delete_record(rid)
    assert image_path == "img/1.jpg"
    assert db.get_record(rid) is None

def test_delete_nonexistent(db):
    result = db.delete_record(999)
    assert result is None


def test_update_feedback(db):
    rid = db.insert_record("img/1.jpg", [SAMPLE_PLATE], used_sr=False)
    assert db.update_feedback(rid, "accurate") is True
    row = db.get_record(rid)
    assert row["user_feedback"] == "accurate"
    assert db.update_feedback(rid, "inaccurate") is True
    assert db.get_record(rid)["user_feedback"] == "inaccurate"
    assert db.update_feedback(rid, None) is True
    assert db.get_record(rid)["user_feedback"] is None

def test_delete_all_records(db):
    db.insert_record("img/1.jpg", [SAMPLE_PLATE], used_sr=False)
    db.insert_record("img/2.jpg", [SAMPLE_PLATE], used_sr=False)
    deleted_paths = db.delete_all_records()
    assert len(deleted_paths) == 2
    assert db.list_records()["total"] == 0
