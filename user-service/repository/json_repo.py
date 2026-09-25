"""
repository/json_repo.py — JSON-file implementation of AbstractUserRepository.

REQ-USR-S01 §2: persists data as JSON files in the directory specified by DATA_DIR.
REQ-USR-S01 §5: exposes the same interface as all other backends so that business
                logic and route handlers need no changes when this backend is active.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Optional

from domain.models import Role, User
from repository.base import AbstractUserRepository

_FILENAME = "users.json"


class JsonUserRepository(AbstractUserRepository):
    """
    File-backed User repository that persists all data as a JSON array in
    ``<data_dir>/users.json``.

    The file is read fresh on every operation (simple, safe for single-process use).
    The directory is created automatically if it does not exist.
    """

    def __init__(self, data_dir: str) -> None:
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._file = self._data_dir / _FILENAME

    # ---------------------------------------------------------------- helpers

    def _load(self) -> List[User]:
        """Read the JSON file and return a list of User objects.

        Returns an empty list if the file does not exist yet.
        """
        if not self._file.exists():
            return []
        with self._file.open("r", encoding="utf-8") as fh:
            raw: list = json.load(fh)
        return [self._dict_to_user(d) for d in raw]

    def _save(self, users: List[User]) -> None:
        """Overwrite the JSON file with the serialised list of users."""
        with self._file.open("w", encoding="utf-8") as fh:
            json.dump([u.to_dict() for u in users], fh, ensure_ascii=False, indent=2)

    @staticmethod
    def _dict_to_user(d: dict) -> User:
        """Reconstruct a User from a serialised dict.

        Fields ``id``, ``created_at``, and ``updated_at`` are passed explicitly
        so that the User dataclass does NOT regenerate them via default_factory.
        """
        return User(
            first_name=d["first_name"],
            last_name=d["last_name"],
            email=d["email"],          # already lowercase in storage
            company=d.get("company"),
            role=Role(d["role"]),
            id=d["id"],
            created_at=d["created_at"],
            updated_at=d["updated_at"],
        )

    # ------------------------------------------------------------------ add

    def add(self, user: User) -> User:
        """Persist a new User and return it.

        Raises ValueError if a User with the same id already exists.
        """
        users = self._load()
        if any(u.id == user.id for u in users):
            raise ValueError(f"User with id {user.id!r} already exists")
        users.append(user)
        self._save(users)
        return user

    # ------------------------------------------------------------ get_by_id

    def get_by_id(self, user_id: str) -> Optional[User]:
        """Return the User for the given id, or None."""
        for user in self._load():
            if user.id == user_id:
                return user
        return None

    # ---------------------------------------------------------- get_by_email

    def get_by_email(self, email: str) -> Optional[User]:
        """Case-insensitive email lookup; returns the first match or None.

        REQ-USR-B01: uniqueness check must be case-insensitive.
        """
        normalised = email.lower()
        for user in self._load():
            if user.email == normalised:   # stored email is already lowercase
                return user
        return None

    # -------------------------------------------------------------- list_all

    def list_all(self) -> List[User]:
        """Return all Users in file order (consistent ordering per REQ-USR-S01 §5)."""
        return self._load()

    # ---------------------------------------------------------------- update

    def update(self, user: User) -> User:
        """Replace the stored record for user.id.

        Raises KeyError if no User with that id exists.
        """
        users = self._load()
        for i, u in enumerate(users):
            if u.id == user.id:
                users[i] = user
                self._save(users)
                return user
        raise KeyError(f"User with id {user.id!r} not found")

    # ---------------------------------------------------------------- delete

    def delete(self, user_id: str) -> bool:
        """Remove the User with the given id.

        Returns True if found and deleted, False if not found.
        """
        users = self._load()
        filtered = [u for u in users if u.id != user_id]
        if len(filtered) == len(users):
            return False
        self._save(filtered)
        return True
