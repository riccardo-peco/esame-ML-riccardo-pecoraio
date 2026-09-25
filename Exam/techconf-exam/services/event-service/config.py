"""
config.py — reads all runtime configuration from environment variables at startup.
No hard-coded values other than the defaults documented here (REQ-EVT-CFG01).
"""
import os

# TCP port the service listens on (REQ-EVT-CFG01 §1, §2)
PORT: int = int(os.environ.get("PORT", 5002))

# Storage backend selection: "memory" | "json" | "sqlite" (REQ-EVT-S01)
STORAGE_BACKEND: str = os.environ.get("STORAGE_BACKEND", "memory")

# Directory used by json/sqlite backends to persist data (REQ-EVT-S01)
DATA_DIR: str = os.environ.get("DATA_DIR", "./data")

# Base URL of the user-service used to validate organizers (REQ-EVT-CFG01 §3, §4)
USER_SERVICE_URL: str = os.environ.get("USER_SERVICE_URL", "http://localhost:5001")
