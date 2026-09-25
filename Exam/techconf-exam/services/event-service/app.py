"""
app.py — Flask application entry-point for event-service.

Runnable with `python -m app` from the service root (see services.yaml).
"""
from flask import Flask, jsonify

import config


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

    return app


# --------------------------------------------------------------------------- main
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=config.PORT)
