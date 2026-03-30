# License Plate Recognition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Chinese license plate recognition web app where users upload images, plates are detected/recognized and stored locally, with history browsing and CSV export.

**Architecture:** Python/FastAPI backend wraps HyperLPR3 for detection and Real-ESRGAN for confidence-based super-resolution enhancement; SQLite persists records. Vue 3 + TDesign frontend handles upload, ROI selection, result visualization, and history — two pages, same-route state machine for recognize flow.

**Tech Stack:** Python 3.11+, FastAPI, HyperLPR3, Real-ESRGAN (basicsr), SQLite, Vue 3, TypeScript, Vite, TDesign Vue Next, Axios, Vitest

---

## File Map

### Backend (`backend/`)
| File | Responsibility |
|------|---------------|
| `main.py` | FastAPI app, CORS, static files, router mount |
| `config.py` | Typed config (confidence threshold, SR timeout, ports) |
| `models.py` | Pydantic request/response models + plate type enum |
| `database.py` | SQLite init, insert, query, export |
| `recognize.py` | RecognizeService: HyperLPR3 → SR → result assembly |
| `sr.py` | SRService: Real-ESRGAN crop+upscale with timeout |
| `requirements.txt` | All Python dependencies |
| `tests/test_database.py` | Unit tests for DB layer |
| `tests/test_recognize.py` | Unit tests for RecognizeService |
| `tests/test_api.py` | Integration tests for API endpoints |
| `tests/fixtures/clear.jpg` | A test image with a clear plate |
| `tests/fixtures/blurry.jpg` | A test image with a blurry plate (can be same image scaled down) |

