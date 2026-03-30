import pytest
import numpy as np
from unittest.mock import patch, MagicMock

# Minimal mock results matching HyperLPR3 output format: [text, confidence, bbox, type_str]
MOCK_HIGH_CONF = [["粤B88888", 0.97, [10, 20, 90, 50], "蓝牌"]]
MOCK_LOW_CONF  = [["粤B88888", 0.75, [10, 20, 90, 50], "蓝牌"]]
MOCK_MULTI     = [["粤B88888", 0.97, [10, 20, 90, 50], "蓝牌"],
                  ["京A12345", 0.95, [200, 20, 90, 50], "蓝牌"]]

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

def test_low_confidence_triggers_sr():
    from recognize import RecognizeService
    import sr as sr_module
    svc = RecognizeService.__new__(RecognizeService)
    call_count = {"n": 0}
    def side_effect(img):
        call_count["n"] += 1
        return MOCK_LOW_CONF if call_count["n"] == 1 else [["粤B88888", 0.93, [0, 0, 80, 30], "蓝牌"]]
    svc._catcher = MagicMock(side_effect=side_effect)
    original = sr_module.sr_service.enhance_crop_with_timeout
    sr_module.sr_service.enhance_crop_with_timeout = MagicMock(return_value=make_blank_image())
    try:
        result = svc.recognize(make_blank_image())
        assert result["used_sr"] is True
        assert result["plates"][0].confidence_before_sr == pytest.approx(0.75, abs=0.01)
    finally:
        sr_module.sr_service.enhance_crop_with_timeout = original

def test_multi_vehicle_flag():
    from recognize import RecognizeService
    svc = RecognizeService.__new__(RecognizeService)
    svc._catcher = MagicMock(return_value=MOCK_MULTI)
    result = svc.recognize(make_blank_image())
    assert result["multi_vehicle"] is True
    assert len(result["plates"]) == 2
