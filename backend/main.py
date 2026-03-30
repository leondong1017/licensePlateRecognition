# backend/main.py
import os, uuid
import cv2
import numpy as np
from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
import io

from config import config
from database import Database
from recognize import recognize_service
from models import RecognizeResponse, RecordsResponse, RecordItem, PlateResult

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

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/bmp"}

async def _read_image(file: UploadFile):
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
    os.makedirs(os.path.dirname(path), exist_ok=True)
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

# Add static file serving for images (must be after route definitions)
if os.path.exists(config.images_dir):
    app.mount("/api/images", StaticFiles(directory=config.images_dir), name="images")
