"""SQLite persistence for named users and BMI history."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


class StorageError(Exception):
    """Raised when a database read or write fails."""


@dataclass(frozen=True)
class BMIRecord:
    id: int
    user_id: int
    user_name: str
    weight: float
    height: float
    bmi: float
    category: str
    recorded_at: str


class BMIStorage:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else Path(__file__).resolve().parent / "bmi_history.db"
        self._init_schema()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
        except sqlite3.Error as exc:
            raise StorageError(f"Could not open the BMI database: {exc}") from exc
        try:
            yield conn
            conn.commit()
        except sqlite3.Error:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        try:
            with self._connect() as conn:
                conn.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL COLLATE NOCASE UNIQUE
                    );

                    CREATE TABLE IF NOT EXISTS records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        weight REAL NOT NULL,
                        height REAL NOT NULL,
                        bmi REAL NOT NULL,
                        category TEXT NOT NULL,
                        recorded_at TEXT NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    );
                    """
                )
        except sqlite3.Error as exc:
            raise StorageError(f"Could not initialise the BMI database: {exc}") from exc

    def list_users(self) -> list[tuple[int, str]]:
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT id, name FROM users ORDER BY name COLLATE NOCASE"
                ).fetchall()
            return [(int(row["id"]), str(row["name"])) for row in rows]
        except sqlite3.Error as exc:
            raise StorageError(f"Could not load users: {exc}") from exc

    def get_or_create_user(self, name: str) -> tuple[int, str]:
        cleaned = (name or "").strip()
        if not cleaned:
            raise StorageError("A user name is required before saving a record.")
        try:
            with self._connect() as conn:
                existing = conn.execute(
                    "SELECT id, name FROM users WHERE name = ? COLLATE NOCASE",
                    (cleaned,),
                ).fetchone()
                if existing:
                    return int(existing["id"]), str(existing["name"])
                cursor = conn.execute("INSERT INTO users (name) VALUES (?)", (cleaned,))
                return int(cursor.lastrowid), cleaned
        except sqlite3.Error as exc:
            raise StorageError(f"Could not save the user '{cleaned}': {exc}") from exc

    def save_record(
        self,
        user_name: str,
        weight: float,
        height: float,
        bmi: float,
        category: str,
        recorded_at: str | None = None,
    ) -> BMIRecord:
        timestamp = recorded_at or datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        user_id, stored_name = self.get_or_create_user(user_name)
        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO records (user_id, weight, height, bmi, category, recorded_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, weight, height, bmi, category, timestamp),
                )
                record_id = int(cursor.lastrowid)
            return BMIRecord(
                id=record_id,
                user_id=user_id,
                user_name=stored_name,
                weight=weight,
                height=height,
                bmi=bmi,
                category=category,
                recorded_at=timestamp,
            )
        except sqlite3.Error as ext:
            raise StorageError(f"Could not save the BMI record: {ext}") from ext

    def records_for_user(self, user_id: int) -> list[BMIRecord]:
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT r.id, r.user_id, u.name AS user_name, r.weight, r.height,
                           r.bmi, r.category, r.recorded_at
                    FROM records r
                    JOIN users u ON u.id = r.user_id
                    WHERE r.user_id = ?
                    ORDER BY r.recorded_at ASC, r.id ASC
                    """,
                    (user_id,),
                ).fetchall()
            return [self._row_to_record(row) for row in rows]
        except sqlite3.Error as exc:
            raise StorageError(f"Could not load BMI history: {exc}") from exc

    def all_records(self) -> list[BMIRecord]:
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT r.id, r.user_id, u.name AS user_name, r.weight, r.height,
                           r.bmi, r.category, r.recorded_at
                    FROM records r
                    JOIN users u ON u.id = r.user_id
                    ORDER BY r.recorded_at DESC, r.id DESC
                    """
                ).fetchall()
            return [self._row_to_record(row) for row in rows]
        except sqlite3.Error as exc:
            raise StorageError(f"Could not load BMI records: {exc}") from exc

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> BMIRecord:
        return BMIRecord(
            id=int(row["id"]),
            user_id=int(row["user_id"]),
            user_name=str(row["user_name"]),
            weight=float(row["weight"]),
            height=float(row["height"]),
            bmi=float(row["bmi"]),
            category=str(row["category"]),
            recorded_at=str(row["recorded_at"]),
        )

    def users_with_history(self) -> list[tuple[int, str]]:
        return self.list_users()
