"""
routes/users.py — Blueprint for /api/v1/users endpoints.

T-07: POST /api/v1/users (REQ-USR-C01, REQ-USR-V01)
T-09: GET  /api/v1/users (REQ-USR-B03 — pagination)
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional

from flask import Blueprint, abort, current_app, jsonify, request

from domain.models import Role, User
from errors import ConflictError, NotFoundError, ValidationError
from pagination import paginate

users_bp = Blueprint("users", __name__, url_prefix="/api/v1/users")

# ---------------------------------------------------------------------------
# Email validation helper
# ---------------------------------------------------------------------------
# Simple format check: non-empty local part, @, domain with at least one dot
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

VALID_ROLES = {r.value for r in Role}


# ---------------------------------------------------------------------------
# Reusable validation function (also used by T-12 PUT/PATCH)
# ---------------------------------------------------------------------------

def validate_user_fields(
    data: Dict[str, Any],
    *,
    require_all: bool = True,
) -> None:
    """Validate user fields from a parsed request body.

    Args:
        data:        Parsed JSON dict from the request.
        require_all: When True (POST / PUT), ``first_name``, ``last_name``, and
                     ``email`` are required.  When False (PATCH), only supplied
                     fields are validated.

    Raises:
        ValidationError: if any field fails its constraint.
    """
    # ── first_name ──────────────────────────────────────────────────────────
    if "first_name" in data:
        fn = data["first_name"]
        if not isinstance(fn, str) or not (1 <= len(fn) <= 50):
            raise ValidationError(
                "first_name must be between 1 and 50 characters",
                {"field": "first_name"},
            )
    elif require_all:
        raise ValidationError("first_name is required", {"field": "first_name"})

    # ── last_name ────────────────────────────────────────────────────────────
    if "last_name" in data:
        ln = data["last_name"]
        if not isinstance(ln, str) or not (1 <= len(ln) <= 50):
            raise ValidationError(
                "last_name must be between 1 and 50 characters",
                {"field": "last_name"},
            )
    elif require_all:
        raise ValidationError("last_name is required", {"field": "last_name"})

    # ── email ────────────────────────────────────────────────────────────────
    if "email" in data:
        em = data["email"]
        if not isinstance(em, str) or not _EMAIL_RE.match(em):
            raise ValidationError(
                "email must be a valid email address",
                {"field": "email"},
            )
    elif require_all:
        raise ValidationError("email is required", {"field": "email"})

    # ── company (optional) ───────────────────────────────────────────────────
    if "company" in data and data["company"] is not None:
        co = data["company"]
        if not isinstance(co, str) or len(co) > 100:
            raise ValidationError(
                "company must be at most 100 characters",
                {"field": "company"},
            )

    # ── role (optional) ──────────────────────────────────────────────────────
    if "role" in data:
        ro = data["role"]
        if ro not in VALID_ROLES:
            raise ValidationError(
                f"role must be one of: {', '.join(sorted(VALID_ROLES))}",
                {"field": "role", "allowed": sorted(VALID_ROLES)},
            )


# ---------------------------------------------------------------------------
# POST /api/v1/users
# ---------------------------------------------------------------------------

@users_bp.post("")
def create_user():
    """Create a new user.

    REQ-USR-C01: 201 + Location header + full User object.
    REQ-USR-V01: field validation with 422 on failure.
    Malformed JSON → 400 (handled by the existing Flask error handler in app.py).
    """
    data: Optional[Dict[str, Any]] = request.get_json(force=True, silent=True)

    # REQ-USR-C01 §5: malformed / non-JSON body → 400
    if data is None:
        abort(400)

    # REQ-USR-V01 + REQ-USR-C01 §4,§6: validate all fields
    validate_user_fields(data, require_all=True)

    # REQ-USR-C01 §7: default role to "attendee"
    role = data.get("role", Role.attendee.value)

    # REQ-USR-V01 §5: ignore server-generated fields if client supplied them
    user = User(
        first_name=data["first_name"],
        last_name=data["last_name"],
        email=data["email"],          # lowercased in User.__post_init__
        company=data.get("company"),
        role=role,
    )

    # REQ-USR-B01: reject duplicate emails (case-insensitive)
    existing = current_app.repo.get_by_email(user.email)
    if existing is not None:
        raise ConflictError(f"Email '{user.email}' is already registered")

    saved = current_app.repo.add(user)  # type: ignore[attr-defined]

    # REQ-USR-C01 §1,§2,§3: 201 + Location + full body
    response = jsonify(saved.to_dict())
    response.status_code = 201
    response.headers["Location"] = f"/api/v1/users/{saved.id}"
    return response


# ---------------------------------------------------------------------------
# GET /api/v1/users
# ---------------------------------------------------------------------------

_DEFAULT_PAGE = 1
_DEFAULT_PAGE_SIZE = 20
_MAX_PAGE_SIZE = 100


def _parse_int_param(name: str, raw: Optional[str], default: int) -> int:
    """Parse a query-string integer parameter, raising ValidationError on bad input.

    Args:
        name:    Parameter name (used in error details).
        raw:     Raw string value from request.args, or None if absent.
        default: Value to return when *raw* is None.

    Returns:
        Parsed integer.

    Raises:
        ValidationError: when the value is not a valid integer string.
    """
    if raw is None:
        return default
    try:
        return int(raw)
    except (ValueError, TypeError):
        raise ValidationError(
            f"{name} must be an integer",
            {"field": name},
        )


@users_bp.get("")
def list_users():
    """List all users with pagination.

    REQ-USR-B03: paginated Page response with page/page_size/total/items.

    Query parameters:
        page      (int, default 1)    — must be >= 1
        page_size (int, default 20)   — must be 1–100
    """
    # ── parse pagination params ──────────────────────────────────────────────
    page = _parse_int_param("page", request.args.get("page"), _DEFAULT_PAGE)
    page_size = _parse_int_param(
        "page_size", request.args.get("page_size"), _DEFAULT_PAGE_SIZE
    )

    # ── validate bounds ──────────────────────────────────────────────────────
    if page < 1:
        raise ValidationError(
            "page must be >= 1",
            {"field": "page"},
        )
    if not (1 <= page_size <= _MAX_PAGE_SIZE):
        raise ValidationError(
            f"page_size must be between 1 and {_MAX_PAGE_SIZE}",
            {"field": "page_size"},
        )

    # ── fetch ────────────────────────────────────────────────────────────────
    all_users = current_app.repo.list_all()  # type: ignore[attr-defined]

    # ── apply role filter (REQ-USR-B03 §4, §6) ───────────────────────────────
    role_filter = request.args.get("role")
    if role_filter is not None:
        if role_filter not in VALID_ROLES:
            raise ValidationError(
                f"role must be one of: {', '.join(sorted(VALID_ROLES))}",
                {"field": "role", "allowed": sorted(VALID_ROLES)},
            )
        all_users = [u for u in all_users if u.role.value == role_filter]

    # ── apply email filter (REQ-USR-B03 §5) ──────────────────────────────────
    email_filter = request.args.get("email")
    if email_filter is not None:
        normalised = email_filter.lower()
        all_users = [u for u in all_users if u.email == normalised]

    # ── paginate ──────────────────────────────────────────────────────────────
    result = paginate(all_users, page, page_size)

    # ── serialise ────────────────────────────────────────────────────────────
    body = {
        "items": [u.to_dict() for u in result["items"]],
        "page": result["page"],
        "page_size": result["page_size"],
        "total": result["total"],
    }
    return jsonify(body), 200


# ---------------------------------------------------------------------------
# GET /api/v1/users/<user_id>
# ---------------------------------------------------------------------------

@users_bp.get("/<user_id>")
def get_user(user_id: str):
    """Retrieve a single user by ID.

    REQ-USR-C02 §1: User exists → 200 + full User object.
    REQ-USR-C02 §2: User not found → 404 + Error_Body code="NOT_FOUND".
    """
    user = current_app.repo.get_by_id(user_id)  # type: ignore[attr-defined]
    if user is None:
        raise NotFoundError(f"User '{user_id}' not found")
    return jsonify(user.to_dict()), 200
