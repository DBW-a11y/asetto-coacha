"""SQLite-based session and lap metadata storage."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .models import Lap, Session


class SessionStore:
    """Manages session and lap metadata in SQLite."""

    def __init__(self, db_path: Path):
        self._db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                track TEXT NOT NULL,
                car TEXT NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                num_laps INTEGER DEFAULT 0,
                best_lap_time_ms INTEGER
            );
            CREATE TABLE IF NOT EXISTS laps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL REFERENCES sessions(id),
                lap_number INTEGER NOT NULL,
                lap_time_ms INTEGER NOT NULL,
                is_valid BOOLEAN DEFAULT 1,
                sector1_ms INTEGER,
                sector2_ms INTEGER,
                sector3_ms INTEGER,
                UNIQUE(session_id, lap_number)
            );
            CREATE INDEX IF NOT EXISTS idx_laps_session ON laps(session_id);
        """)

    def create_session(self, track: str, car: str) -> str:
        session_id = uuid.uuid4().hex[:12]
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            "INSERT INTO sessions (id, track, car, started_at) VALUES (?, ?, ?, ?)",
            (session_id, track, car, now),
        )
        self._conn.commit()
        return session_id

    def end_session(self, session_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            "UPDATE sessions SET ended_at = ? WHERE id = ?",
            (now, session_id),
        )
        self._conn.commit()

    def add_lap(
        self,
        session_id: str,
        lap_number: int,
        lap_time_ms: int,
        is_valid: bool = True,
        sector1_ms: int | None = None,
        sector2_ms: int | None = None,
        sector3_ms: int | None = None,
    ) -> None:
        self._conn.execute(
            """INSERT OR REPLACE INTO laps
               (session_id, lap_number, lap_time_ms, is_valid, sector1_ms, sector2_ms, sector3_ms)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (session_id, lap_number, lap_time_ms, is_valid, sector1_ms, sector2_ms, sector3_ms),
        )
        # Update session stats
        self._conn.execute(
            """UPDATE sessions SET
               num_laps = (SELECT COUNT(*) FROM laps WHERE session_id = ?),
               best_lap_time_ms = (SELECT MIN(lap_time_ms) FROM laps
                                   WHERE session_id = ? AND is_valid = 1)
               WHERE id = ?""",
            (session_id, session_id, session_id),
        )
        self._conn.commit()

    def get_session(self, session_id: str) -> Session | None:
        row = self._conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if not row:
            return None
        return self._row_to_session(row)

    def list_sessions(self, limit: int = 50) -> list[Session]:
        rows = self._conn.execute(
            "SELECT * FROM sessions ORDER BY started_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [self._row_to_session(r) for r in rows]

    def get_laps(self, session_id: str) -> list[Lap]:
        rows = self._conn.execute(
            "SELECT * FROM laps WHERE session_id = ? ORDER BY lap_number",
            (session_id,),
        ).fetchall()
        return [self._row_to_lap(r) for r in rows]

    def get_lap(self, session_id: str, lap_number: int) -> Lap | None:
        row = self._conn.execute(
            "SELECT * FROM laps WHERE session_id = ? AND lap_number = ?",
            (session_id, lap_number),
        ).fetchone()
        return self._row_to_lap(row) if row else None

    @staticmethod
    def _row_to_session(row: sqlite3.Row) -> Session:
        return Session(
            id=row["id"],
            track=row["track"],
            car=row["car"],
            started_at=datetime.fromisoformat(row["started_at"]),
            ended_at=datetime.fromisoformat(row["ended_at"]) if row["ended_at"] else None,
            num_laps=row["num_laps"],
            best_lap_time_ms=row["best_lap_time_ms"],
        )

    @staticmethod
    def _row_to_lap(row: sqlite3.Row) -> Lap:
        return Lap(
            id=row["id"],
            session_id=row["session_id"],
            lap_number=row["lap_number"],
            lap_time_ms=row["lap_time_ms"],
            is_valid=bool(row["is_valid"]),
            sector1_ms=row["sector1_ms"],
            sector2_ms=row["sector2_ms"],
            sector3_ms=row["sector3_ms"],
        )

    def close(self) -> None:
        self._conn.close()
