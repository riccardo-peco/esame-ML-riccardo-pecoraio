"""
domain/models.py — Event domain model.

REQ-EVT-C01 (p.3): server-generated id (UUID v4), created_at, updated_at.
REQ-EVT-V01: price normalized to 2 decimals; id/created_at/updated_at not writable.
REQ-EVT-B04: status lifecycle transitions via is_valid_transition().
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class EventStatus(str, Enum):
    """Valid event lifecycle states (REQ-EVT-C01, REQ-EVT-B04)."""
    draft = "draft"
    published = "published"
    cancelled = "cancelled"


def _utcnow() -> str:
    """Return the current UTC time as an ISO 8601 string with 'Z' suffix."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


# Allowed status transitions (REQ-EVT-B04). No-op transitions (current == target)
# are always valid and handled separately in is_valid_transition().
_ALLOWED_TRANSITIONS = {
    (EventStatus.draft, EventStatus.published),
    (EventStatus.draft, EventStatus.cancelled),
    (EventStatus.published, EventStatus.cancelled),
}


def is_valid_transition(current: EventStatus, target: EventStatus) -> bool:
    """Return True if moving from *current* to *target* is allowed (REQ-EVT-B04).

    Allowed: draft->published, draft->cancelled, published->cancelled, and the
    no-op transition (current == target). Everything else is invalid.
    """
    if current == target:
        return True
    return (current, target) in _ALLOWED_TRANSITIONS


@dataclass
class Event:
    """
    Central Event (conference) entity for the TechConf platform.

    Server-generated fields (not writable by clients — REQ-EVT-V01 §8):
        id          — UUID v4 string
        created_at  — ISO 8601 UTC timestamp set on creation
        updated_at  — ISO 8601 UTC timestamp updated on every mutation

    Client-supplied fields:
        title        — 3–120 chars (REQ-EVT-V01)
        description  — optional, max 2000 chars (REQ-EVT-V01)
        organizer_id — UUID of an organizer user (validated against user-service)
        venue        — max 100 chars (REQ-EVT-V01)
        city         — max 60 chars (REQ-EVT-V01)
        start_date   — YYYY-MM-DD
        end_date     — YYYY-MM-DD (>= start_date)
        capacity     — 1–10000 (REQ-EVT-V01)
        price        — >= 0, stored with 2 decimals (REQ-EVT-V01)
        status       — EventStatus enum, default 'draft' (REQ-EVT-C01 §6)
    """

    title: str
    organizer_id: str
    venue: str
    city: str
    start_date: str
    end_date: str
    capacity: int
    price: float
    description: Optional[str] = None
    status: EventStatus = EventStatus.draft

    # Server-generated — use default_factory so each instance gets unique values
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=_utcnow)
    updated_at: str = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        # Coerce status strings to the enum so callers can pass either form
        if isinstance(self.status, str):
            self.status = EventStatus(self.status)
        # Normalise price to a float with 2 decimals (REQ-EVT-V01 §7)
        self.price = round(float(self.price), 2)

    def to_dict(self) -> dict:
        """Serialize to a plain dict matching the Event contract schema exactly.

        Emits precisely the keys declared in the OpenAPI Event schema
        (additionalProperties: false) and no others. description stays null
        when None; status is returned as its string value; price as a float
        with 2 decimals.
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "organizer_id": self.organizer_id,
            "venue": self.venue,
            "city": self.city,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "capacity": self.capacity,
            "price": round(float(self.price), 2),
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
