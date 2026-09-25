"""
tests/test_repository.py — Unit tests for the three storage backends.

REQ-USR-S01 §5: All backends (memory, json, sqlite) SHALL expose the same
behaviour. This suite enforces that by running one parametrized test suite
against every implementation. json and sqlite use pytest's ``tmp_path`` as
their ``data_dir`` so no real files leak between tests.

Task: T-14
"""
from __future__ import annotations

import pytest

from domain.models import Role, User
from repository.json_repo import JsonUserRepository
from repository.memory_repo import MemoryUserRepository
from repository.sqlite_repo import SqliteUserRepository


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

@pytest.fixture(params=["memory", "json", "sqlite"])
def repo(request, tmp_path):
    """Yield a fresh repository for each of the three backends.

    json and sqlite are backed by pytest's per-test ``tmp_path`` directory.
    """
    backend = request.param
    if backend == "memory":
        return MemoryUserRepository()
    if backend == "json":
        return JsonUserRepository(str(tmp_path))
    return SqliteUserRepository(str(tmp_path))


@pytest.fixture(params=["json", "sqlite"])
def persistent_repo_factory(request, tmp_path):
    """Return a zero-arg factory that builds a NEW repo instance on the same
    ``data_dir`` for each call.

    Only the file-backed backends (json, sqlite) support persistence, so the
    memory backend is intentionally excluded here.
    """
    backend = request.param
    data_dir = str(tmp_path)

    def _factory():
        if backend == "json":
            return JsonUserRepository(data_dir)
        return SqliteUserRepository(data_dir)

    return _factory


def _make_user(
    first_name="Ada",
    last_name="Lovelace",
    email="ada@example.com",
    company="Analytical Engines",
    role=Role.attendee,
) -> User:
    """Build a User with server-generated id/timestamps."""
    return User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        company=company,
        role=role,
    )


# --------------------------------------------------------------------------- #
# add / get_by_id
# --------------------------------------------------------------------------- #

def test_add_then_get_by_id_returns_same_user(repo):
    user = _make_user()
    repo.add(user)

    fetched = repo.get_by_id(user.id)

    assert fetched is not None
    assert fetched.id == user.id
    assert fetched.first_name == user.first_name
    assert fetched.last_name == user.last_name
    assert fetched.email == user.email
    assert fetched.company == user.company
    assert fetched.role == user.role
    assert fetched.created_at == user.created_at
    assert fetched.updated_at == user.updated_at


def test_get_by_id_missing_returns_none(repo):
    assert repo.get_by_id("does-not-exist") is None


def test_add_duplicate_id_raises_value_error(repo):
    user = _make_user()
    repo.add(user)

    duplicate = _make_user(email="other@example.com")
    duplicate.id = user.id  # force the same id

    with pytest.raises(ValueError):
        repo.add(duplicate)


# --------------------------------------------------------------------------- #
# get_by_email (REQ-USR-B01 — case-insensitive)
# --------------------------------------------------------------------------- #

def test_get_by_email_is_case_insensitive(repo):
    user = _make_user(email="ada@example.com")
    repo.add(user)

    # stored lowercase, looked up with uppercase
    fetched = repo.get_by_email("ADA@EXAMPLE.COM")

    assert fetched is not None
    assert fetched.id == user.id
    assert fetched.email == "ada@example.com"


def test_get_by_email_missing_returns_none(repo):
    assert repo.get_by_email("nobody@example.com") is None


# --------------------------------------------------------------------------- #
# list_all
# --------------------------------------------------------------------------- #

def test_list_all_empty_returns_empty_list(repo):
    assert repo.list_all() == []


def test_list_all_returns_all_added_users(repo):
    u1 = _make_user(email="a@example.com")
    u2 = _make_user(email="b@example.com")
    u3 = _make_user(email="c@example.com")
    repo.add(u1)
    repo.add(u2)
    repo.add(u3)

    all_ids = {u.id for u in repo.list_all()}

    assert all_ids == {u1.id, u2.id, u3.id}
    assert len(repo.list_all()) == 3


# --------------------------------------------------------------------------- #
# update
# --------------------------------------------------------------------------- #

def test_update_modifies_existing_user_and_returns_updated(repo):
    user = _make_user(first_name="Ada", role=Role.attendee)
    repo.add(user)

    user.first_name = "Augusta"
    user.role = Role.speaker
    user.updated_at = "2099-01-01T00:00:00.000Z"

    returned = repo.update(user)

    assert returned.first_name == "Augusta"
    assert returned.role == Role.speaker

    fetched = repo.get_by_id(user.id)
    assert fetched is not None
    assert fetched.first_name == "Augusta"
    assert fetched.role == Role.speaker
    assert fetched.updated_at == "2099-01-01T00:00:00.000Z"


def test_update_missing_id_raises_key_error(repo):
    user = _make_user()  # never added
    with pytest.raises(KeyError):
        repo.update(user)


# --------------------------------------------------------------------------- #
# delete
# --------------------------------------------------------------------------- #

def test_delete_existing_returns_true_and_removes(repo):
    user = _make_user()
    repo.add(user)

    assert repo.delete(user.id) is True
    assert repo.get_by_id(user.id) is None


def test_delete_missing_returns_false(repo):
    assert repo.delete("does-not-exist") is False


# --------------------------------------------------------------------------- #
# Persistence round-trip (json + sqlite only)
# --------------------------------------------------------------------------- #

def test_persistence_round_trip(persistent_repo_factory):
    """After add, a NEW repo instance on the same data_dir still sees the user.

    This verifies real file persistence for the json and sqlite backends
    (REQ-USR-S01 §2, §3).
    """
    repo_a = persistent_repo_factory()
    user = _make_user(email="persist@example.com")
    repo_a.add(user)

    # Fresh instance pointing at the same data_dir
    repo_b = persistent_repo_factory()

    fetched = repo_b.get_by_id(user.id)
    assert fetched is not None
    assert fetched.id == user.id
    assert fetched.email == "persist@example.com"

    # And uniqueness lookup survives the round-trip too
    assert repo_b.get_by_email("PERSIST@EXAMPLE.COM") is not None
