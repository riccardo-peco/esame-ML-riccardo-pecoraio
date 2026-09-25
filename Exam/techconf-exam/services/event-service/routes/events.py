"""
routes/events.py — Blueprint for /api/v1/events endpoints.

T-08: POST /api/v1/events (create) with field validation (REQ-EVT-C01,
REQ-EVT-V01, REQ-EVT-B03) and organizer reference validation against the
user-service (REQ-EVT-B01, REQ-EVT-B02, REQ-EVT-B05).
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from flask import Blueprint, abort, current_app, jsonify, request

from domain.models import Event, EventStatus
from validation import validate_event_fields

events_bp = Blueprint("events", __name__, url_prefix="/api/v1/events")


# ---------------------------------------------------------------------------
# POST /api/v1/events
# ---------------------------------------------------------------------------

@events_bp.post("")
def create_event():
    """Create a new Event.

    REQ-EVT-C01 §1: valid body → create, persist, respond 201.
    REQ-EVT-C01 §2: include a Location header for the new resource.
    REQ-EVT-C01 §3: return the full Event object with server-generated fields.
    REQ-EVT-C01 §4: missing required field → 422 VALIDATION_ERROR.
    REQ-EVT-C01 §5: malformed JSON → 400.
    REQ-EVT-C01 §6: default status to "draft".
    REQ-EVT-B01/B02/B05: validate organizer_id against the user-service.
    REQ-EVT-V01 §8: ignore client-supplied id/created_at/updated_at.
    """
    data: Optional[Dict[str, Any]] = request.get_json(force=True, silent=True)

    # REQ-EVT-C01 §5: malformed / non-JSON body → 400
    if data is None:
        abort(400)

    # REQ-EVT-V01 + REQ-EVT-C01 §4,§7 + REQ-EVT-B03: field-level validation
    validate_event_fields(data, require_all=True)

    # REQ-EVT-B01/B02/B05: validate organizer BEFORE persisting. The client's
    # exceptions (ReferenceNotFoundError / InvalidOrganizerError /
    # DependencyUnavailableError) propagate to the registered error handlers.
    current_app.user_client.validate_organizer(data["organizer_id"])

    # REQ-EVT-C01 §6: default status to "draft" when omitted.
    # REQ-EVT-V01 §8: build only from client-writable fields — id, created_at,
    # and updated_at are always server-generated and never taken from input.
    event = Event(
        title=data["title"],
        organizer_id=data["organizer_id"],
        venue=data["venue"],
        city=data["city"],
        start_date=data["start_date"],
        end_date=data["end_date"],
        capacity=data["capacity"],
        price=data["price"],
        description=data.get("description"),
        status=data.get("status", EventStatus.draft.value),
    )

    saved = current_app.repo.add(event)  # type: ignore[attr-defined]

    # REQ-EVT-C01 §1,§2,§3: 201 + Location + full body
    response = jsonify(saved.to_dict())
    response.status_code = 201
    response.headers["Location"] = f"/api/v1/events/{saved.id}"
    return response
