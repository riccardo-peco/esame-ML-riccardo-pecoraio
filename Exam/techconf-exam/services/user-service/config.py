"""
config.py — reads all runtime configuration from environment variables at startup.
No hard-coded values other than the defaults documented here.
"""
import os

# TCP port the service listens on (REQ-USR-CFG01)
PORT: int = int(os.environ.get("PORT", 5001))

# Storage backend selection: "memory" | "json" | "sqlite" (REQ-USR-S01)
STORAGE_BACKEND: str = os.environ.get("STORAGE_BACKEND", "memory")

# Directory used by json/sqlite backends to persist data (REQ-USR-S01)
DATA_DIR: str = os.environ.get("DATA_DIR", "./data")
