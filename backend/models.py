# backend/models.py
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
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
    text: str
    province: str
    city_code: str
    number: str
    type: PlateType
    type_label: str
    confidence: float
    confidence_before_sr: Optional[float] = None
    bbox: List[int]

class RecognizeResponse(BaseModel):
    record_id: int
    plates: List[PlateResult]
    used_sr: bool
    duration_ms: int
    multi_vehicle: bool

class RecordItem(BaseModel):
    id: int
    created_at: str
    plates: List[PlateResult]
    used_sr: bool
    image_url: str
    user_feedback: Optional[Literal["accurate", "inaccurate"]] = None


class FeedbackPatchRequest(BaseModel):
    feedback: Optional[Literal["accurate", "inaccurate"]] = Field(
        default=None,
        description="用户反馈；传 null 表示清除",
    )

class RecordsResponse(BaseModel):
    total: int
    items: List[RecordItem]

class ConfirmRequest(BaseModel):
    record_id: int
    plate_index: int
