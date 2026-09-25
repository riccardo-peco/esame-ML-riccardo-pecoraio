"""
app.py — Flask application entry-point for user-service.
"""
from flask import Flask, jsonify

import config
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

    return app


# --------------------------------------------------------------------------- main
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=config.PORT)
