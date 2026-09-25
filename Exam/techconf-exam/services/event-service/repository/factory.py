"""
repository/factory.py — Repository factory.

REQ-EVT-S01: selects the correct backend implementation based on the
STORAGE_BACKEND environment variable value passed from config.py.
"""
from __future__ import annotations

from repository.base import AbstractEventRepository


def create_repository(backend: str, data_dir: str) -> AbstractEventRepository:
    """Instantiate and return the appropriate repository implementation.

    Args:
        backend:  One of ``"memory"``, ``"json"``, or ``"sqlite"``.
        data_dir: Directory used by file-based backends (json / sqlite).
                  Ignored for the memory backend.

    Returns:
        A concrete ``AbstractEventRepository`` instance.

    Raises:
        NotImplementedError: For backends not yet implemented.
        ValueError:          For unrecognised backend names.
    """
    if backend == "memory":
        from repository.memory_repo import MemoryEventRepository
        return MemoryEventRepository()

    if backend == "json":
        raise NotImplementedError("json backend not yet implemented")

    if backend == "sqlite":
        raise NotImplementedError("sqlite backend not yet implemented")

    raise ValueError(f"Unknown storage backend: {backend!r}")
