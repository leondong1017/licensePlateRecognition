import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_recognize_result():
    return {
        "plates": [],
        "used_sr": False,
        "multi_vehicle": False,
        "duration_ms": 50,
    }
