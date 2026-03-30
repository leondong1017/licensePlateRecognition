# backend/recognize.py
import time
import numpy as np
from typing import Optional, List, Dict, Any
from models import PlateResult, PlateType, PLATE_TYPE_LABELS
from sr import sr_service
from config import config

_TYPE_MAP = {
    "蓝牌": PlateType.blue,
    "绿牌": PlateType.green_small,
    "黄牌": PlateType.yellow,
    "白牌": PlateType.white,
    "黑牌": PlateType.black,
}

def _parse_text(text: str):
    if len(text) >= 2:
        return text[0], text[1], text[2:]
    return text, "", ""

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
            text, conf, bbox, type_str = item[0], float(item[1]), list(item[2]), item[3]
            plate_type = _TYPE_MAP.get(type_str, PlateType.unknown)
            conf_before_sr = None
            if conf < config.confidence_threshold:
                enhanced = sr_service.enhance_crop_with_timeout(image_bgr, bbox)
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
                bbox=bbox,
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
