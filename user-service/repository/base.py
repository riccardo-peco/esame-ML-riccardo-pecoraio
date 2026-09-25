"""
repository/base.py — Abstract repository interface.

REQ-USR-S01: defines the contract that all storage backends must fulfil so
that domain/service.py never needs to know which backend is active.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from domain.models import User


class AbstractUserRepository(ABC):
    """
    Abstract base class for User persistence.

    All concrete implementations (memory, json, sqlite) must implement every
    method defined here.  The method signatures mirror the CRUD operations
    exposed by the HTTP API:

        add        → POST   /api/v1/users
        get_by_id  → GET    /api/v1/users/{id}
        get_by_email → internal uniqueness check (REQ-USR-B01)
        list_all   → GET    /api/v1/users  (filtering/pagination done in service layer)
        update     → PUT / PATCH /api/v1/users/{id}
        delete     → DELETE /api/v1/users/{id}
    """

    @abstractmethod
    def add(self, user: User) -> User:
        """Persist a new User and return it.

        The caller is responsible for supplying a fully-constructed User
        (including server-generated id, created_at, updated_at).
        """
        ...

    @abstractmethod
    def get_by_id(self, user_id: str) -> Optional[User]:
        """Return the User with the given id, or None if not found."""
        ...

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Return the User whose stored (lowercase) email matches *email*,
        or None if not found.  Comparison must be case-insensitive."""
        ...

    @abstractmethod
    def list_all(self) -> List[User]:
        """Return all stored Users in a consistent order.

        Filtering and pagination are applied by the service layer on top of
        this result so that all backends behave identically (REQ-USR-S01 §5).
        """
        ...

    @abstractmethod
    def update(self, user: User) -> User:
        """Replace the stored record for *user.id* with the supplied User
        and return the updated User.

        The caller is responsible for updating updated_at before calling this.
        Raises KeyError if the User does not exist.
        """
        ...

    @abstractmethod
    def delete(self, user_id: str) -> bool:
        """Remove the User with the given id.

        Returns True if the User was found and deleted, False otherwise.
        """
        ...
