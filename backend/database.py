import sqlite3, json, os, csv, io
from typing import Optional, List, Dict, Any
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

    def insert_record(self, image_path: str, plates: List[PlateResult], used_sr: bool) -> int:
        plates_json = json.dumps([p.model_dump() for p in plates], ensure_ascii=False)
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO records (image_path, plates, used_sr) VALUES (?, ?, ?)",
                (image_path, plates_json, int(used_sr))
            )
            return cur.lastrowid

    def get_record(self, record_id: int) -> Optional[Dict[str, Any]]:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM records WHERE id=?", (record_id,)).fetchone()
        return self._row_to_dict(row) if row else None

    def list_records(self, page: int = 1, limit: int = 20,
                     plate_filter: str = "", type_filter: str = "",
                     date_from: str = "", date_to: str = "") -> Dict[str, Any]:
        where, params = [], []
        if plate_filter:
            where.append("plates LIKE ?")
            params.append(f"%{plate_filter}%")
        if type_filter:
            where.append("plates LIKE ?")
            params.append(f"%{type_filter}%")
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

    def delete_record(self, record_id: int):
        """Delete a record and return its image_path, or None if not found."""
        with self._conn() as conn:
            row = conn.execute("SELECT image_path FROM records WHERE id=?", (record_id,)).fetchone()
            if not row:
                return None
            conn.execute("DELETE FROM records WHERE id=?", (record_id,))
            return row["image_path"]

    def _row_to_dict(self, row) -> Dict[str, Any]:
        d = dict(row)
        d["plates"] = json.loads(d["plates"])
        d["used_sr"] = bool(d["used_sr"])
        return d
