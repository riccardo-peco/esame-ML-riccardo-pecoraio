"""
repository/factory.py — Repository factory.

REQ-USR-S01: selects the correct backend implementation based on the
STORAGE_BACKEND environment variable value passed from config.py.
"""
from __future__ import annotations

from repository.base import AbstractUserRepository


def create_repository(backend: str, data_dir: str) -> AbstractUserRepository:
    """Instantiate and return the appropriate repository implementation.

    Args:
        backend:  One of ``"memory"``, ``"json"``, or ``"sqlite"``.
        data_dir: Directory used by file-based backends (json / sqlite).
                  Ignored for the memory backend.

    Returns:
        A concrete ``AbstractUserRepository`` instance.

    Raises:
        NotImplementedError: For backends not yet implemented (json, sqlite).
        ValueError:          For unrecognised backend names.
    """
    if backend == "memory":
        from repository.memory_repo import MemoryUserRepository
        return MemoryUserRepository()

    if backend == "json":
        from repository.json_repo import JsonUserRepository
        return JsonUserRepository(data_dir)

    if backend == "sqlite":
        raise NotImplementedError("sqlite backend not yet implemented")

    raise ValueError(f"Unknown storage backend: {backend!r}")
