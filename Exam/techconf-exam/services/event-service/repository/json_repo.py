"""
repository/json_repo.py — JSON-file implementation of AbstractEventRepository.

REQ-EVT-S01: persists data as a JSON array in the directory specified by DATA_DIR
             and exposes the same interface as all other backends so that business
             logic and route handlers need no changes when this backend is active.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from domain.models import Event
from repository.base import AbstractEventRepository

_FILENAME = "events.json"


class JsonEventRepository(AbstractEventRepository):
    """
    File-backed Event repository that persists all data as a JSON array in
    ``<data_dir>/events.json``.

    The file is read fresh on every operation (simple, safe for single-process use).
    The directory is created automatically if it does not exist.
    """

    def __init__(self, data_dir: str) -> None:
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._file = self._data_dir / _FILENAME

    # ---------------------------------------------------------------- helpers

    def _load(self) -> List[Event]:
        """Read the JSON file and return a list of Event objects.

        Returns an empty list if the file does not exist yet.
        """
        if not self._file.exists():
            return []
        with self._file.open("r", encoding="utf-8") as fh:
            raw: list = json.load(fh)
        return [self._dict_to_event(d) for d in raw]

    def _save(self, events: List[Event]) -> None:
        """Overwrite the JSON file with the serialised list of events."""
        with self._file.open("w", encoding="utf-8") as fh:
            json.dump([e.to_dict() for e in events], fh, ensure_ascii=False, indent=2)

    @staticmethod
    def _dict_to_event(d: dict) -> Event:
        """Reconstruct an Event from a serialised dict.

        Fields ``id``, ``created_at``, and ``updated_at`` are passed explicitly
        so that the Event dataclass does NOT regenerate them via default_factory.
        status and price are coerced/normalised by the Event constructor.
        """
        return Event(
            title=d["title"],
            organizer_id=d["organizer_id"],
            venue=d["venue"],
            city=d["city"],
            start_date=d["start_date"],
            end_date=d["end_date"],
            capacity=d["capacity"],
            price=d["price"],
            description=d.get("description"),
            status=d["status"],
            id=d["id"],
            created_at=d["created_at"],
            updated_at=d["updated_at"],
        )

    # ------------------------------------------------------------------ add

    def add(self, event: Event) -> Event:
        """Persist a new Event and return it.

        Raises ValueError if an Event with the same id already exists.
        """
        events = self._load()
        if any(e.id == event.id for e in events):
            raise ValueError(f"Event with id {event.id!r} already exists")
        events.append(event)
        self._save(events)
        return event

    # ------------------------------------------------------------ get_by_id

    def get_by_id(self, event_id: str) -> Optional[Event]:
        """Return the Event for the given id, or None."""
        for event in self._load():
            if event.id == event_id:
                return event
        return None

    # -------------------------------------------------------------- list_all

    def list_all(self) -> List[Event]:
        """Return all Events in file order (consistent ordering per REQ-EVT-S01)."""
        return self._load()

    # ---------------------------------------------------------------- update

    def update(self, event: Event) -> Event:
        """Replace the stored record for event.id.

        Raises KeyError if no Event with that id exists.
        """
        events = self._load()
        for i, e in enumerate(events):
            if e.id == event.id:
                events[i] = event
                self._save(events)
                return event
        raise KeyError(f"Event with id {event.id!r} not found")

    # ---------------------------------------------------------------- delete

    def delete(self, event_id: str) -> bool:
        """Remove the Event with the given id.

        Returns True if found and deleted, False if not found.
        """
        events = self._load()
        filtered = [e for e in events if e.id != event_id]
        if len(filtered) == len(events):
            return False
        self._save(filtered)
        return True
