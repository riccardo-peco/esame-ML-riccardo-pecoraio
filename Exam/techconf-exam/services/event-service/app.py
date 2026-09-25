"""
app.py — Flask application entry-point for event-service.

Runnable with `python -m app` from the service root (see services.yaml).
"""
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

import config
from errors import (
    DependencyUnavailableError,
    InvalidOrganizerError,
    InvalidStatusTransitionError,
    NotFoundError,
    ReferenceNotFoundError,
    ValidationError,
    make_error_body,
)


def create_app() -> Flask:
    """Application factory."""
    app = Flask(__name__)

    # ------------------------------------------------------------------ health
    @app.get("/health")
    def health():
        """GET /health — REQ-EVT-H01.
        Always responds 200 regardless of the storage backend state or the
        reachability of the user-service.
        """
        return jsonify({"status": "ok", "service": "event-service"}), 200

    # --------------------------------------------------------- error handlers
    @app.errorhandler(ValidationError)
    def handle_validation_error(exc: ValidationError):
        """HTTP 422 — field-level validation failure (REQ-EVT-V01, B03)."""
        body = make_error_body("VALIDATION_ERROR", exc.message, exc.details)
        return jsonify(body), 422

    @app.errorhandler(NotFoundError)
    def handle_not_found_error(exc: NotFoundError):
        """HTTP 404 — resource not found (REQ-EVT-C02 §2)."""
        body = make_error_body("NOT_FOUND", exc.message)
        return jsonify(body), 404

    @app.errorhandler(ReferenceNotFoundError)
    def handle_reference_not_found_error(exc: ReferenceNotFoundError):
        """HTTP 422 — organizer_id references a missing user (REQ-EVT-B01)."""
        body = make_error_body("REFERENCE_NOT_FOUND", exc.message)
        return jsonify(body), 422

    @app.errorhandler(InvalidOrganizerError)
    def handle_invalid_organizer_error(exc: InvalidOrganizerError):
        """HTTP 422 — referenced user is not an organizer (REQ-EVT-B01)."""
        body = make_error_body("INVALID_ORGANIZER", exc.message)
        return jsonify(body), 422

    @app.errorhandler(InvalidStatusTransitionError)
    def handle_invalid_status_transition_error(exc: InvalidStatusTransitionError):
        """HTTP 422 — illegal lifecycle transition (REQ-EVT-B04)."""
        body = make_error_body("INVALID_STATUS_TRANSITION", exc.message)
        return jsonify(body), 422

    @app.errorhandler(DependencyUnavailableError)
    def handle_dependency_unavailable_error(exc: DependencyUnavailableError):
        """HTTP 503 — user-service unreachable during validation (REQ-EVT-B05)."""
        body = make_error_body("DEPENDENCY_UNAVAILABLE", exc.message)
        return jsonify(body), 503

    @app.errorhandler(400)
    def handle_bad_request(exc):
        """HTTP 400 — malformed JSON or bad request (REQ-EVT-C01 §5)."""
        message = exc.description if isinstance(exc, HTTPException) else "Bad request"
        body = make_error_body("BAD_REQUEST", str(message))
        return jsonify(body), 400

    @app.errorhandler(404)
    def handle_generic_not_found(exc):
        """HTTP 404 — route not found (generic Flask 404)."""
        body = make_error_body("NOT_FOUND", "The requested resource was not found")
        return jsonify(body), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(exc):
        """HTTP 405 — method not allowed (REQ-EVT-OA01 §4)."""
        body = make_error_body("METHOD_NOT_ALLOWED", "Method not allowed")
        return jsonify(body), 405

    return app


# --------------------------------------------------------------------------- main
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=config.PORT)
