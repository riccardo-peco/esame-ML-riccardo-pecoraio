"""
repository/sqlite_repo.py — SQLite implementation of AbstractEventRepository.

REQ-EVT-S01: persists data in a SQLite database file in DATA_DIR using only the
             Python standard library sqlite3 module, and exposes the same
             interface as all other backends so that business logic and route
             handlers need no changes when this backend is active.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional

from domain.models import Event
from repository.base import AbstractEventRepository

_DBFILE = "events.db"

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS events (
    id           TEXT PRIMARY KEY,
    title        TEXT NOT NULL,
    description  TEXT,
    organizer_id TEXT NOT NULL,
    venue        TEXT NOT NULL,
    city         TEXT NOT NULL,
    start_date   TEXT NOT NULL,
    end_date     TEXT NOT NULL,
    capacity     INTEGER NOT NULL,
    price        REAL NOT NULL,
    status       TEXT NOT NULL,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
)
"""


class SqliteEventRepository(AbstractEventRepository):
    """
    SQLite-backed Event repository that persists all data in
    ``<data_dir>/events.db``.

    Each public method opens a fresh connection and closes it on return, which
    keeps the implementation simple and avoids file-lock issues on Windows
    (matching the json backend's approach of reading fresh on every op).
    """

    def __init__(self, data_dir: str) -> None:
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._data_dir / _DBFILE
        # Ensure the table exists
        conn = self._connect()
        try:
            conn.execute(_CREATE_TABLE_SQL)
            conn.commit()
        finally:
            conn.close()

    # ---------------------------------------------------------------- helpers

    def _connect(self) -> sqlite3.Connection:
        """Open and return a new SQLite connection with row_factory set."""
        conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _row_to_event(row: sqlite3.Row) -> Event:
        """Reconstruct an Event from a database row.

        id, created_at, and updated_at are passed explicitly so that the Event
        dataclass does NOT regenerate them via default_factory. status and price
        are coerced/normalised by the Event constructor.
        """
        return Event(
            title=row["title"],
            organizer_id=row["organizer_id"],
            venue=row["venue"],
            city=row["city"],
            start_date=row["start_date"],
            end_date=row["end_date"],
            capacity=row["capacity"],
            price=row["price"],
            description=row["description"],
            status=row["status"],
            id=row["id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    # ------------------------------------------------------------------ add

    def add(self, event: Event) -> Event:
        """Insert a new Event into the database and return it.

        Raises ValueError if an Event with the same id already exists.
        """
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT id FROM events WHERE id = ?", (event.id,)
            ).fetchone()
            if row is not None:
                raise ValueError(f"Event with id {event.id!r} already exists")

            conn.execute(
                """
                INSERT INTO events
                    (id, title, description, organizer_id, venue, city,
                     start_date, end_date, capacity, price, status,
                     created_at, updated_at)
                VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.id,
                    event.title,
                    event.description,
                    event.organizer_id,
                    event.venue,
                    event.city,
                    event.start_date,
                    event.end_date,
                    event.capacity,
                    event.price,
                    event.status.value,
                    event.created_at,
                    event.updated_at,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return event

    # ------------------------------------------------------------ get_by_id

    def get_by_id(self, event_id: str) -> Optional[Event]:
        """Return the Event for the given id, or None."""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM events WHERE id = ?", (event_id,)
            ).fetchone()
        finally:
            conn.close()
        return self._row_to_event(row) if row is not None else None

    # -------------------------------------------------------------- list_all

    def list_all(self) -> List[Event]:
        """Return all Events ordered by created_at ASC (consistent ordering per REQ-EVT-S01)."""
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM events ORDER BY created_at ASC"
            ).fetchall()
        finally:
            conn.close()
        return [self._row_to_event(r) for r in rows]

    # ---------------------------------------------------------------- update

    def update(self, event: Event) -> Event:
        """Replace the stored record for event.id.

        Raises KeyError if no Event with that id exists.
        """
        conn = self._connect()
        try:
            cursor = conn.execute(
                """
                UPDATE events
                SET title        = ?,
                    description  = ?,
                    organizer_id = ?,
                    venue        = ?,
                    city         = ?,
                    start_date   = ?,
                    end_date     = ?,
                    capacity     = ?,
                    price        = ?,
                    status       = ?,
                    updated_at   = ?
                WHERE id = ?
                """,
                (
                    event.title,
                    event.description,
                    event.organizer_id,
                    event.venue,
                    event.city,
                    event.start_date,
                    event.end_date,
                    event.capacity,
                    event.price,
                    event.status.value,
                    event.updated_at,
                    event.id,
                ),
            )
            conn.commit()
            if cursor.rowcount == 0:
                raise KeyError(f"Event with id {event.id!r} not found")
        finally:
            conn.close()
        return event

    # ---------------------------------------------------------------- delete

    def delete(self, event_id: str) -> bool:
        """Remove the Event with the given id.

        Returns True if found and deleted, False if not found.
        """
        conn = self._connect()
        try:
            cursor = conn.execute(
                "DELETE FROM events WHERE id = ?", (event_id,)
            )
            conn.commit()
        finally:
            conn.close()
        return cursor.rowcount > 0