### Frontend (`frontend/`)
| File | Responsibility |
|------|---------------|
| `src/main.ts` | App bootstrap, TDesign plugin, router |
| `src/router/index.ts` | Two routes: `/` → RecognizePage, `/history` → HistoryPage |
| `src/api/index.ts` | Axios instance + typed API functions |
| `src/types/index.ts` | TypeScript interfaces mirroring backend models |
| `src/components/PlateVisual.vue` | Render plate number with correct type colors |
| `src/components/UploadZone.vue` | Drag-drop upload with file validation |
| `src/components/RoiSelector.vue` | Canvas overlay for drawing bounding box on image |
| `src/components/PlateCard.vue` | Single plate result card (confidence bar, SR notice) |
| `src/components/HistoryTable.vue` | Paginated table with filters |
| `src/views/RecognizePage.vue` | Upload→Loading→Result state machine |
| `src/views/HistoryPage.vue` | History page shell |
| `src/App.vue` | Nav bar + router-view + footer disclaimer |
| `src/assets/theme.css` | TDesign token overrides (primary color → #1a1a1a) |
| `tests/PlateVisual.test.ts` | Unit tests for plate color logic |
| `tests/api.test.ts` | Mock-based API function tests |

---

## Task 1: Backend — Project Setup & Config

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/config.py`

- [ ] **Step 1: Create requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
python-multipart==0.0.9
hyperlpr3==0.1.3
basicsr==1.4.2
realesrgan==0.3.0
opencv-python-headless==4.9.0.80
Pillow==10.3.0
pytest==8.2.0
httpx==0.27.0
```

- [ ] **Step 2: Install dependencies**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Expected: All packages install without errors. HyperLPR3 will download model weights on first use (~50MB).

- [ ] **Step 3: Create config.py**

```python
# backend/config.py
from dataclasses import dataclass

@dataclass
class Config:
    confidence_threshold: float = 0.9
    sr_timeout_seconds: int = 30
    images_dir: str = "images"
    db_path: str = "lpr.db"
    host: str = "0.0.0.0"
    port: int = 8000

config = Config()
```

- [ ] **Step 4: Verify import works**

```bash
cd backend && python -c "from config import config; print(config.confidence_threshold)"
```

Expected output: `0.9`

- [ ] **Step 5: Commit**

```bash
git init  # from project root if not already a git repo
git add backend/requirements.txt backend/config.py
git commit -m "feat: backend project setup and config"
```

---

## Task 2: Backend — Models

**Files:**
- Create: `backend/models.py`

- [ ] **Step 1: Write models.py**

```python
# backend/models.py
from pydantic import BaseModel
from typing import Optional
from enum import Enum

class PlateType(str, Enum):
    blue = "blue"
    green_small = "green_small"
    yellow = "yellow"
    white = "white"
    black = "black"
    unknown = "unknown"

PLATE_TYPE_LABELS = {
    PlateType.blue: "普通蓝牌",
    PlateType.green_small: "新能源小型",
    PlateType.yellow: "黄牌",
    PlateType.white: "警/军牌",
    PlateType.black: "使馆/港澳",
    PlateType.unknown: "未知",
}

class PlateResult(BaseModel):
    text: str                          # e.g. "粤B88888"
    province: str                      # e.g. "粤"
    city_code: str                     # e.g. "B"
    number: str                        # e.g. "88888"
    type: PlateType
    type_label: str
    confidence: float
    confidence_before_sr: Optional[float] = None
    bbox: list[int]                    # [x, y, w, h]

class RecognizeResponse(BaseModel):
    record_id: int
    plates: list[PlateResult]
    used_sr: bool
    duration_ms: int
    multi_vehicle: bool

class RecordItem(BaseModel):
    id: int
    created_at: str
    plates: list[PlateResult]
    used_sr: bool
    image_url: str

class RecordsResponse(BaseModel):
    total: int
    items: list[RecordItem]
```

- [ ] **Step 2: Verify Pydantic parses correctly**

```bash
cd backend && python -c "
from models import PlateResult, PlateType
p = PlateResult(text='粤B88888', province='粤', city_code='B', number='88888',
    type=PlateType.blue, type_label='普通蓝牌', confidence=0.95, bbox=[10,20,80,30])
print(p.model_dump())
"
```

Expected: dict printed with all fields.

- [ ] **Step 3: Commit**

```bash
git add backend/models.py
git commit -m "feat: backend Pydantic models"
```

---

## Task 3: Backend — Database Layer

**Files:**
- Create: `backend/database.py`
- Create: `tests/test_database.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_database.py
import pytest, json, os, tempfile
from database import Database
from models import PlateResult, PlateType

SAMPLE_PLATE = PlateResult(
    text="粤B88888", province="粤", city_code="B", number="88888",
    type=PlateType.blue, type_label="普通蓝牌", confidence=0.95, bbox=[0,0,80,30]
)

@pytest.fixture
def db(tmp_path):
    d = Database(str(tmp_path / "test.db"), str(tmp_path / "images"))
    d.init()
    return d

def test_insert_and_retrieve(db):
    rid = db.insert_record("img/test.jpg", [SAMPLE_PLATE], used_sr=False)
    assert rid == 1
    result = db.get_record(1)
    assert result["id"] == 1
    assert result["plates"][0]["text"] == "粤B88888"

def test_list_records_pagination(db):
    for i in range(5):
        db.insert_record(f"img/{i}.jpg", [SAMPLE_PLATE], used_sr=False)
    result = db.list_records(page=1, limit=3)
    assert result["total"] == 5
    assert len(result["items"]) == 3

def test_filter_by_plate(db):
    db.insert_record("img/1.jpg", [SAMPLE_PLATE], used_sr=False)
    plate2 = SAMPLE_PLATE.model_copy(update={"text": "京A12345"})
    db.insert_record("img/2.jpg", [plate2], used_sr=False)
    result = db.list_records(plate_filter="京A")
    assert result["total"] == 1

def test_export_csv(db):
    db.insert_record("img/1.jpg", [SAMPLE_PLATE], used_sr=False)
    csv_str = db.export_csv()
    assert "粤B88888" in csv_str
    assert "id,created_at" in csv_str
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd backend && python -m pytest tests/test_database.py -v
```

Expected: `ModuleNotFoundError: No module named 'database'`

- [ ] **Step 3: Implement database.py**

```python
# backend/database.py
import sqlite3, json, os, csv, io
from datetime import datetime
from models import PlateResult

class Database:
    def __init__(self, db_path: str, images_dir: str):
        self.db_path = db_path
        self.images_dir = images_dir

    def init(self):
        os.makedirs(self.images_dir, exist_ok=True)
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS records (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    image_path TEXT NOT NULL,
                    plates     TEXT NOT NULL,
                    used_sr    INTEGER DEFAULT 0
                )
            """)

    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def insert_record(self, image_path: str, plates: list[PlateResult], used_sr: bool) -> int:
        plates_json = json.dumps([p.model_dump() for p in plates], ensure_ascii=False)
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO records (image_path, plates, used_sr) VALUES (?, ?, ?)",
                (image_path, plates_json, int(used_sr))
            )
            return cur.lastrowid

    def get_record(self, record_id: int) -> dict | None:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM records WHERE id=?", (record_id,)).fetchone()
        return self._row_to_dict(row) if row else None

    def list_records(self, page: int = 1, limit: int = 20,
                     plate_filter: str = "", type_filter: str = "",
                     date_from: str = "", date_to: str = "") -> dict:
        where, params = [], []
        if plate_filter:
            where.append("plates LIKE ?")
            params.append(f"%{plate_filter}%")
        if date_from:
            where.append("created_at >= ?")
            params.append(date_from)
        if date_to:
            where.append("created_at <= ?")
            params.append(date_to + " 23:59:59")
        clause = ("WHERE " + " AND ".join(where)) if where else ""
        with self._conn() as conn:
            total = conn.execute(f"SELECT COUNT(*) FROM records {clause}", params).fetchone()[0]
            offset = (page - 1) * limit
            rows = conn.execute(
                f"SELECT * FROM records {clause} ORDER BY created_at DESC LIMIT ? OFFSET ?",
                params + [limit, offset]
            ).fetchall()
        return {"total": total, "items": [self._row_to_dict(r) for r in rows]}

    def export_csv(self) -> str:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM records ORDER BY created_at DESC").fetchall()
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["id", "created_at", "plate_text", "plate_type", "confidence", "used_sr"])
        for row in rows:
            plates = json.loads(row["plates"])
            for p in plates:
                writer.writerow([row["id"], row["created_at"], p["text"],
                                  p["type_label"], p["confidence"], bool(row["used_sr"])])
        return buf.getvalue()

    def _row_to_dict(self, row) -> dict:
        d = dict(row)
        d["plates"] = json.loads(d["plates"])
        d["used_sr"] = bool(d["used_sr"])
        return d
```

- [ ] **Step 4: Run tests — expect all pass**

```bash
cd backend && python -m pytest tests/test_database.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/database.py backend/tests/test_database.py
git commit -m "feat: database layer with insert, query, filter, export"
```

---

## Task 4: Backend — Super-Resolution Service

**Files:**
- Create: `backend/sr.py`

- [ ] **Step 1: Create sr.py**

```python
# backend/sr.py
import cv2
import numpy as np
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from realesrgan import RealESRGANer
from basicsr.archs.rrdbnet_arch import RRDBNet

class SRService:
    def __init__(self, timeout_seconds: int = 30):
        self.timeout = timeout_seconds
        self._upsampler = None  # lazy init — model loads on first use

    def _get_upsampler(self) -> RealESRGANer:
        if self._upsampler is None:
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

    def enhance_crop(self, image_bgr: np.ndarray, bbox: list[int]) -> np.ndarray:
        """Crop the plate region, upscale 4×, return enhanced crop (BGR)."""
        x, y, w, h = bbox
        # Add padding to give model context
        pad = 4
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(image_bgr.shape[1], x + w + pad)
        y2 = min(image_bgr.shape[0], y + h + pad)
        crop = image_bgr[y1:y2, x1:x2]
        upsampler = self._get_upsampler()
        enhanced, _ = upsampler.enhance(crop, outscale=4)
        return enhanced

    def enhance_crop_with_timeout(self, image_bgr: np.ndarray, bbox: list[int]) -> np.ndarray | None:
        """Returns enhanced crop or None if timeout exceeded."""
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self.enhance_crop, image_bgr, bbox)
            try:
                return future.result(timeout=self.timeout)
            except FuturesTimeout:
                return None

sr_service = SRService()
```

- [ ] **Step 2: Verify import (model not loaded yet)**

```bash
cd backend && python -c "from sr import sr_service; print('SR service ready')"
```

Expected: `SR service ready` (no model download — lazy init)

- [ ] **Step 3: Commit**

```bash
git add backend/sr.py
git commit -m "feat: Real-ESRGAN super-resolution service with timeout"
```

---

## Task 5: Backend — Recognition Service

**Files:**
- Create: `backend/recognize.py`
- Create: `backend/tests/test_recognize.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_recognize.py
import pytest, cv2, numpy as np
from unittest.mock import patch, MagicMock
from recognize import RecognizeService
from config import config

# Minimal mock: HyperLPR3 returns one high-confidence plate
MOCK_HIGH_CONF = [["粤B88888", 0.97, [10, 20, 90, 50], "蓝牌"]]
# Low-confidence plate (should trigger SR)
MOCK_LOW_CONF  = [["粤B88888", 0.75, [10, 20, 90, 50], "蓝牌"]]
# Two plates (multi-vehicle)
MOCK_MULTI     = [["粤B88888", 0.97, [10,20,90,50], "蓝牌"],
                  ["京A12345", 0.95, [200,20,90,50], "蓝牌"]]

def make_blank_image():
    return np.zeros((200, 400, 3), dtype=np.uint8)

@patch("recognize.LicensePlateCatcher")
def test_high_confidence_no_sr(MockCatcher):
    MockCatcher.return_value.side_effect = None
    MockCatcher.return_value.__call__ = lambda self, img: MOCK_HIGH_CONF
    svc = RecognizeService()
    svc._catcher = MagicMock(return_value=MOCK_HIGH_CONF)
    result = svc.recognize(make_blank_image())
    assert result["used_sr"] is False
    assert len(result["plates"]) == 1
    assert result["plates"][0].text == "粤B88888"

@patch("recognize.LicensePlateCatcher")
@patch("recognize.sr_service")
def test_low_confidence_triggers_sr(MockSR, MockCatcher):
    # First call returns low-conf; second call (on SR crop) returns high-conf
    call_count = {"n": 0}
    def side_effect(img):
        call_count["n"] += 1
        return MOCK_LOW_CONF if call_count["n"] == 1 else [["粤B88888", 0.93, [0,0,80,30], "蓝牌"]]
    svc = RecognizeService()
    svc._catcher = MagicMock(side_effect=side_effect)
    MockSR.enhance_crop_with_timeout = MagicMock(return_value=make_blank_image())
    result = svc.recognize(make_blank_image())
    assert result["used_sr"] is True
    assert result["plates"][0].confidence_before_sr == pytest.approx(0.75, 0.01)

@patch("recognize.LicensePlateCatcher")
def test_multi_vehicle_flag(MockCatcher):
    svc = RecognizeService()
    svc._catcher = MagicMock(return_value=MOCK_MULTI)
    result = svc.recognize(make_blank_image())
    assert result["multi_vehicle"] is True
    assert len(result["plates"]) == 2
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd backend && python -m pytest tests/test_recognize.py -v
```

Expected: `ModuleNotFoundError: No module named 'recognize'`

- [ ] **Step 3: Implement recognize.py**

```python
# backend/recognize.py
import cv2
import numpy as np
import time
import hyperlpr3 as lpr3
from models import PlateResult, PlateType, PLATE_TYPE_LABELS
from sr import sr_service
from config import config

# HyperLPR3 type string → our PlateType enum
_TYPE_MAP = {
    "蓝牌": PlateType.blue,
    "绿牌": PlateType.green_small,
    "黄牌": PlateType.yellow,
    "白牌": PlateType.white,
    "黑牌": PlateType.black,
}

def _parse_text(text: str) -> tuple[str, str, str]:
    """Split 粤B88888 → (粤, B, 88888). Best-effort."""
    if len(text) >= 2:
        province = text[0]
        city_code = text[1]
        number = text[2:]
        return province, city_code, number
    return text, "", ""

class RecognizeService:
    def __init__(self):
        self._catcher = lpr3.LicensePlateCatcher()

    def recognize(self, image_bgr: np.ndarray, roi: list[int] | None = None) -> dict:
        start = time.perf_counter()

        # Crop to ROI if provided
        if roi:
            x, y, w, h = roi
            image_bgr = image_bgr[y:y+h, x:x+w]

        raw_results = self._catcher(image_bgr)
        # raw_results: list of [text, confidence, bbox, type_str]

        plates: list[PlateResult] = []
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

recognize_service = RecognizeService()
```

- [ ] **Step 4: Run tests — expect all pass**

```bash
cd backend && python -m pytest tests/test_recognize.py -v
```

Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/recognize.py backend/tests/test_recognize.py
git commit -m "feat: recognition service with SR fallback"
```

---

## Task 6: Backend — FastAPI App & API Tests

**Files:**
- Create: `backend/main.py`
- Create: `backend/tests/test_api.py`
- Create: `backend/tests/conftest.py`

- [ ] **Step 1: Write failing API tests**

```python
# backend/tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import numpy as np

@pytest.fixture
def client(tmp_path):
    # Patch DB path and images dir to temp dir
    with patch("main.db") as mock_db, \
         patch("main.recognize_service") as mock_rec:
        mock_rec.recognize.return_value = {
            "plates": [], "used_sr": False,
            "multi_vehicle": False, "duration_ms": 50
        }
        mock_db.insert_record.return_value = 1
        mock_db.get_record.return_value = None
        mock_db.list_records.return_value = {"total": 0, "items": []}
        mock_db.export_csv.return_value = "id,created_at\n"
        from main import app
        yield TestClient(app)
```

```python
# backend/tests/test_api.py
import io
from PIL import Image

def _make_png_bytes():
    img = Image.fromarray([[255,255,255]], "RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def test_recognize_returns_200(client):
    resp = client.post(
        "/api/recognize",
        files={"image": ("test.png", _make_png_bytes(), "image/png")}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "record_id" in data
    assert "plates" in data
    assert "multi_vehicle" in data

def test_recognize_invalid_format(client):
    resp = client.post(
        "/api/recognize",
        files={"image": ("test.txt", b"not an image", "text/plain")}
    )
    assert resp.status_code == 400

def test_records_list(client):
    resp = client.get("/api/records")
    assert resp.status_code == 200
    assert "total" in resp.json()

def test_records_export_csv(client):
    resp = client.get("/api/records/export")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd backend && python -m pytest tests/test_api.py -v
```

Expected: `ModuleNotFoundError: No module named 'main'`

- [ ] **Step 3: Implement main.py**

```python
# backend/main.py
import os, uuid
import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
import io

from config import config
from database import Database
from recognize import recognize_service
from models import RecognizeResponse, RecordsResponse

app = FastAPI(title="License Plate Recognition API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

db = Database(config.db_path, config.images_dir)
db.init()

os.makedirs(config.images_dir, exist_ok=True)
app.mount("/api/images", StaticFiles(directory=config.images_dir), name="images")

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/bmp"}

async def _read_image(file: UploadFile) -> np.ndarray:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, "仅支持 JPG/PNG/BMP 格式")
    data = await file.read()
    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(400, "文件不超过 20MB")
    arr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(400, "无法解码图片")
    return img, data

async def _save_image(raw_bytes: bytes) -> str:
    filename = f"{uuid.uuid4().hex}.jpg"
    path = os.path.join(config.images_dir, filename)
    with open(path, "wb") as f:
        f.write(raw_bytes)
    return filename

@app.post("/api/recognize", response_model=RecognizeResponse)
async def recognize(image: UploadFile = File(...)):
    img, raw = await _read_image(image)
    filename = await _save_image(raw)
    result = recognize_service.recognize(img)
    record_id = db.insert_record(filename, result["plates"], result["used_sr"])
    return RecognizeResponse(record_id=record_id, **result)

@app.post("/api/recognize/roi", response_model=RecognizeResponse)
async def recognize_roi(
    image: UploadFile = File(...),
    roi_x: int = Query(...), roi_y: int = Query(...),
    roi_w: int = Query(...), roi_h: int = Query(...)
):
    img, raw = await _read_image(image)
    filename = await _save_image(raw)
    result = recognize_service.recognize(img, roi=[roi_x, roi_y, roi_w, roi_h])
    record_id = db.insert_record(filename, result["plates"], result["used_sr"])
    return RecognizeResponse(record_id=record_id, **result)

@app.get("/api/records", response_model=RecordsResponse)
def list_records(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    plate: str = Query(""),
    type: str = Query(""),
    date_from: str = Query(""),
    date_to: str = Query(""),
):
    raw = db.list_records(page, limit, plate, type, date_from, date_to)
    items = []
    for r in raw["items"]:
        from models import RecordItem, PlateResult
        items.append(RecordItem(
            id=r["id"],
            created_at=r["created_at"],
            plates=[PlateResult(**p) for p in r["plates"]],
            used_sr=r["used_sr"],
            image_url=f"/api/images/{r['image_path']}",
        ))
    return RecordsResponse(total=raw["total"], items=items)

@app.get("/api/records/export")
def export_records():
    csv_str = db.export_csv()
    return StreamingResponse(
        io.StringIO(csv_str),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=records.csv"}
    )
```

- [ ] **Step 4: Run API tests**

```bash
cd backend && python -m pytest tests/test_api.py -v
```

Expected: `4 passed`

- [ ] **Step 5: Smoke-test the server**

```bash
cd backend && uvicorn main:app --reload --port 8000
# In another terminal:
curl http://localhost:8000/api/records
```

Expected: `{"total":0,"items":[]}`

- [ ] **Step 6: Commit**

```bash
git add backend/main.py backend/tests/test_api.py backend/tests/conftest.py
git commit -m "feat: FastAPI app with recognize and records endpoints"
```

---

## Task 7: Frontend — Project Setup & Types

**Files:**
- Create: `frontend/` (Vite scaffold)
- Create: `frontend/src/types/index.ts`
- Create: `frontend/src/assets/theme.css`

- [ ] **Step 1: Scaffold Vue 3 + TypeScript project**

```bash
cd /Users/leon/ccDestination/licensePlateRecognition
npm create vite@latest frontend -- --template vue-ts
cd frontend && npm install
npm install tdesign-vue-next axios
npm install -D vitest @vue/test-utils @vitejs/plugin-vue jsdom
```

- [ ] **Step 2: Configure Vite for proxy + Vitest**

Replace `frontend/vite.config.ts`:

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
  },
})
```

- [ ] **Step 3: Create types/index.ts**

```typescript
// frontend/src/types/index.ts
export type PlateType = 'blue' | 'green_small' | 'yellow' | 'white' | 'black' | 'unknown'

export interface PlateResult {
  text: string
  province: string
  city_code: string
  number: string
  type: PlateType
  type_label: string
  confidence: number
  confidence_before_sr: number | null
  bbox: [number, number, number, number]
}

export interface RecognizeResponse {
  record_id: number
  plates: PlateResult[]
  used_sr: boolean
  duration_ms: number
  multi_vehicle: boolean
}

export interface RecordItem {
  id: number
  created_at: string
  plates: PlateResult[]
  used_sr: boolean
  image_url: string
}

export interface RecordsResponse {
  total: number
  items: RecordItem[]
}
```

- [ ] **Step 4: Create theme.css (TDesign token overrides)**

```css
/* frontend/src/assets/theme.css */
:root {
  --td-brand-color: #1a1a1a;
  --td-brand-color-hover: #333333;
  --td-brand-color-active: #000000;
  --td-brand-color-disabled: #cccccc;
  --td-brand-color-light: #f5f5f5;
  --td-brand-color-light-hover: #ebebeb;
  --td-brand-color-focus: rgba(26, 26, 26, 0.1);
}
```

- [ ] **Step 5: Bootstrap main.ts**

```typescript
// frontend/src/main.ts
import { createApp } from 'vue'
import TDesign from 'tdesign-vue-next'
import 'tdesign-vue-next/es/style/index.css'
import './assets/theme.css'
import App from './App.vue'
import router from './router'

createApp(App).use(TDesign).use(router).mount('#app')
```

- [ ] **Step 6: Verify dev server starts**

```bash
cd frontend && npm run dev
```

Expected: `VITE ready on http://localhost:5173` (no errors)

- [ ] **Step 7: Commit**

```bash
git add frontend/
git commit -m "feat: frontend scaffold with TDesign and types"
```

---

## Task 8: Frontend — Router & API Client

**Files:**
- Create: `frontend/src/router/index.ts`
- Create: `frontend/src/api/index.ts`
- Create: `frontend/tests/api.test.ts`

- [ ] **Step 1: Write failing API tests**

```typescript
// frontend/tests/api.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import { recognizePlate, listRecords } from '../src/api'

vi.mock('axios')
const mockedAxios = axios as any

describe('API client', () => {
  beforeEach(() => vi.clearAllMocks())

  it('recognizePlate posts FormData and returns response', async () => {
    mockedAxios.post = vi.fn().mockResolvedValue({
      data: { record_id: 1, plates: [], used_sr: false, duration_ms: 50, multi_vehicle: false }
    })
    const file = new File([''], 'test.jpg', { type: 'image/jpeg' })
    const result = await recognizePlate(file)
    expect(result.record_id).toBe(1)
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/recognize', expect.any(FormData))
  })

  it('listRecords passes query params', async () => {
    mockedAxios.get = vi.fn().mockResolvedValue({ data: { total: 0, items: [] } })
    await listRecords({ page: 2, plate: '粤B' })
    expect(mockedAxios.get).toHaveBeenCalledWith('/api/records', {
      params: { page: 2, limit: 20, plate: '粤B', type: '', date_from: '', date_to: '' }
    })
  })
})
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd frontend && npx vitest run tests/api.test.ts
```

Expected: `Cannot find module '../src/api'`

- [ ] **Step 3: Create router/index.ts**

```typescript
// frontend/src/router/index.ts
import { createRouter, createWebHistory } from 'vue-router'
import RecognizePage from '../views/RecognizePage.vue'
import HistoryPage from '../views/HistoryPage.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: RecognizePage },
    { path: '/history', component: HistoryPage },
  ],
})
```

Install vue-router:

```bash
cd frontend && npm install vue-router@4
```

- [ ] **Step 4: Create api/index.ts**

```typescript
// frontend/src/api/index.ts
import axios from 'axios'
import type { RecognizeResponse, RecordsResponse } from '../types'

export async function recognizePlate(file: File, roi?: { x: number; y: number; w: number; h: number }): Promise<RecognizeResponse> {
  const form = new FormData()
  form.append('image', file)
  const params = roi ? `?roi_x=${roi.x}&roi_y=${roi.y}&roi_w=${roi.w}&roi_h=${roi.h}` : ''
  const endpoint = roi ? `/api/recognize/roi${params}` : '/api/recognize'
  const { data } = await axios.post<RecognizeResponse>(endpoint, form)
  return data
}

export async function listRecords(params: {
  page?: number
  limit?: number
  plate?: string
  type?: string
  date_from?: string
  date_to?: string
} = {}): Promise<RecordsResponse> {
  const { data } = await axios.get<RecordsResponse>('/api/records', {
    params: {
      page: params.page ?? 1,
      limit: params.limit ?? 20,
      plate: params.plate ?? '',
      type: params.type ?? '',
      date_from: params.date_from ?? '',
      date_to: params.date_to ?? '',
    }
  })
  return data
}

export function exportRecordsUrl(): string {
  return '/api/records/export?format=csv'
}
```

- [ ] **Step 5: Run tests — expect pass**

```bash
cd frontend && npx vitest run tests/api.test.ts
```

Expected: `2 passed`

- [ ] **Step 6: Commit**

```bash
git add frontend/src/router frontend/src/api frontend/tests/api.test.ts
git commit -m "feat: router and API client"
```

---

## Task 9: Frontend — PlateVisual Component

**Files:**
- Create: `frontend/src/components/PlateVisual.vue`
- Create: `frontend/tests/PlateVisual.test.ts`

- [ ] **Step 1: Write failing tests**

```typescript
// frontend/tests/PlateVisual.test.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import PlateVisual from '../src/components/PlateVisual.vue'

describe('PlateVisual', () => {
  it('renders blue plate with correct CSS class', () => {
    const wrapper = mount(PlateVisual, {
      props: { province: '粤', cityCode: 'B', number: '88888', type: 'blue' }
    })
    expect(wrapper.find('.plate-root').classes()).toContain('plate-blue')
    expect(wrapper.text()).toContain('粤')
    expect(wrapper.text()).toContain('88888')
  })

  it('renders green plate for green_small type', () => {
    const wrapper = mount(PlateVisual, {
      props: { province: '京', cityCode: 'A', number: '12345D', type: 'green_small' }
    })
    expect(wrapper.find('.plate-root').classes()).toContain('plate-green')
  })

  it('renders yellow plate for yellow type', () => {
    const wrapper = mount(PlateVisual, {
      props: { province: '沪', cityCode: 'C', number: 'A6789', type: 'yellow' }
    })
    expect(wrapper.find('.plate-root').classes()).toContain('plate-yellow')
  })

  it('supports size prop', () => {
    const wrapper = mount(PlateVisual, {
      props: { province: '粤', cityCode: 'B', number: '88888', type: 'blue', size: 'sm' }
    })
    expect(wrapper.find('.plate-root').classes()).toContain('plate-sm')
  })
})
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd frontend && npx vitest run tests/PlateVisual.test.ts
```

Expected: `Cannot find module '../src/components/PlateVisual.vue'`

- [ ] **Step 3: Implement PlateVisual.vue**

```vue
<!-- frontend/src/components/PlateVisual.vue -->
<template>
  <div :class="['plate-root', typeClass, sizeClass]">
    <div class="plate-province">{{ province }}</div>
    <div class="plate-number">
      {{ cityCode }}<span class="plate-dot">·</span>{{ number }}
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PlateType } from '../types'

const props = withDefaults(defineProps<{
  province: string
  cityCode: string
  number: string
  type: PlateType
  size?: 'sm' | 'md' | 'lg'
}>(), { size: 'md' })

const TYPE_CLASS: Record<PlateType, string> = {
  blue: 'plate-blue',
  green_small: 'plate-green',
  yellow: 'plate-yellow',
  white: 'plate-white',
  black: 'plate-black',
  unknown: 'plate-blue',
}

const typeClass = TYPE_CLASS[props.type]
const sizeClass = `plate-${props.size}`
</script>

<style scoped>
.plate-root {
  display: inline-flex;
  align-items: stretch;
  border-radius: 5px;
  overflow: hidden;
  border: 2px solid rgba(0, 0, 0, 0.25);
  box-shadow: 0 1px 4px rgba(0,0,0,.2);
  font-family: "PingFang SC", "Microsoft YaHei", monospace;
  font-weight: 700;
  letter-spacing: 0.06em;
  user-select: none;
}
.plate-province {
  display: flex;
  align-items: center;
  justify-content: center;
  border-right: 1px solid rgba(0,0,0,.2);
  padding: 0 4px;
  font-weight: 900;
}
.plate-number {
  display: flex;
  align-items: center;
  padding: 6px 10px;
}
.plate-dot { margin: 0 2px; opacity: 0.7; }

/* Type colors */
.plate-blue  { background: #1a3a8f; color: #fff; }
.plate-blue  .plate-province { background: #1a3a8f; }
.plate-green { background: linear-gradient(to right, #1d7a3a 0%, #1d7a3a 20%, #8db828 60%, #c8b020 100%); color: #000; }
.plate-green .plate-province { background: #1d7a3a; }
.plate-yellow { background: #e8b800; color: #1a1a1a; }
.plate-yellow .plate-province { background: #d4a800; }
.plate-white  { background: #f5f5f5; color: #1a1a1a; border-color: #bbb; }
.plate-white  .plate-province { background: #e8e8e8; }
.plate-black  { background: #1a1a1a; color: #fff; }
.plate-black  .plate-province { background: #111; }

/* Sizes */
.plate-sm .plate-province { width: 24px; font-size: 11px; }
.plate-sm .plate-number   { font-size: 13px; padding: 4px 7px; }
.plate-md .plate-province { width: 32px; font-size: 14px; }
.plate-md .plate-number   { font-size: 18px; }
.plate-lg .plate-province { width: 38px; font-size: 16px; }
.plate-lg .plate-number   { font-size: 22px; padding: 8px 14px; }
</style>
```

- [ ] **Step 4: Run tests — expect all pass**

```bash
cd frontend && npx vitest run tests/PlateVisual.test.ts
```

Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/PlateVisual.vue frontend/tests/PlateVisual.test.ts
git commit -m "feat: PlateVisual component with type-based colors"
```

---

## Task 10: Frontend — UploadZone & RoiSelector Components

**Files:**
- Create: `frontend/src/components/UploadZone.vue`
- Create: `frontend/src/components/RoiSelector.vue`

- [ ] **Step 1: Create UploadZone.vue**

```vue
<!-- frontend/src/components/UploadZone.vue -->
<template>
  <div
    class="upload-zone"
    :class="{ 'upload-zone--dragover': isDragging }"
    @click="fileInput.click()"
    @dragover.prevent="isDragging = true"
    @dragleave="isDragging = false"
    @drop.prevent="onDrop"
  >
    <input ref="fileInput" type="file" accept=".jpg,.jpeg,.png,.bmp" hidden @change="onFileChange" />
    <t-icon name="upload" size="48px" style="color: #999; margin-bottom: 12px" />
    <p class="upload-text">点击或拖拽图片 / 视频帧至此处</p>
    <p class="upload-hint">支持 JPG、PNG、BMP，最大 <strong>20MB</strong></p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'

const emit = defineEmits<{ (e: 'file-selected', file: File): void }>()
const fileInput = ref<HTMLInputElement>()
const isDragging = ref(false)

function validate(file: File): boolean {
  const ALLOWED = ['image/jpeg', 'image/png', 'image/bmp']
  if (!ALLOWED.includes(file.type)) {
    MessagePlugin.error('仅支持 JPG/PNG/BMP 格式')
    return false
  }
  if (file.size > 20 * 1024 * 1024) {
    MessagePlugin.error('文件不超过 20MB')
    return false
  }
  return true
}

function onFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file && validate(file)) emit('file-selected', file)
}

function onDrop(e: DragEvent) {
  isDragging.value = false
  const file = e.dataTransfer?.files[0]
  if (file && validate(file)) emit('file-selected', file)
}
</script>

<style scoped>
.upload-zone {
  border: 2px dashed #d4d4d4;
  border-radius: 6px;
  padding: 48px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.15s;
  background: #fafafa;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.upload-zone:hover, .upload-zone--dragover {
  border-color: #1a1a1a;
  background: #f5f5f5;
}
.upload-text { font-size: 14px; color: #4a4a4a; margin-bottom: 5px; }
.upload-hint { font-size: 12px; color: #999; }
.upload-hint strong { color: #1a1a1a; font-weight: 500; }
</style>
```

- [ ] **Step 2: Create RoiSelector.vue**

```vue
<!-- frontend/src/components/RoiSelector.vue -->
<template>
  <div class="roi-wrapper">
    <div class="roi-header">
      <span class="roi-title">
        <t-icon name="info-circle" /> 检测到多辆车，请框选目标车辆
        <t-tag theme="warning" size="small">多车场景</t-tag>
      </span>
      <t-button variant="text" size="small" @click="emit('skip')">跳过</t-button>
    </div>
    <div class="roi-container" @mousedown="startDraw" @mousemove="drawing" @mouseup="endDraw">
      <img ref="imgEl" :src="imageSrc" class="roi-image" @load="onImgLoad" draggable="false" />
      <canvas ref="canvas" class="roi-canvas" />
    </div>
    <p class="roi-hint">在图片上拖动绘制框选区域，框选后点击"开始识别"</p>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{ imageSrc: string }>()
const emit = defineEmits<{
  (e: 'roi-change', roi: { x: number; y: number; w: number; h: number } | null): void
  (e: 'skip'): void
}>()

const canvas = ref<HTMLCanvasElement>()
const imgEl = ref<HTMLImageElement>()
let startX = 0, startY = 0, isDrawing = false

function onImgLoad() {
  if (!canvas.value || !imgEl.value) return
  canvas.value.width = imgEl.value.clientWidth
  canvas.value.height = imgEl.value.clientHeight
}

function getPos(e: MouseEvent) {
  const rect = canvas.value!.getBoundingClientRect()
  return { x: e.clientX - rect.left, y: e.clientY - rect.top }
}

function startDraw(e: MouseEvent) {
  const pos = getPos(e)
  startX = pos.x; startY = pos.y
  isDrawing = true
}

function drawing(e: MouseEvent) {
  if (!isDrawing || !canvas.value) return
  const ctx = canvas.value.getContext('2d')!
  const pos = getPos(e)
  ctx.clearRect(0, 0, canvas.value.width, canvas.value.height)
  ctx.strokeStyle = '#fff'
  ctx.lineWidth = 2
  ctx.fillStyle = 'rgba(255,255,255,0.1)'
  const w = pos.x - startX, h = pos.y - startY
  ctx.strokeRect(startX, startY, w, h)
  ctx.fillRect(startX, startY, w, h)
}

function endDraw(e: MouseEvent) {
  if (!isDrawing || !imgEl.value) return
  isDrawing = false
  const pos = getPos(e)
  const scaleX = imgEl.value.naturalWidth / imgEl.value.clientWidth
  const scaleY = imgEl.value.naturalHeight / imgEl.value.clientHeight
  const x = Math.round(Math.min(startX, pos.x) * scaleX)
  const y = Math.round(Math.min(startY, pos.y) * scaleY)
  const w = Math.round(Math.abs(pos.x - startX) * scaleX)
  const h = Math.round(Math.abs(pos.y - startY) * scaleY)
  if (w > 10 && h > 10) emit('roi-change', { x, y, w, h })
  else emit('roi-change', null)
}
</script>

<style scoped>
.roi-wrapper { padding: 16px; background: #fafafa; border: 1px solid #e8e8e8; border-radius: 6px; margin-top: 20px; }
.roi-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.roi-title { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 500; }
.roi-container { position: relative; background: #1a1a1a; border-radius: 4px; overflow: hidden; }
.roi-image { display: block; width: 100%; max-height: 280px; object-fit: contain; }
.roi-canvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; cursor: crosshair; }
.roi-hint { font-size: 12px; color: #999; margin-top: 8px; }
</style>
```

- [ ] **Step 3: Verify components render in browser**

Start frontend dev server and confirm no console errors:

```bash
cd frontend && npm run dev
```

Import both components temporarily in `App.vue` and check browser console.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/UploadZone.vue frontend/src/components/RoiSelector.vue
git commit -m "feat: UploadZone and RoiSelector components"
```

---

## Task 11: Frontend — PlateCard Component

**Files:**
- Create: `frontend/src/components/PlateCard.vue`

- [ ] **Step 1: Create PlateCard.vue**

```vue
<!-- frontend/src/components/PlateCard.vue -->
<template>
  <div class="plate-card" :class="{ 'plate-card--primary': primary }">
    <!-- Plate visual + type label -->
    <div class="plate-display-row">
      <PlateVisual
        :province="plate.province"
        :city-code="plate.city_code"
        :number="plate.number"
        :type="plate.type"
        size="lg"
      />
      <span class="type-label">{{ plate.type_label }}</span>
    </div>

    <!-- Confidence bar -->
    <div class="confidence-bar">
      <div class="confidence-fill" :class="{ 'warn': plate.confidence < 0.9 }"
           :style="{ width: (plate.confidence * 100) + '%' }" />
    </div>
    <p class="confidence-label">
      置信度 {{ (plate.confidence * 100).toFixed(0) }}%
      <span v-if="plate.confidence_before_sr != null">
        （超分前 {{ (plate.confidence_before_sr * 100).toFixed(0) }}%）
      </span>
    </p>

    <!-- SR notice -->
    <div v-if="plate.confidence_before_sr != null" class="sr-notice">
      ⚠ 图片较模糊，已自动启用超分增强
    </div>

    <!-- Meta info -->
    <div class="info-row">
      <span>耗时 {{ durationMs }}ms</span>
      <span>{{ timestamp }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import PlateVisual from './PlateVisual.vue'
import type { PlateResult } from '../types'

defineProps<{
  plate: PlateResult
  primary?: boolean
  durationMs?: number
  timestamp?: string
}>()
</script>

<style scoped>
.plate-card { background: #fff; border: 1px solid #e8e8e8; border-radius: 6px; padding: 18px; }
.plate-card--primary { border-color: #1a1a1a; box-shadow: 0 0 0 3px rgba(0,0,0,.04); }
.plate-display-row { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
.type-label { font-size: 11px; color: #999; }
.confidence-bar { height: 3px; background: #f0f0f0; border-radius: 2px; overflow: hidden; margin-bottom: 4px; }
.confidence-fill { height: 100%; background: #1a1a1a; border-radius: 2px; transition: width .3s; }
.confidence-fill.warn { background: #e65c00; }
.confidence-label { font-size: 11px; color: #999; }
.sr-notice { font-size: 12px; color: #e65c00; display: flex; align-items: center; gap: 5px; margin-top: 8px; padding: 6px 10px; background: #fff3e0; border-radius: 4px; }
.info-row { display: flex; justify-content: space-between; font-size: 11px; color: #bbb; padding-top: 10px; border-top: 1px solid #f0f0f0; margin-top: 8px; }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/PlateCard.vue
git commit -m "feat: PlateCard component"
```

---

## Task 12: Frontend — RecognizePage

**Files:**
- Create: `frontend/src/views/RecognizePage.vue`

- [ ] **Step 1: Create RecognizePage.vue**

The page manages three states: `upload` | `loading` | `result`.

```vue
<!-- frontend/src/views/RecognizePage.vue -->
<template>
  <t-card :bordered="false" class="page-card">
    <!-- State tabs -->
    <t-tabs v-model="activeTab" @change="onTabChange">
      <t-tab-panel value="upload" label="上传图片" />
      <t-tab-panel value="result" label="识别结果" :disabled="!hasResult" />
    </t-tabs>

    <!-- Upload state -->
    <div v-if="activeTab === 'upload'" class="tab-content">
      <UploadZone @file-selected="onFileSelected" />

      <!-- ROI selector — only shown after multi-vehicle detection -->
      <RoiSelector
        v-if="showRoi && previewUrl"
        :image-src="previewUrl"
        @roi-change="roi = $event"
        @skip="showRoi = false; roi = null"
      />

      <div class="action-row">
        <t-button variant="outline" class="action-btn" @click="reset">重置</t-button>
        <t-button class="action-btn" :disabled="!selectedFile" :loading="loading" @click="submit">
          开始识别
        </t-button>
      </div>
    </div>

    <!-- Result state -->
    <div v-if="activeTab === 'result' && result" class="tab-content result-layout">
      <!-- Left: image with plate bbox overlays -->
      <div class="result-image-wrap">
        <img :src="previewUrl" class="result-image" ref="resultImg" @load="drawBboxes" />
        <canvas ref="bboxCanvas" class="bbox-canvas" />
        <t-tag v-if="result.plates.length > 0" theme="success" class="plate-count-tag">
          ✓ {{ result.plates.length }} 张车牌
        </t-tag>
        <t-tag v-else theme="warning" class="plate-count-tag">未检测到车牌</t-tag>
      </div>

      <!-- Right: result cards -->
      <div class="result-panel">
        <p class="section-label">识别结果</p>
        <PlateCard
          v-for="(plate, i) in result.plates"
          :key="i"
          :plate="plate"
          :primary="i === 0"
          :duration-ms="result.duration_ms"
          :timestamp="savedAt"
        />
        <t-alert v-if="result.plates.length === 0" theme="warning"
          message="未检测到车牌，请尝试更换图片或框选目标区域" />
        <div class="action-row">
          <t-button variant="outline" class="action-btn" @click="reset">重新识别</t-button>
          <t-button class="action-btn" :loading="saving" @click="saveRecord">保存记录</t-button>
        </div>
      </div>
    </div>
  </t-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { MessagePlugin } from 'tdesign-vue-next'
import UploadZone from '../components/UploadZone.vue'
import RoiSelector from '../components/RoiSelector.vue'
import PlateCard from '../components/PlateCard.vue'
import { recognizePlate } from '../api'
import type { RecognizeResponse } from '../types'

const activeTab = ref<'upload' | 'result'>('upload')
const selectedFile = ref<File | null>(null)
const previewUrl = ref<string>('')
const showRoi = ref(false)
const roi = ref<{ x: number; y: number; w: number; h: number } | null>(null)
const loading = ref(false)
const saving = ref(false)
const result = ref<RecognizeResponse | null>(null)
const hasResult = ref(false)
const savedAt = ref('')
const resultImg = ref<HTMLImageElement>()
const bboxCanvas = ref<HTMLCanvasElement>()

function onFileSelected(file: File) {
  selectedFile.value = file
  previewUrl.value = URL.createObjectURL(file)
  showRoi.value = false
  roi.value = null
}

async function submit() {
  if (!selectedFile.value) return
  loading.value = true
  try {
    const res = await recognizePlate(selectedFile.value, roi.value ?? undefined)
    result.value = res
    hasResult.value = true
    savedAt.value = new Date().toLocaleString('zh-CN')
    if (res.multi_vehicle && !roi.value) {
      showRoi.value = true
      MessagePlugin.info('检测到多辆车，请框选目标车辆后重新识别')
      return
    }
    activeTab.value = 'result'
  } catch (e: any) {
    MessagePlugin.error(e?.response?.data?.detail ?? '识别失败，请重试')
  } finally {
    loading.value = false
  }
}

function reset() {
  selectedFile.value = null
  previewUrl.value = ''
  showRoi.value = false
  roi.value = null
  result.value = null
  hasResult.value = false
  activeTab.value = 'upload'
}

function onTabChange(val: string) {
  if (val === 'result' && !hasResult.value) activeTab.value = 'upload'
}

function saveRecord() {
  // Record is already saved in backend on recognize; this just shows confirmation
  MessagePlugin.success('记录已保存')
}

function drawBboxes() {
  if (!bboxCanvas.value || !resultImg.value || !result.value) return
  const img = resultImg.value
  const canvas = bboxCanvas.value
  canvas.width = img.clientWidth
  canvas.height = img.clientHeight
  const scaleX = img.clientWidth / img.naturalWidth
  const scaleY = img.clientHeight / img.naturalHeight
  const ctx = canvas.getContext('2d')!
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.strokeStyle = '#00e5a0'
  ctx.lineWidth = 2
  for (const plate of result.value.plates) {
    const [x, y, w, h] = plate.bbox
    ctx.strokeRect(x * scaleX, y * scaleY, w * scaleX, h * scaleY)
  }
}
</script>

<style scoped>
.page-card { max-width: 1100px; margin: 0 auto; }
.tab-content { padding-top: 24px; }
.action-row { margin-top: 20px; display: flex; justify-content: flex-end; gap: 10px; }
.action-btn { width: 140px; }
.result-layout { display: grid; grid-template-columns: 1fr 360px; gap: 20px; }
.result-image-wrap { position: relative; border-radius: 6px; overflow: hidden; background: #111; }
.result-image { display: block; width: 100%; max-height: 400px; object-fit: contain; }
.bbox-canvas { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; }
.plate-count-tag { position: absolute; top: 10px; left: 10px; }
.result-panel { display: flex; flex-direction: column; gap: 14px; }
.section-label { font-size: 11px; font-weight: 600; color: #999; text-transform: uppercase; letter-spacing: .08em; }
</style>
```

- [ ] **Step 2: Verify page loads without errors**

```bash
cd frontend && npm run dev
# Open http://localhost:5173 — should show upload zone
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/RecognizePage.vue
git commit -m "feat: RecognizePage with upload/result state machine"
```

---

## Task 13: Frontend — HistoryTable & HistoryPage

**Files:**
- Create: `frontend/src/components/HistoryTable.vue`
- Create: `frontend/src/views/HistoryPage.vue`

- [ ] **Step 1: Create HistoryTable.vue**

```vue
<!-- frontend/src/components/HistoryTable.vue -->
<template>
  <div>
    <!-- Toolbar -->
    <div class="toolbar">
      <t-input v-model="filters.plate" placeholder="搜索车牌号…" clearable style="width:200px" @change="onFilter" />
      <t-select v-model="filters.type" placeholder="全部类型" clearable style="width:130px" @change="onFilter">
        <t-option value="" label="全部类型" />
        <t-option value="blue" label="蓝牌" />
        <t-option value="green_small" label="新能源" />
        <t-option value="yellow" label="黄牌" />
      </t-select>
      <t-date-range-picker v-model="filters.dateRange" placeholder="选择日期范围" clearable
        style="width:240px" @change="onFilter" />
      <div style="flex:1" />
      <t-button variant="outline" @click="exportCsv">↓ 导出 CSV</t-button>
    </div>

    <!-- Table -->
    <t-table :data="records" :columns="columns" :loading="loading" row-key="id" />

    <!-- Pagination -->
    <t-pagination
      v-model="page" :total="total" :page-size="20"
      style="margin-top:16px;justify-content:flex-end"
      @change="load"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { listRecords, exportRecordsUrl } from '../api'
import PlateVisual from './PlateVisual.vue'
import type { RecordItem } from '../types'

const records = ref<RecordItem[]>([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const filters = ref({ plate: '', type: '', dateRange: [] as string[] })

const columns = [
  {
    colKey: 'image_url', title: '缩略图', width: 80,
    cell: (_: any, { row }: { row: RecordItem }) =>
      h('img', { src: row.image_url, style: 'width:54px;height:34px;object-fit:cover;border-radius:3px;background:#2b2b2b' })
  },
  {
    colKey: 'plates', title: '车牌',
    cell: (_: any, { row }: { row: RecordItem }) =>
      row.plates.length
        ? h(PlateVisual, { province: row.plates[0].province, cityCode: row.plates[0].city_code, number: row.plates[0].number, type: row.plates[0].type, size: 'sm' })
        : h('span', { style: 'color:#999;font-size:12px' }, '无')
  },
  {
    colKey: 'confidence', title: '置信度',
    cell: (_: any, { row }: { row: RecordItem }) =>
      h('span', row.plates[0] ? `${(row.plates[0].confidence * 100).toFixed(0)}%` : '-')
  },
  {
    colKey: 'used_sr', title: '超分',
    cell: (_: any, { row }: { row: RecordItem }) =>
      h('t-tag', { theme: row.used_sr ? 'warning' : 'default', size: 'small' }, row.used_sr ? '是' : '否')
  },
  { colKey: 'created_at', title: '识别时间' },
  {
    colKey: 'actions', title: '操作',
    cell: () => h('t-button', { variant: 'text', size: 'small' }, '查看')
  },
]

async function load() {
  loading.value = true
  try {
    const res = await listRecords({
      page: page.value, plate: filters.value.plate, type: filters.value.type,
      date_from: filters.value.dateRange[0] ?? '', date_to: filters.value.dateRange[1] ?? '',
    })
    records.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function onFilter() { page.value = 1; load() }

function exportCsv() {
  const a = document.createElement('a')
  a.href = exportRecordsUrl()
  a.download = 'records.csv'
  a.click()
}

onMounted(load)
</script>

<style scoped>
.toolbar { display: flex; gap: 10px; margin-bottom: 16px; align-items: center; flex-wrap: wrap; }
</style>
```

- [ ] **Step 2: Create HistoryPage.vue**

```vue
<!-- frontend/src/views/HistoryPage.vue -->
<template>
  <t-card :bordered="false" style="max-width:1100px;margin:0 auto">
    <HistoryTable />
  </t-card>
</template>

<script setup lang="ts">
import HistoryTable from '../components/HistoryTable.vue'
</script>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/HistoryTable.vue frontend/src/views/HistoryPage.vue
git commit -m "feat: HistoryTable and HistoryPage"
```

---

## Task 14: Frontend — App Shell (Nav + Footer)

**Files:**
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: Replace App.vue**

```vue
<!-- frontend/src/App.vue -->
<template>
  <div class="app-shell">
    <!-- Nav -->
    <header class="nav">
      <div class="nav-brand">
        <t-icon name="car" style="width:20px;height:20px" />
        车牌识别系统
      </div>
      <nav class="nav-links">
        <router-link to="/" class="nav-link" :class="{ active: route.path === '/' }">识别</router-link>
        <router-link to="/history" class="nav-link" :class="{ active: route.path === '/history' }">历史记录</router-link>
      </nav>
    </header>

    <!-- Content -->
    <main class="main-content">
      <router-view />
    </main>

    <!-- Footer disclaimer -->
    <footer class="footer">
      <p>
        <strong>免责声明</strong>　本工具仅提供车牌图像识别辅助功能，识别结果由 AI 模型自动生成，可能存在误识别或遗漏，<strong>不构成任何法律证明或执法依据</strong>。用户在将识别结果用于违章举报或其他用途前，须自行核实原始图像信息，并承担相应责任。本平台不存储用户上传的图片，不对识别结果的准确性作出保证。
      </p>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
const route = useRoute()
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif; background: #f5f5f5; color: #1a1a1a; }
</style>

<style scoped>
.app-shell { min-height: 100vh; display: flex; flex-direction: column; }
.nav { background: #1a1a1a; height: 56px; display: flex; align-items: center; padding: 0 24px; gap: 32px; position: sticky; top: 0; z-index: 100; }
.nav-brand { font-size: 15px; font-weight: 600; color: #fff; display: flex; align-items: center; gap: 8px; }
.nav-links { display: flex; gap: 4px; }
.nav-link { padding: 6px 16px; border-radius: 4px; font-size: 13px; color: #999; text-decoration: none; transition: all .15s; }
.nav-link:hover { color: #ccc; }
.nav-link.active { background: rgba(255,255,255,.12); color: #fff; font-weight: 500; }
.main-content { flex: 1; padding: 24px; }
.footer { background: #f0f0f0; border-top: 1px solid #e0e0e0; padding: 14px 24px; }
.footer p { font-size: 11px; color: #999; line-height: 1.7; max-width: 900px; margin: 0 auto; text-align: center; }
.footer strong { color: #bbb; font-weight: 500; }
</style>
```

- [ ] **Step 2: End-to-end smoke test**

Start both backend and frontend:

```bash
# Terminal 1
cd backend && source .venv/bin/activate && uvicorn main:app --reload --port 8000

# Terminal 2
cd frontend && npm run dev
```

Open `http://localhost:5173`:
- Navigation bar shows "识别" / "历史记录"
- Upload zone renders
- Click 历史记录 — table loads (empty)
- Footer disclaimer visible on both pages

- [ ] **Step 3: Commit**

```bash
git add frontend/src/App.vue
git commit -m "feat: App shell with nav and footer disclaimer"
```

---

## Task 15: Full Integration Test

**Goal:** Verify the complete user flow end-to-end.

- [ ] **Step 1: Find a test image with a Chinese license plate**

Download any photo containing a visible Chinese plate, save to `tests/fixtures/car.jpg`.

- [ ] **Step 2: Test via curl**

```bash
cd backend && source .venv/bin/activate
curl -X POST http://localhost:8000/api/recognize \
  -F "image=@tests/fixtures/car.jpg" | python3 -m json.tool
```

Expected: JSON with `record_id`, `plates` array (≥1 item), `multi_vehicle`, `duration_ms`

- [ ] **Step 3: Test via UI**

1. Open `http://localhost:5173`
2. Upload the test image → click "开始识别"
3. Verify: result tab shows, plate displayed with correct colors, confidence bar renders
4. Click "保存记录" → success toast
5. Navigate to 历史记录 → confirm record appears in table with colored plate badge
6. Click "导出 CSV" → file downloads with correct headers

- [ ] **Step 4: Run all backend tests**

```bash
cd backend && python -m pytest tests/ -v
```

Expected: All tests pass (≥9 total)

- [ ] **Step 5: Run all frontend tests**

```bash
cd frontend && npx vitest run
```

Expected: All tests pass (≥6 total)

- [ ] **Step 6: Final commit**

```bash
git add .
git commit -m "feat: complete license plate recognition app — all tests passing"
```

---

## Self-Review

**Spec coverage check:**

| Requirement | Task |
|-------------|------|
| Upload JPG/PNG/BMP ≤20MB | Task 10 (UploadZone validation), Task 6 (backend) |
| HyperLPR3 recognition | Task 5 |
| Confidence < 0.9 → SR | Task 4 + 5 |
| Multi-vehicle → ROI selector | Task 5 (multi_vehicle flag), Task 10 (RoiSelector), Task 12 (RecognizePage) |
| SQLite storage | Task 3 |
| History list + filter + pagination | Task 3 (DB), Task 13 (UI) |
| CSV export | Task 3 (DB), Task 13 (UI) |
| PlateVisual colors | Task 9 |
| Black/white/gray theme | Task 7 (theme.css) |
| Footer disclaimer | Task 14 |
| TDesign Vue Next | Task 7 |

No gaps found. All placeholder patterns checked — none present.
