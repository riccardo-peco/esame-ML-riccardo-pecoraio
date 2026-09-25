"""
validation.py — Reusable field validation for Event create/update requests.

Centralises every field constraint (REQ-EVT-V01) plus the date-range rule
(REQ-EVT-B03) so that POST / PUT / PATCH route handlers stay thin and share
identical behaviour. All violations raise ValidationError, which the app's
error handler maps to HTTP 422 with code "VALIDATION_ERROR".
"""
from __future__ import annotations

import re
from datetime import date
from typing import Any, Dict

from errors import ValidationError

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

_VALID_STATUSES = {"draft", "published", "cancelled"}

_TITLE_MIN, _TITLE_MAX = 3, 120
_DESCRIPTION_MAX = 2000
_VENUE_MIN, _VENUE_MAX = 1, 100
_CITY_MIN, _CITY_MAX = 1, 60
_CAPACITY_MIN, _CAPACITY_MAX = 1, 10000


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fail(message: str, field: str) -> None:
    """Raise a ValidationError carrying the offending field name."""
    raise ValidationError(message, {"field": field})


def _parse_date(value: Any, field: str) -> date:
    """Parse a YYYY-MM-DD string into a real ``date`` or raise ValidationError.

    Rejects non-strings, wrong shapes, and impossible calendar dates
    (e.g. 2024-13-40). Used for start_date / end_date (REQ-EVT-B03).
    """
    if not isinstance(value, str) or not _DATE_RE.match(value):
        _fail(f"{field} must be a valid YYYY-MM-DD date", field)
    try:
        return date.fromisoformat(value)
    except ValueError:
        _fail(f"{field} must be a valid YYYY-MM-DD date", field)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_event_fields(data: Dict[str, Any], *, require_all: bool) -> None:
    """Validate Event fields from a parsed request body.

    Args:
        data:        Parsed JSON dict from the request.
        require_all: When True (POST / PUT), the core fields — ``title``,
                     ``organizer_id``, ``venue``, ``city``, ``start_date``,
                     ``end_date``, ``capacity``, ``price`` — are required.
                     When False (PATCH), only supplied fields are validated.

    Raises:
        ValidationError: on the first constraint violation, with
                         ``details = {"field": <name>}``.
    """
    # ── title ─────────────────────────────────────────────────────────────
    if "title" in data:
        title = data["title"]
        if not isinstance(title, str) or not (_TITLE_MIN <= len(title) <= _TITLE_MAX):
            _fail(
                f"title must be between {_TITLE_MIN} and {_TITLE_MAX} characters",
                "title",
            )
    elif require_all:
        _fail("title is required", "title")

    # ── organizer_id ──────────────────────────────────────────────────────
    if "organizer_id" in data:
        organizer_id = data["organizer_id"]
        if not isinstance(organizer_id, str) or not organizer_id:
            _fail("organizer_id must be a non-empty string", "organizer_id")
    elif require_all:
        _fail("organizer_id is required", "organizer_id")

    # ── venue ─────────────────────────────────────────────────────────────
    if "venue" in data:
        venue = data["venue"]
        if not isinstance(venue, str) or not (_VENUE_MIN <= len(venue) <= _VENUE_MAX):
            _fail(
                f"venue must be between {_VENUE_MIN} and {_VENUE_MAX} characters",
                "venue",
            )
    elif require_all:
        _fail("venue is required", "venue")

    # ── city ──────────────────────────────────────────────────────────────
    if "city" in data:
        city = data["city"]
        if not isinstance(city, str) or not (_CITY_MIN <= len(city) <= _CITY_MAX):
            _fail(
                f"city must be between {_CITY_MIN} and {_CITY_MAX} characters",
                "city",
            )
    elif require_all:
        _fail("city is required", "city")

    # ── start_date / end_date (REQ-EVT-B03) ───────────────────────────────
    start_present = "start_date" in data
    end_present = "end_date" in data

    start_parsed = None
    end_parsed = None

    if start_present:
        start_parsed = _parse_date(data["start_date"], "start_date")
    elif require_all:
        _fail("start_date is required", "start_date")

    if end_present:
        end_parsed = _parse_date(data["end_date"], "end_date")
    elif require_all:
        _fail("end_date is required", "end_date")

    # end_date must be >= start_date when both are available (REQ-EVT-B03)
    if start_parsed is not None and end_parsed is not None:
        if end_parsed < start_parsed:
            _fail("end_date must be on or after start_date", "end_date")

    # ── capacity ──────────────────────────────────────────────────────────
    if "capacity" in data:
        capacity = data["capacity"]
        # bool is a subclass of int — reject it explicitly
        if isinstance(capacity, bool) or not isinstance(capacity, int):
            _fail("capacity must be an integer", "capacity")
        if not (_CAPACITY_MIN <= capacity <= _CAPACITY_MAX):
            _fail(
                f"capacity must be between {_CAPACITY_MIN} and {_CAPACITY_MAX}",
                "capacity",
            )
    elif require_all:
        _fail("capacity is required", "capacity")

    # ── price ─────────────────────────────────────────────────────────────
    if "price" in data:
        price = data["price"]
        # reject bool (subclass of int) and any non-numeric type
        if isinstance(price, bool) or not isinstance(price, (int, float)):
            _fail("price must be a number", "price")
        if price < 0:
            _fail("price must be greater than or equal to 0", "price")
    elif require_all:
        _fail("price is required", "price")

    # ── description (optional) ─────────────────────────────────────────────
    if "description" in data and data["description"] is not None:
        description = data["description"]
        if not isinstance(description, str) or len(description) > _DESCRIPTION_MAX:
            _fail(
                f"description must be at most {_DESCRIPTION_MAX} characters",
                "description",
            )

    # ── status (optional) ──────────────────────────────────────────────────
    if "status" in data:
        status = data["status"]
        if status not in _VALID_STATUSES:
            _fail(
                f"status must be one of: {', '.join(sorted(_VALID_STATUSES))}",
                "status",
            )
