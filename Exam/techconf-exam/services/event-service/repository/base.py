"""
repository/base.py — Abstract repository interface.

REQ-EVT-S01: defines the contract that all storage backends must fulfil so
that the service/route layer never needs to know which backend is active.
Filtering and pagination (REQ-EVT-B06) are applied on top of list_all() so
that all backends behave identically.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from domain.models import Event


class AbstractEventRepository(ABC):
    """
    Abstract base class for Event persistence.

    All concrete implementations (memory, json, sqlite) must implement every
    method defined here.  The method signatures mirror the CRUD operations
    exposed by the HTTP API:

        add        → POST   /api/v1/events
        get_by_id  → GET    /api/v1/events/{id}
        list_all   → GET    /api/v1/events (filtering/pagination in service layer)
        update     → PUT / PATCH /api/v1/events/{id}
        delete     → DELETE /api/v1/events/{id}
    """

    @abstractmethod
    def add(self, event: Event) -> Event:
        """Persist a new Event and return it.

        The caller is responsible for supplying a fully-constructed Event
        (including server-generated id, created_at, updated_at).
        """
        ...

    @abstractmethod
    def get_by_id(self, event_id: str) -> Optional[Event]:
        """Return the Event with the given id, or None if not found."""
        ...

    @abstractmethod
    def list_all(self) -> List[Event]:
        """Return all stored Events in a consistent order.

        Filtering (status/city) and pagination are applied by the service
        layer on top of this result so that all backends behave identically
        (REQ-EVT-S01 §5, REQ-EVT-B06).
        """
        ...

    @abstractmethod
    def update(self, event: Event) -> Event:
        """Replace the stored record for *event.id* with the supplied Event
        and return the updated Event.

        The caller is responsible for updating updated_at before calling this.
        Raises KeyError if the Event does not exist.
        """
        ...

    @abstractmethod
    def delete(self, event_id: str) -> bool:
        """Remove the Event with the given id.

        Returns True if the Event was found and deleted, False otherwise.
        """
        ...
