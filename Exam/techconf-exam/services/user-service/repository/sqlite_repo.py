"""
repository/sqlite_repo.py — SQLite implementation of AbstractUserRepository.

REQ-USR-S01 §3: persists data in a SQLite database file in DATA_DIR using
                only the Python standard library sqlite3 module.
REQ-USR-S01 §5: exposes the same interface as all other backends so that
                business logic and route handlers need no changes when this
                backend is active.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List, Optional

from domain.models import Role, User
from repository.base import AbstractUserRepository

_DBFILE = "users.db"

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id         TEXT PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name  TEXT NOT NULL,
    email      TEXT NOT NULL,
    company    TEXT,
    role       TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""


class SqliteUserRepository(AbstractUserRepository):
    """
    SQLite-backed User repository that persists all data in
    ``<data_dir>/users.db``.

    Each public method opens a fresh connection and closes it on return,
    which keeps the implementation simple and safe for single-process use
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
    def _row_to_user(row: sqlite3.Row) -> User:
        """Reconstruct a User from a database row.

        id, created_at, and updated_at are passed explicitly so that the
        User dataclass does NOT regenerate them via default_factory.
        """
        return User(
            first_name=row["first_name"],
            last_name=row["last_name"],
            email=row["email"],        # already lowercase in storage
            company=row["company"],
            role=Role(row["role"]),
            id=row["id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    # ------------------------------------------------------------------ add

    def add(self, user: User) -> User:
        """Insert a new User into the database and return it.

        Raises ValueError if a User with the same id already exists.
        """
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT id FROM users WHERE id = ?", (user.id,)
            ).fetchone()
            if row is not None:
                raise ValueError(f"User with id {user.id!r} already exists")

            conn.execute(
                """
                INSERT INTO users
                    (id, first_name, last_name, email, company, role, created_at, updated_at)
                VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user.id,
                    user.first_name,
                    user.last_name,
                    user.email,           # already lowercase from User.__post_init__
                    user.company,
                    user.role.value,
                    user.created_at,
                    user.updated_at,
                ),
            )
            conn.commit()
        finally:
            conn.close()
        return user

    # ------------------------------------------------------------ get_by_id

    def get_by_id(self, user_id: str) -> Optional[User]:
        """Return the User for the given id, or None."""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()
        finally:
            conn.close()
        return self._row_to_user(row) if row is not None else None

    # ---------------------------------------------------------- get_by_email

    def get_by_email(self, email: str) -> Optional[User]:
        """Case-insensitive email lookup; returns the first match or None.

        REQ-USR-B01: uniqueness check must be case-insensitive.
        """
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email,)
            ).fetchone()
        finally:
            conn.close()
        return self._row_to_user(row) if row is not None else None

    # -------------------------------------------------------------- list_all

    def list_all(self) -> List[User]:
        """Return all Users ordered by created_at ASC (consistent ordering per REQ-USR-S01 §5)."""
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM users ORDER BY created_at ASC"
            ).fetchall()
        finally:
            conn.close()
        return [self._row_to_user(r) for r in rows]

    # ---------------------------------------------------------------- update

    def update(self, user: User) -> User:
        """Replace the stored record for user.id.

        Raises KeyError if no User with that id exists.
        """
        conn = self._connect()
        try:
            cursor = conn.execute(
                """
                UPDATE users
                SET first_name = ?,
                    last_name  = ?,
                    email      = ?,
                    company    = ?,
                    role       = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    user.first_name,
                    user.last_name,
                    user.email,
                    user.company,
                    user.role.value,
                    user.updated_at,
                    user.id,
                ),
            )
            conn.commit()
            if cursor.rowcount == 0:
                raise KeyError(f"User with id {user.id!r} not found")
        finally:
            conn.close()
        return user

    # ---------------------------------------------------------------- delete

    def delete(self, user_id: str) -> bool:
        """Remove the User with the given id.

        Returns True if found and deleted, False if not found.
        """
        conn = self._connect()
        try:
            cursor = conn.execute(
                "DELETE FROM users WHERE id = ?", (user_id,)
            )
            conn.commit()
        finally:
            conn.close()
        return cursor.rowcount > 0
