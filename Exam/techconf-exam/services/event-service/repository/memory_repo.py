"""
repository/memory_repo.py — In-memory implementation of AbstractEventRepository.

REQ-EVT-S01: stores all data in-process with no file I/O; used as the default
             backend when STORAGE_BACKEND is not set.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from domain.models import Event
from repository.base import AbstractEventRepository


class MemoryEventRepository(AbstractEventRepository):
    """
    Thread-local, in-process Event store backed by a plain dict.

    Insertion order is preserved (Python 3.7+ dict guarantee), so
    list_all() returns events in the order they were added.
    """

    def __init__(self) -> None:
        # Primary store keyed by event.id
        self._store: Dict[str, Event] = {}

    # ------------------------------------------------------------------ add
    def add(self, event: Event) -> Event:
        """Persist a new Event and return it.

        Raises ValueError if an Event with the same id already exists
        (prevents accidental overwrites of existing records).
        """
        if event.id in self._store:
            raise ValueError(f"Event with id {event.id!r} already exists")
        self._store[event.id] = event
        return event

    # ------------------------------------------------------------ get_by_id
    def get_by_id(self, event_id: str) -> Optional[Event]:
        """Return the Event for the given id, or None."""
        return self._store.get(event_id)

    # -------------------------------------------------------------- list_all
    def list_all(self) -> List[Event]:
        """Return all Events in insertion order (consistent ordering per REQ-EVT-S01)."""
        return list(self._store.values())

    # ---------------------------------------------------------------- update
    def update(self, event: Event) -> Event:
        """Replace the stored record for event.id.

        Raises KeyError if no Event with that id exists.
        """
        if event.id not in self._store:
            raise KeyError(f"Event with id {event.id!r} not found")
        self._store[event.id] = event
        return event

    # ---------------------------------------------------------------- delete
    def delete(self, event_id: str) -> bool:
        """Remove the Event with the given id.

        Returns True if found and deleted, False if not found.
        """
        if event_id in self._store:
            del self._store[event_id]
            return True
        return False
