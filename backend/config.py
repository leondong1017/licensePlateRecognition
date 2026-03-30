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
