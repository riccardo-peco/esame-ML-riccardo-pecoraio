"""
app.py — Flask application entry-point for user-service.
"""
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

import config
from errors import ConflictError, NotFoundError, ValidationError, make_error_body
from repository.factory import create_repository


def create_app() -> Flask:
    """Application factory."""
    app = Flask(__name__)

    # ------------------------------------------------ repository (REQ-USR-S01)
    # Instantiate once at startup; route handlers access it via current_app.repo
    app.repo = create_repository(config.STORAGE_BACKEND, config.DATA_DIR)  # type: ignore[attr-defined]

    # ------------------------------------------------------------------ health
    @app.get("/health")
    def health():
        """GET /health — REQ-USR-H01.
        Always responds 200 regardless of the storage backend state.
        """
        return jsonify({"status": "ok", "service": "user-service"}), 200

    # --------------------------------------------------------- error handlers
    @app.errorhandler(ValidationError)
    def handle_validation_error(exc: ValidationError):
        """HTTP 422 — field-level validation failure (REQ-USR-C01 §4, §6)."""
        body = make_error_body("VALIDATION_ERROR", exc.message, exc.details)
        return jsonify(body), 422

    @app.errorhandler(NotFoundError)
    def handle_not_found_error(exc: NotFoundError):
        """HTTP 404 — resource not found (REQ-USR-C02 §2)."""
        body = make_error_body("NOT_FOUND", exc.message)
        return jsonify(body), 404

    @app.errorhandler(ConflictError)
    def handle_conflict_error(exc: ConflictError):
        """HTTP 409 — email uniqueness violation (REQ-USR-B01)."""
        body = make_error_body("EMAIL_ALREADY_EXISTS", exc.message)
        return jsonify(body), 409

    @app.errorhandler(400)
    def handle_bad_request(exc):
        """HTTP 400 — malformed JSON or bad request (REQ-USR-C01 §5)."""
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
        """HTTP 405 — method not allowed."""
        body = make_error_body("METHOD_NOT_ALLOWED", "Method not allowed")
        return jsonify(body), 405

    return app


# --------------------------------------------------------------------------- main
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=config.PORT)
