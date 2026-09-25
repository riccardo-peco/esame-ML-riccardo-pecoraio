"""
app.py — Flask application entry-point for user-service.
"""
from flask import Flask, jsonify

import config


def create_app() -> Flask:
    """Application factory."""
    app = Flask(__name__)

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
