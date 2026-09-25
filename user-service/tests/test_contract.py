"""
tests/test_contract.py — OpenAPI contract-conformance tests for user-service.

Each test issues a real request through Flask's test client (fresh app / memory
backend) and validates the response against the OpenAPI contract using the
non-modifiable helper ``contracts.validator.assert_matches_contract``.

Covers at least one contract check per endpoint/operation plus a couple of
error-path checks:

    GET    /health                 -> 200  (Health)
    POST   /api/v1/users           -> 201  (User)
    POST   /api/v1/users           -> 422  (Error)
    GET    /api/v1/users           -> 200  (UserPage)
    GET    /api/v1/users/{id}      -> 200  (User)
    GET    /api/v1/users/{id}      -> 404  (Error)
    PUT    /api/v1/users/{id}      -> 200  (User)
    PATCH  /api/v1/users/{id}      -> 200  (User)
    DELETE /api/v1/users/{id}      -> 204  (no body)

Requirements: REQ-USR-OA01 (Response Contract Conformance)
Task: T-16
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# --------------------------------------------------------------------------- #
# Make the non-modifiable contract validator importable.
#
# Layout:
#   <repo>/user-service/tests/test_contract.py   (this file)
#   <repo>/Exam/techconf-exam/contracts/validator.py
#
# parents[2] of this file is the repo root, so we resolve the contracts dir
# relative to it (robust to a moved checkout). Falls back to an absolute path
# for the known exam layout if the relative resolution does not exist.
# --------------------------------------------------------------------------- #
_REPO_ROOT = Path(__file__).resolve().parents[2]
_CONTRACTS_DIR = _REPO_ROOT / "Exam" / "techconf-exam" / "contracts"
if not _CONTRACTS_DIR.is_dir():
    _CONTRACTS_DIR = Path(
        r"c:\Users\riccardo.pecoraio\Documents\esame-ML-riccardo-pecoraio"
        r"\esame-ML-riccardo-pecoraio\Exam\techconf-exam\contracts"
    )
if str(_CONTRACTS_DIR) not in sys.path:
    sys.path.insert(0, str(_CONTRACTS_DIR))

from validator import assert_matches_contract  # noqa: E402

from app import create_app  # noqa: E402


# --------------------------------------------------------------------------- #
# Fixtures & helpers
# --------------------------------------------------------------------------- #

_SERVICE = "user-service"


@pytest.fixture
def client():
    """Fresh test client per test (fresh in-memory repo → full isolation)."""
    app = create_app()  # memory backend by default
    app.config.update(TESTING=True)
    return app.test_client()


def _to_contract_response(flask_resp):
    """Adapt a Flask test-client response to the dict form the validator accepts.

    The validator expects either a ``requests.Response``-like object with a
    ``json()`` method, or a plain dict with ``status_code`` / ``headers`` /
    ``json`` keys. Flask exposes ``get_json()`` (not ``json()``), so we build
    the dict form here.
    """
    return {
        "status_code": flask_resp.status_code,
        "headers": dict(flask_resp.headers),
        "json": flask_resp.get_json(silent=True),
    }


def _valid_body(**overrides):
    body = {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": "ada@example.com",
        "company": "Analytical Engines",
    }
    body.update(overrides)
    return body


def _create(client, **overrides):
    return client.post("/api/v1/users", json=_valid_body(**overrides))


# --------------------------------------------------------------------------- #
# Health — GET /health -> 200
# --------------------------------------------------------------------------- #

def test_health_matches_contract(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert_matches_contract(_SERVICE, "GET", "/health", _to_contract_response(resp))


# --------------------------------------------------------------------------- #
# Create — POST /api/v1/users -> 201 (User) and -> 422 (Error)
# --------------------------------------------------------------------------- #

def test_create_user_matches_contract(client):
    resp = _create(client)
    assert resp.status_code == 201
    assert_matches_contract(_SERVICE, "POST", "/api/v1/users", _to_contract_response(resp))


def test_create_user_validation_error_matches_contract(client):
    body = _valid_body()
    del body["email"]
    resp = client.post("/api/v1/users", json=body)
    assert resp.status_code == 422
    assert_matches_contract(_SERVICE, "POST", "/api/v1/users", _to_contract_response(resp))


# --------------------------------------------------------------------------- #
# List — GET /api/v1/users -> 200 (UserPage)
# --------------------------------------------------------------------------- #

def test_list_users_matches_contract(client):
    _create(client, email="a@example.com")
    _create(client, email="b@example.com")
    resp = client.get("/api/v1/users")
    assert resp.status_code == 200
    assert_matches_contract(_SERVICE, "GET", "/api/v1/users", _to_contract_response(resp))


# --------------------------------------------------------------------------- #
# Retrieve — GET /api/v1/users/{id} -> 200 (User) and -> 404 (Error)
# --------------------------------------------------------------------------- #

def test_get_user_matches_contract(client):
    created = _create(client).get_json()
    resp = client.get(f"/api/v1/users/{created['id']}")
    assert resp.status_code == 200
    assert_matches_contract(
        _SERVICE, "GET", f"/api/v1/users/{created['id']}", _to_contract_response(resp)
    )


def test_get_user_not_found_matches_contract(client):
    resp = client.get("/api/v1/users/00000000-0000-4000-8000-000000000000")
    assert resp.status_code == 404
    assert_matches_contract(
        _SERVICE,
        "GET",
        "/api/v1/users/00000000-0000-4000-8000-000000000000",
        _to_contract_response(resp),
    )


# --------------------------------------------------------------------------- #
# Replace — PUT /api/v1/users/{id} -> 200 (User)
# --------------------------------------------------------------------------- #

def test_put_user_matches_contract(client):
    created = _create(client).get_json()
    resp = client.put(
        f"/api/v1/users/{created['id']}",
        json={
            "first_name": "Augusta",
            "last_name": "King",
            "email": "augusta@example.com",
            "role": "speaker",
        },
    )
    assert resp.status_code == 200
    assert_matches_contract(
        _SERVICE, "PUT", f"/api/v1/users/{created['id']}", _to_contract_response(resp)
    )


# --------------------------------------------------------------------------- #
# Partial update — PATCH /api/v1/users/{id} -> 200 (User)
# --------------------------------------------------------------------------- #

def test_patch_user_matches_contract(client):
    created = _create(client).get_json()
    resp = client.patch(
        f"/api/v1/users/{created['id']}",
        json={"first_name": "Grace"},
    )
    assert resp.status_code == 200
    assert_matches_contract(
        _SERVICE, "PATCH", f"/api/v1/users/{created['id']}", _to_contract_response(resp)
    )


# --------------------------------------------------------------------------- #
# Delete — DELETE /api/v1/users/{id} -> 204 (no body)
# --------------------------------------------------------------------------- #

def test_delete_user_matches_contract(client):
    created = _create(client).get_json()
    resp = client.delete(f"/api/v1/users/{created['id']}")
    assert resp.status_code == 204
    assert_matches_contract(
        _SERVICE, "DELETE", f"/api/v1/users/{created['id']}", _to_contract_response(resp)
    )
