from typing import Dict

from models import PlateType

VALID_ALNUM = set("ABCDEFGHJKLMNPQRSTUVWXYZ0123456789")
PROVINCES = set(
    "京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼港澳使领学警"
)

EXPECTED_NUMBER_LEN: Dict[PlateType, int] = {
    PlateType.blue: 5,
    PlateType.yellow: 5,
    PlateType.white: 5,
    PlateType.black: 5,
    PlateType.green_small: 6,
    PlateType.unknown: 5,
}


def _safe_char(ch: str) -> str:
    if not ch:
        return "?"
    c = ch.upper()
    return c if c in VALID_ALNUM else "?"


def normalize_plate_text(raw_text: str, plate_type: PlateType) -> Dict[str, str]:
    text = (raw_text or "").strip().upper()
    province = text[0] if len(text) >= 1 else "?"
    city_code = _safe_char(text[1] if len(text) >= 2 else "?")
    number_raw = text[2:] if len(text) > 2 else ""

    expected = EXPECTED_NUMBER_LEN.get(plate_type, 5)
    number = number_raw.ljust(expected, "?")[:expected]

    fixed = []
    for idx, ch in enumerate(number):
        cur = _safe_char(ch)
        if plate_type == PlateType.green_small and idx == expected - 1 and cur not in {"D", "F"}:
            cur = "?"
        fixed.append(cur)
    number_norm = "".join(fixed)

    # Province best effort: keep Chinese province char, otherwise fallback '?'
    if province not in PROVINCES:
        province = "?"

    norm_text = f"{province}{city_code}{number_norm}"
    return {
        "text": norm_text,
        "province": province,
        "city_code": city_code,
        "number": number_norm,
    }


def plate_validity_bonus(text: str, plate_type: PlateType) -> float:
    if not text:
        return -0.3
    bonus = 0.0
    if "?" not in text:
        bonus += 0.12
    else:
        bonus -= 0.06 * min(text.count("?"), 3)

    expected_len = 8 if plate_type == PlateType.green_small else 7
    if len(text) == expected_len:
        bonus += 0.05
    else:
        bonus -= 0.08

    if plate_type == PlateType.green_small and len(text) >= 8:
        bonus += 0.04 if text[-1] in {"D", "F"} else -0.08

    return bonus

