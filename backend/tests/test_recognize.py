import pytest
import numpy as np
from unittest.mock import patch, MagicMock

# Fix: HyperLPR3 format is [text, conf, color_int, [x1,y1,x2,y2]]
MOCK_HIGH_CONF = [["粤B88888", 0.97, 0, [10, 20, 100, 70]]]
MOCK_LOW_CONF  = [["粤B88888", 0.75, 0, [10, 20, 100, 70]]]
MOCK_MULTI     = [["粤B88888", 0.97, 0, [10, 20, 100, 70]],
                  ["京A12345", 0.95, 0, [200, 20, 290, 70]]]

def make_blank_image():
    return np.zeros((200, 400, 3), dtype=np.uint8)

def test_high_confidence_no_sr():
    from recognize import RecognizeService
    svc = RecognizeService.__new__(RecognizeService)
    svc._catcher = MagicMock(return_value=MOCK_HIGH_CONF)
    result = svc.recognize(make_blank_image())
    assert result["used_sr"] is False
    assert len(result["plates"]) == 1
    assert result["plates"][0].text == "粤B88888"
    assert result["multi_vehicle"] is False

def test_multi_vehicle_flag():
    from recognize import RecognizeService
    svc = RecognizeService.__new__(RecognizeService)
    svc._catcher = MagicMock(return_value=MOCK_MULTI)
    result = svc.recognize(make_blank_image())
    assert result["multi_vehicle"] is True
    assert len(result["plates"]) == 2

def test_recognize_with_sr_applies_enhancement():
    from recognize import RecognizeService
    import sr as sr_module
    svc = RecognizeService.__new__(RecognizeService)
    svc._catcher = MagicMock(return_value=MOCK_HIGH_CONF)
    enhanced_img = make_blank_image()
    original_fn = sr_module.sr_service.enhance_crop_with_timeout
    sr_module.sr_service.enhance_crop_with_timeout = MagicMock(return_value=enhanced_img)
    try:
        plate = svc.recognize_with_sr(make_blank_image(), [10, 20, 90, 50])
        assert plate is not None
        assert sr_module.sr_service.enhance_crop_with_timeout.called
    finally:
        sr_module.sr_service.enhance_crop_with_timeout = original_fn
