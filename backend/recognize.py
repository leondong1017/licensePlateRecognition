# backend/recognize.py
import time
import numpy as np
from typing import Optional, List, Dict, Any
import cv2
from models import PlateResult, PlateType, PLATE_TYPE_LABELS
from sr import sr_service
from plate_rules import normalize_plate_text, plate_validity_bonus

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

def _bbox_to_xywh(bbox: List[int]) -> List[int]:
    """Convert [x1,y1,x2,y2] to [x,y,w,h]."""
    x1, y1, x2, y2 = bbox
    return [x1, y1, x2 - x1, y2 - y1]

def _build_plate(item, conf_before_sr=None) -> PlateResult:
    text = str(item[0])
    conf = float(item[1])
    color_int = int(item[2])
    bbox_xywh = _bbox_to_xywh(list(item[3]))
    plate_type = _COLOR_MAP.get(color_int, PlateType.unknown)
    normalized = normalize_plate_text(text, plate_type)
    return PlateResult(
        text=normalized["text"],
        province=normalized["province"],
        city_code=normalized["city_code"],
        number=normalized["number"],
        type=plate_type,
        type_label=PLATE_TYPE_LABELS[plate_type],
        confidence=conf,
        confidence_before_sr=conf_before_sr,
        bbox=bbox_xywh,
    )


def _crop_by_bbox(image_bgr: np.ndarray, bbox_xywh: List[int], pad: int = 4) -> np.ndarray:
    x, y, w, h = bbox_xywh
    x1 = max(0, x - pad)
    y1 = max(0, y - pad)
    x2 = min(image_bgr.shape[1], x + w + pad)
    y2 = min(image_bgr.shape[0], y + h + pad)
    return image_bgr[y1:y2, x1:x2]


def _enhance_motion_blur(crop_bgr: np.ndarray) -> np.ndarray:
    # Fast route for motion-blur samples: CLAHE + bilateral + unsharp
    gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    eq = clahe.apply(gray)
    denoise = cv2.bilateralFilter(eq, d=5, sigmaColor=35, sigmaSpace=35)
    blur = cv2.GaussianBlur(denoise, (0, 0), 1.2)
    sharp = cv2.addWeighted(denoise, 1.6, blur, -0.6, 0)
    return cv2.cvtColor(sharp, cv2.COLOR_GRAY2BGR)


def _plate_score(plate: PlateResult) -> float:
    return plate.confidence + plate_validity_bonus(plate.text, plate.type)

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
        refined = []
        for plate in plates:
            # Quick refinement for likely motion-blur / low confidence cases
            if plate.confidence >= 0.9 and "?" not in plate.text:
                refined.append(plate)
                continue
            crop = _crop_by_bbox(image_bgr, plate.bbox)
            enhanced = _enhance_motion_blur(crop)
            cand = [plate]
            for src in (crop, enhanced):
                out = self._catcher(src)
                if out:
                    p = _build_plate(out[0])
                    p.bbox = plate.bbox
                    cand.append(p)
            refined.append(max(cand, key=_plate_score))
        plates = refined
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

        candidates: List[PlateResult] = []

        # Route 1: baseline from original detection at target bbox
        for item in original_results:
            item_bbox = _bbox_to_xywh(list(item[3]))
            if item_bbox == bbox_xywh:
                base = _build_plate(item, conf_before_sr=conf_before_sr)
                base.bbox = bbox_xywh
                candidates.append(base)
                break

        # Route 2: crop + fast deblur preprocess
        crop = _crop_by_bbox(image_bgr, bbox_xywh)
        for src in (crop, _enhance_motion_blur(crop)):
            out = self._catcher(src)
            if out:
                p = _build_plate(out[0], conf_before_sr=conf_before_sr)
                p.bbox = bbox_xywh
                candidates.append(p)

        # Route 3: SR + optional deblur
        enhanced = sr_service.enhance_crop_with_timeout(image_bgr, bbox_xywh)
        if enhanced is not None:
            for src in (enhanced, _enhance_motion_blur(enhanced)):
                out = self._catcher(src)
                if out:
                    p = _build_plate(out[0], conf_before_sr=conf_before_sr)
                    p.bbox = bbox_xywh
                    candidates.append(p)
            if candidates:
                return max(candidates, key=_plate_score)

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
