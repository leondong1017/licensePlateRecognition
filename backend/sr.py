# backend/sr.py
import cv2
import numpy as np
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

class SRService:
    """Wraps Real-ESRGAN for plate crop super-resolution with timeout."""

    def __init__(self, timeout_seconds: int = 30):
        self.timeout = timeout_seconds
        self._upsampler = None  # lazy init on first use

    def _get_upsampler(self):
        if self._upsampler is None:
            from realesrgan import RealESRGANer
            from basicsr.archs.rrdbnet_arch import RRDBNet
            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64,
                            num_block=23, num_grow_ch=32, scale=4)
            self._upsampler = RealESRGANer(
                scale=4,
                model_path="https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
                model=model,
                tile=0,
                half=False,
            )
        return self._upsampler

    def enhance_crop(self, image_bgr: np.ndarray, bbox: List[int]) -> np.ndarray:
        """Crop plate region, upscale 4×, return enhanced BGR crop."""
        x, y, w, h = bbox
        pad = 4
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(image_bgr.shape[1], x + w + pad)
        y2 = min(image_bgr.shape[0], y + h + pad)
        crop = image_bgr[y1:y2, x1:x2]
        upsampler = self._get_upsampler()
        enhanced, _ = upsampler.enhance(crop, outscale=4)
        return enhanced

    def enhance_crop_with_timeout(self, image_bgr: np.ndarray, bbox: List[int]) -> Optional[np.ndarray]:
        """Returns enhanced crop or None if timeout exceeded."""
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self.enhance_crop, image_bgr, bbox)
            try:
                return future.result(timeout=self.timeout)
            except FuturesTimeout:
                return None

sr_service = SRService()
