# backend/config.py
import os
from dataclasses import dataclass, field

@dataclass
class Config:
    confidence_threshold: float = field(default_factory=lambda: float(os.getenv("CONFIDENCE_THRESHOLD", "0.95")))
    sr_timeout_seconds: int = field(default_factory=lambda: int(os.getenv("SR_TIMEOUT_SECONDS", "30")))
    images_dir: str = field(default_factory=lambda: os.getenv("IMAGES_DIR", "images"))
    db_path: str = field(default_factory=lambda: os.getenv("DB_PATH", "lpr.db"))
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))

config = Config()
