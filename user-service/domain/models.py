"""
domain/models.py — User domain model.

REQ-USR-C01: fields, server-generated id/created_at/updated_at.
REQ-USR-B02: email is stored and returned in lowercase.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class Role(str, Enum):
    """Valid user roles (REQ-USR-C01 §6)."""
    attendee = "attendee"
    speaker = "speaker"
    organizer = "organizer"


def _utcnow() -> str:
    """Return the current UTC time as an ISO 8601 string with 'Z' suffix."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


@dataclass
class User:
    """
    Central User entity for the TechConf platform.

    Server-generated fields (not writable by clients):
        id          — UUID v4 string
        created_at  — ISO 8601 UTC timestamp set on creation
        updated_at  — ISO 8601 UTC timestamp updated on every mutation

    Client-supplied fields:
        first_name  — 1–50 chars (REQ-USR-V01)
        last_name   — 1–50 chars (REQ-USR-V01)
        email       — valid e-mail format; stored lowercase (REQ-USR-B02)
        company     — optional, max 100 chars (REQ-USR-V01)
        role        — Role enum, default 'attendee' (REQ-USR-C01 §7)
    """

    first_name: str
    last_name: str
    email: str                          # stored lowercase (REQ-USR-B02)
    company: Optional[str] = None
    role: Role = Role.attendee

    # Server-generated — use default_factory so each instance gets unique values
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=_utcnow)
    updated_at: str = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        # Always normalise email to lowercase at construction time (REQ-USR-B02)
        self.email = self.email.lower()
        # Coerce role strings to the enum so callers can pass either form
        if isinstance(self.role, str):
            self.role = Role(self.role)

    def to_dict(self) -> dict:
        """Serialize to a plain dict suitable for JSON responses.

        email is always lowercase (REQ-USR-B02).
        role is returned as its string value.
        """
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,          # already lowercase from __post_init__
            "company": self.company,
            "role": self.role.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
