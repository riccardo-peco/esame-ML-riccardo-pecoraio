"""
repository/memory_repo.py — In-memory implementation of AbstractUserRepository.

REQ-USR-S01 §1: stores all data in-process with no file I/O.
REQ-USR-S01 §4: used as the default backend when STORAGE_BACKEND is not set.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from domain.models import User
from repository.base import AbstractUserRepository


class MemoryUserRepository(AbstractUserRepository):
    """
    Thread-local, in-process User store backed by a plain dict.

    Insertion order is preserved (Python 3.7+ dict guarantee), so
    list_all() returns users in the order they were added.
    """

    def __init__(self) -> None:
        # Primary store keyed by user.id
        self._store: Dict[str, User] = {}

    # ------------------------------------------------------------------ add
    def add(self, user: User) -> User:
        """Persist a new User and return it.

        Raises ValueError if a User with the same id already exists
        (prevents accidental overwrites of existing records).
        """
        if user.id in self._store:
            raise ValueError(f"User with id {user.id!r} already exists")
        self._store[user.id] = user
        return user

    # ------------------------------------------------------------ get_by_id
    def get_by_id(self, user_id: str) -> Optional[User]:
        """Return the User for the given id, or None."""
        return self._store.get(user_id)

    # ---------------------------------------------------------- get_by_email
    def get_by_email(self, email: str) -> Optional[User]:
        """Case-insensitive email lookup; returns the first match or None.

        REQ-USR-B01: uniqueness check must be case-insensitive.
        """
        normalised = email.lower()
        for user in self._store.values():
            if user.email == normalised:   # stored email is already lowercase
                return user
        return None

    # -------------------------------------------------------------- list_all
    def list_all(self) -> List[User]:
        """Return all Users in insertion order (consistent ordering per REQ-USR-S01 §5)."""
        return list(self._store.values())

    # ---------------------------------------------------------------- update
    def update(self, user: User) -> User:
        """Replace the stored record for user.id.

        Raises KeyError if no User with that id exists.
        """
        if user.id not in self._store:
            raise KeyError(f"User with id {user.id!r} not found")
        self._store[user.id] = user
        return user

    # ---------------------------------------------------------------- delete
    def delete(self, user_id: str) -> bool:
        """Remove the User with the given id.

        Returns True if found and deleted, False if not found.
        """
        if user_id in self._store:
            del self._store[user_id]
            return True
        return False
