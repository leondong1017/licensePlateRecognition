# backend/recognize.py
import time
import numpy as np
from typing import Optional, List, Dict, Any
from models import PlateResult, PlateType, PLATE_TYPE_LABELS
from sr import sr_service
from config import config

# HyperLPR3 color_int → PlateType
# Actual format: [text, confidence, color_int, [x1, y1, x2, y2]]
# color constants: BLUE=0, YELLOW_SINGLE=1, WHILE_SINGLE=2, GREEN=3, BLACK_HK_MACAO=4
_COLOR_MAP = {
    0: PlateType.blue,
    1: PlateType.yellow,
    2: PlateType.white,
    3: PlateType.green_small,
    4: PlateType.black,
    9: PlateType.yellow,   # YELLOW_DOUBLE
}

def _parse_text(text: str):
    if len(text) >= 2:
        return text[0], text[1], text[2:]
    return text, "", ""

def _bbox_to_xywh(bbox: List[int]) -> List[int]:
    """Convert [x1,y1,x2,y2] to [x,y,w,h]."""
    x1, y1, x2, y2 = bbox
    return [x1, y1, x2 - x1, y2 - y1]

class RecognizeService:
    def __init__(self):
        import hyperlpr3 as lpr3
        self._catcher = lpr3.LicensePlateCatcher()

    def recognize(self, image_bgr: np.ndarray, roi: Optional[List[int]] = None) -> Dict[str, Any]:
        start = time.perf_counter()
        if roi:
            x, y, w, h = roi
            image_bgr = image_bgr[y:y+h, x:x+w]
        raw_results = self._catcher(image_bgr)
        plates: List[PlateResult] = []
        used_sr = False
        for item in raw_results:
            # HyperLPR3 format: [text, confidence, color_int, [x1,y1,x2,y2]]
            text = item[0]
            conf = float(item[1])
            color_int = int(item[2])
            bbox_xywh = _bbox_to_xywh(list(item[3]))
            plate_type = _COLOR_MAP.get(color_int, PlateType.unknown)
            conf_before_sr = None
            if conf < config.confidence_threshold:
                enhanced = sr_service.enhance_crop_with_timeout(image_bgr, bbox_xywh)
                if enhanced is not None:
                    re_results = self._catcher(enhanced)
                    if re_results:
                        conf_before_sr = conf
                        conf = float(re_results[0][1])
                        text = re_results[0][0]
                        used_sr = True
            province, city_code, number = _parse_text(text)
            plates.append(PlateResult(
                text=text,
                province=province,
                city_code=city_code,
                number=number,
                type=plate_type,
                type_label=PLATE_TYPE_LABELS[plate_type],
                confidence=conf,
                confidence_before_sr=conf_before_sr,
                bbox=bbox_xywh,
            ))
        duration_ms = int((time.perf_counter() - start) * 1000)
        return {
            "plates": plates,
            "used_sr": used_sr,
            "multi_vehicle": len(plates) > 1,
            "duration_ms": duration_ms,
        }

_recognize_service = None

def get_recognize_service() -> RecognizeService:
    global _recognize_service
    if _recognize_service is None:
        _recognize_service = RecognizeService()
    return _recognize_service

# Module-level singleton — initialized lazily to allow tests to mock before use
try:
    recognize_service = RecognizeService()
except Exception:
    recognize_service = None  # type: ignore
