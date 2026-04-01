from models import PlateType
from plate_rules import normalize_plate_text, plate_validity_bonus


def test_normalize_plate_text_enforces_length_and_charset():
    # Raw has invalid chars and wrong suffix for green plate.
    out = normalize_plate_text("浙A12I4OZ", PlateType.green_small)
    assert out["province"] == "浙"
    assert out["city_code"] == "A"
    assert len(out["number"]) == 6
    assert out["number"][-1] == "?"
    assert "I" not in out["text"]
    assert "O" not in out["text"]


def test_plate_validity_bonus_prefers_compliant_text():
    good = plate_validity_bonus("浙AT1Q96D", PlateType.green_small)
    bad = plate_validity_bonus("?A??????", PlateType.green_small)
    assert good > bad

