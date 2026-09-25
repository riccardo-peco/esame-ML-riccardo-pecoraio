"""
errors.py — Common error body format and custom exception classes.

No Flask imports here — kept standalone so it is testable without the app.

Error_Body format (spec glossary):
    {"error": {"code": "UPPER_SNAKE", "message": "...", "details": {...}}}
"""
from __future__ import annotations

from typing import Optional


# ---------------------------------------------------------------------------
# Error body builder
# ---------------------------------------------------------------------------

def make_error_body(code: str, message: str, details: Optional[dict] = None) -> dict:
    """Build the standard Error_Body dict.

    Args:
        code:    UPPER_SNAKE error code (e.g. ``"VALIDATION_ERROR"``).
        message: Human-readable description.
        details: Optional free-form dict with additional context.

    Returns:
        ``{"error": {"code": ..., "message": ...[, "details": ...]}}``
    """
    body: dict = {"code": code, "message": message}
    if details:
        body["details"] = details
    return {"error": body}


# ---------------------------------------------------------------------------
# Custom exceptions  (no HTTP status codes here — that's the handler's job)
# ---------------------------------------------------------------------------

class ValidationError(Exception):
    """Raised when request data fails validation rules.

    Maps to HTTP 422, code ``"VALIDATION_ERROR"``.
    """

    def __init__(self, message: str, details: Optional[dict] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class NotFoundError(Exception):
    """Raised when a requested resource does not exist.

    Maps to HTTP 404, code ``"NOT_FOUND"``.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ReferenceNotFoundError(Exception):
    """Raised when a referenced organizer does not exist in the user-service.

    Maps to HTTP 422, code ``"REFERENCE_NOT_FOUND"`` (REQ-EVT-B01, B02).
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidOrganizerError(Exception):
    """Raised when the referenced user exists but is not an organizer.

    Maps to HTTP 422, code ``"INVALID_ORGANIZER"`` (REQ-EVT-B01, B02).
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidStatusTransitionError(Exception):
    """Raised when a status change violates the lifecycle state machine.

    Maps to HTTP 422, code ``"INVALID_STATUS_TRANSITION"`` (REQ-EVT-B04).
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class DependencyUnavailableError(Exception):
    """Raised when the user-service is unreachable during organizer validation.

    Maps to HTTP 503, code ``"DEPENDENCY_UNAVAILABLE"`` (REQ-EVT-B05).
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
