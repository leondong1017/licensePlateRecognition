# backend/recognize.py
import time
import numpy as np
from typing import Optional, List, Dict, Any
from models import PlateResult, PlateType, PLATE_TYPE_LABELS
from sr import sr_service
from config import config

# HyperLPR3 color_int → PlateType
# Format: [text, confidence, color_int, [x1, y1, x2, y2]]
_COLOR_MAP = {
    0: PlateType.blue,
    1: PlateType.yellow,
    2: PlateType.white,
    3: PlateType.green_small,
    4: PlateType.black,
    9: PlateType.yellow,
}

def _parse_text(text: str):
    if len(text) >= 2:
        return text[0], text[1], text[2:]
    return text, "", ""

def _bbox_to_xywh(bbox: List[int]) -> List[int]:
    """Convert [x1,y1,x2,y2] to [x,y,w,h]."""
    x1, y1, x2, y2 = bbox
    return [x1, y1, x2 - x1, y2 - y1]

def _build_plate(item, conf_before_sr=None) -> PlateResult:
    text = item[0]
    conf = float(item[1])
    color_int = int(item[2])
    bbox_xywh = _bbox_to_xywh(list(item[3]))
    plate_type = _COLOR_MAP.get(color_int, PlateType.unknown)
    province, city_code, number = _parse_text(text)
    return PlateResult(
        text=text,
        province=province,
        city_code=city_code,
        number=number,
        type=plate_type,
        type_label=PLATE_TYPE_LABELS[plate_type],
        confidence=conf,
        confidence_before_sr=conf_before_sr,
        bbox=bbox_xywh,
    )

class RecognizeService:
    def __init__(self):
        import hyperlpr3 as lpr3
        self._catcher = lpr3.LicensePlateCatcher()

    def recognize(self, image_bgr: np.ndarray, roi: Optional[List[int]] = None) -> Dict[str, Any]:
        """Detect all plates quickly, NO super-resolution applied here."""
        start = time.perf_counter()
        if roi:
            x, y, w, h = roi
            image_bgr = image_bgr[y:y+h, x:x+w]
        raw_results = self._catcher(image_bgr)
        plates = [_build_plate(item) for item in raw_results]
        duration_ms = int((time.perf_counter() - start) * 1000)
        return {
            "plates": plates,
            "used_sr": False,
            "multi_vehicle": len(plates) > 1,
            "duration_ms": duration_ms,
        }

    def recognize_with_sr(self, image_bgr: np.ndarray, bbox_xywh: List[int]) -> PlateResult:
        """Apply SR unconditionally on the given bbox region, then re-recognize."""
        original_results = self._catcher(image_bgr)
        # Find the plate at this bbox for baseline confidence
        conf_before_sr = None
        for item in original_results:
            item_bbox = _bbox_to_xywh(list(item[3]))
            if item_bbox == bbox_xywh:
                conf_before_sr = float(item[1])
                break

        enhanced = sr_service.enhance_crop_with_timeout(image_bgr, bbox_xywh)
        if enhanced is not None:
            re_results = self._catcher(enhanced)
            if re_results:
                plate = _build_plate(re_results[0], conf_before_sr=conf_before_sr)
                plate.bbox = bbox_xywh  # keep original bbox coords for display
                return plate

        # SR failed or no result — fall back to original detection
        for item in original_results:
            item_bbox = _bbox_to_xywh(list(item[3]))
            if item_bbox == bbox_xywh:
                return _build_plate(item)
        # Last resort: re-run on cropped region without SR
        x, y, w, h = bbox_xywh
        crop = image_bgr[y:y+h, x:x+w]
        fallback = self._catcher(crop)
        if fallback:
            return _build_plate(fallback[0])
        return _build_plate([f"未知", 0.0, 0, [0, 0, 1, 1]])

_recognize_service = None

def get_recognize_service() -> RecognizeService:
    global _recognize_service
    if _recognize_service is None:
        _recognize_service = RecognizeService()
    return _recognize_service

try:
    recognize_service = RecognizeService()
except Exception:
    recognize_service = None  # type: ignore
