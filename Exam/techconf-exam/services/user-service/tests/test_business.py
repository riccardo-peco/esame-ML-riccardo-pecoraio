"""
tests/test_business.py — HTTP-level unit tests for user-service business rules.

Uses Flask's test client against ``create_app()`` with the default in-memory
backend. Each test gets a fresh app (and therefore a fresh MemoryUserRepository),
so tests are fully isolated.

Covers:
    REQ-USR-C01  — user creation (POST)
    REQ-USR-V01  — field validation constraints
    REQ-USR-B01  — email uniqueness (case-insensitive)
    REQ-USR-B02  — email lowercase normalisation
    REQ-USR-B03  — list, pagination, filters
    REQ-USR-C02  — retrieve single user (GET /{id})
    REQ-USR-C03  — full replacement (PUT)
    REQ-USR-C04  — partial update (PATCH)
    REQ-USR-C05  — delete (DELETE)

Task: T-15
"""
from __future__ import annotations

import json

import pytest

from app import create_app


# --------------------------------------------------------------------------- #
# Fixtures & helpers
# --------------------------------------------------------------------------- #

@pytest.fixture
def client():
    """Fresh test client per test (fresh in-memory repo → full isolation)."""
    app = create_app()  # memory backend by default
    app.config.update(TESTING=True)
    return app.test_client()


def _valid_body(**overrides):
    """A minimal valid create body; override any field via kwargs."""
    body = {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": "ada@example.com",
        "company": "Analytical Engines",
    }
    body.update(overrides)
    return body


def _create(client, **overrides):
    """POST a user and return the Flask test response."""
    return client.post("/api/v1/users", json=_valid_body(**overrides))


def _error_code(resp):
    """Extract the error code from an Error_Body response."""
    return resp.get_json()["error"]["code"]


# --------------------------------------------------------------------------- #
# Creation — REQ-USR-C01
# --------------------------------------------------------------------------- #

def test_create_valid_returns_201_with_location_and_fields(client):
    resp = _create(client)

    assert resp.status_code == 201
    assert resp.headers.get("Location", "").startswith("/api/v1/users/")

    body = resp.get_json()
    assert body["id"]
    assert body["created_at"]
    assert body["updated_at"]
    assert body["first_name"] == "Ada"
    assert body["email"] == "ada@example.com"
    # REQ-USR-C01 §7: default role
    assert body["role"] == "attendee"
    # Location header references the created id
    assert resp.headers["Location"] == f"/api/v1/users/{body['id']}"


@pytest.mark.parametrize("missing", ["first_name", "last_name", "email"])
def test_create_missing_required_field_returns_422(client, missing):
    body = _valid_body()
    del body[missing]
    resp = client.post("/api/v1/users", json=body)

    assert resp.status_code == 422
    assert _error_code(resp) == "VALIDATION_ERROR"


def test_create_malformed_json_returns_400(client):
    resp = client.post(
        "/api/v1/users",
        data="{not valid json",
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_create_invalid_role_returns_422(client):
    resp = _create(client, role="wizard")
    assert resp.status_code == 422
    assert _error_code(resp) == "VALIDATION_ERROR"


@pytest.mark.parametrize("role", ["speaker", "organizer"])
def test_create_explicit_valid_role_returns_201_with_role(client, role):
    resp = _create(client, email=f"{role}@example.com", role=role)
    assert resp.status_code == 201
    assert resp.get_json()["role"] == role


def test_create_ignores_client_supplied_server_fields(client):
    resp = client.post(
        "/api/v1/users",
        json=_valid_body(
            id="client-chosen-id",
            created_at="2000-01-01T00:00:00.000Z",
            updated_at="2000-01-01T00:00:00.000Z",
        ),
    )
    assert resp.status_code == 201
    body = resp.get_json()
    # REQ-USR-V01 §5: server generates its own values
    assert body["id"] != "client-chosen-id"
    assert body["created_at"] != "2000-01-01T00:00:00.000Z"
    assert body["updated_at"] != "2000-01-01T00:00:00.000Z"


# --------------------------------------------------------------------------- #
# Field validation — REQ-USR-V01
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("field", ["first_name", "last_name"])
@pytest.mark.parametrize("value", ["", "x" * 51])
def test_name_length_bounds_return_422(client, field, value):
    resp = _create(client, **{field: value})
    assert resp.status_code == 422
    assert _error_code(resp) == "VALIDATION_ERROR"


@pytest.mark.parametrize("field", ["first_name", "last_name"])
@pytest.mark.parametrize("value", ["a", "x" * 50])
def test_name_length_bounds_valid_return_201(client, field, value):
    resp = _create(client, **{field: value})
    assert resp.status_code == 201


@pytest.mark.parametrize("bad_email", ["not-an-email", "missing@domain", "@example.com", "a@b"])
def test_invalid_email_format_returns_422(client, bad_email):
    resp = _create(client, email=bad_email)
    assert resp.status_code == 422
    assert _error_code(resp) == "VALIDATION_ERROR"


def test_company_too_long_returns_422(client):
    resp = _create(client, company="x" * 101)
    assert resp.status_code == 422
    assert _error_code(resp) == "VALIDATION_ERROR"


def test_company_max_length_valid_returns_201(client):
    resp = _create(client, company="x" * 100)
    assert resp.status_code == 201


# --------------------------------------------------------------------------- #
# Uniqueness & normalisation — REQ-USR-B01, REQ-USR-B02
# --------------------------------------------------------------------------- #

def test_duplicate_email_same_case_returns_409(client):
    assert _create(client, email="dup@example.com").status_code == 201
    resp = _create(client, email="dup@example.com", first_name="Other")
    assert resp.status_code == 409
    assert _error_code(resp) == "EMAIL_ALREADY_EXISTS"


def test_duplicate_email_different_case_returns_409(client):
    assert _create(client, email="dup@example.com").status_code == 201
    resp = _create(client, email="DUP@EXAMPLE.COM", first_name="Other")
    assert resp.status_code == 409
    assert _error_code(resp) == "EMAIL_ALREADY_EXISTS"


def test_email_stored_and_returned_lowercase(client):
    resp = _create(client, email="MixedCase@Example.COM")
    assert resp.status_code == 201
    assert resp.get_json()["email"] == "mixedcase@example.com"


# --------------------------------------------------------------------------- #
# List + pagination + filters — REQ-USR-B03
# --------------------------------------------------------------------------- #

def test_list_returns_page_shape(client):
    _create(client, email="a@example.com")
    _create(client, email="b@example.com")

    resp = client.get("/api/v1/users")
    assert resp.status_code == 200
    body = resp.get_json()
    assert set(["items", "page", "page_size", "total"]).issubset(body.keys())
    assert body["total"] == 2
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert len(body["items"]) == 2


@pytest.mark.parametrize("bad_size", [0, 101])
def test_page_size_out_of_bounds_returns_422(client, bad_size):
    resp = client.get(f"/api/v1/users?page_size={bad_size}")
    assert resp.status_code == 422
    assert _error_code(resp) == "VALIDATION_ERROR"


def test_page_zero_returns_422(client):
    resp = client.get("/api/v1/users?page=0")
    assert resp.status_code == 422
    assert _error_code(resp) == "VALIDATION_ERROR"


def test_pagination_slices_results(client):
    for i in range(5):
        _create(client, email=f"user{i}@example.com")

    resp = client.get("/api/v1/users?page=1&page_size=2")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["total"] == 5
    assert body["page_size"] == 2
    assert len(body["items"]) == 2

    resp3 = client.get("/api/v1/users?page=3&page_size=2")
    assert len(resp3.get_json()["items"]) == 1  # 5 items → last page has 1


def test_role_filter_returns_only_matching(client):
    _create(client, email="a@example.com", role="attendee")
    _create(client, email="s@example.com", role="speaker")
    _create(client, email="o@example.com", role="organizer")

    resp = client.get("/api/v1/users?role=speaker")
    assert resp.status_code == 200
    items = resp.get_json()["items"]
    assert len(items) == 1
    assert items[0]["role"] == "speaker"


def test_invalid_role_filter_returns_422(client):
    resp = client.get("/api/v1/users?role=wizard")
    assert resp.status_code == 422
    assert _error_code(resp) == "VALIDATION_ERROR"


def test_email_filter_is_case_insensitive(client):
    _create(client, email="findme@example.com")
    _create(client, email="other@example.com")

    resp = client.get("/api/v1/users?email=FINDME@EXAMPLE.COM")
    assert resp.status_code == 200
    items = resp.get_json()["items"]
    assert len(items) == 1
    assert items[0]["email"] == "findme@example.com"


# --------------------------------------------------------------------------- #
# Retrieve — REQ-USR-C02
# --------------------------------------------------------------------------- #

def test_get_existing_returns_200(client):
    created = _create(client).get_json()
    resp = client.get(f"/api/v1/users/{created['id']}")
    assert resp.status_code == 200
    assert resp.get_json()["id"] == created["id"]


def test_get_missing_returns_404(client):
    resp = client.get("/api/v1/users/nonexistent")
    assert resp.status_code == 404
    assert _error_code(resp) == "NOT_FOUND"


# --------------------------------------------------------------------------- #
# Full replacement (PUT) — REQ-USR-C03
# --------------------------------------------------------------------------- #

def test_put_full_replacement_returns_200_and_updates_timestamp(client):
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
    body = resp.get_json()
    assert body["first_name"] == "Augusta"
    assert body["email"] == "augusta@example.com"
    assert body["role"] == "speaker"
    # created_at preserved; updated_at refreshed to a current timestamp.
    # Timestamps have millisecond resolution, so within the same millisecond the
    # value can equal created_at — assert monotonic (>=) rather than strict >.
    assert body["created_at"] == created["created_at"]
    assert body["updated_at"] >= created["updated_at"]


def test_put_missing_required_field_returns_422(client):
    created = _create(client).get_json()
    resp = client.put(
        f"/api/v1/users/{created['id']}",
        json={"first_name": "Augusta", "last_name": "King"},  # no email
    )
    assert resp.status_code == 422
    assert _error_code(resp) == "VALIDATION_ERROR"


def test_put_missing_user_returns_404(client):
    resp = client.put(
        "/api/v1/users/nonexistent",
        json={"first_name": "A", "last_name": "B", "email": "a@example.com"},
    )
    assert resp.status_code == 404
    assert _error_code(resp) == "NOT_FOUND"


def test_put_email_conflict_returns_409(client):
    first = _create(client, email="first@example.com").get_json()
    _create(client, email="second@example.com")

    resp = client.put(
        f"/api/v1/users/{first['id']}",
        json={
            "first_name": "First",
            "last_name": "User",
            "email": "second@example.com",  # belongs to another user
        },
    )
    assert resp.status_code == 409
    assert _error_code(resp) == "EMAIL_ALREADY_EXISTS"


def test_put_malformed_json_returns_400(client):
    created = _create(client).get_json()
    resp = client.put(
        f"/api/v1/users/{created['id']}",
        data="{bad",
        content_type="application/json",
    )
    assert resp.status_code == 400


# --------------------------------------------------------------------------- #
# Partial update (PATCH) — REQ-USR-C04
# --------------------------------------------------------------------------- #

def test_patch_partial_updates_only_supplied_field(client):
    created = _create(client).get_json()

    resp = client.patch(
        f"/api/v1/users/{created['id']}",
        json={"first_name": "Grace"},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["first_name"] == "Grace"
    # other fields unchanged
    assert body["last_name"] == created["last_name"]
    assert body["email"] == created["email"]
    assert body["created_at"] == created["created_at"]
    # updated_at refreshed to a current timestamp (>= due to ms resolution)
    assert body["updated_at"] >= created["updated_at"]


def test_patch_missing_user_returns_404(client):
    resp = client.patch("/api/v1/users/nonexistent", json={"first_name": "X"})
    assert resp.status_code == 404
    assert _error_code(resp) == "NOT_FOUND"


def test_patch_invalid_field_value_returns_422(client):
    created = _create(client).get_json()
    resp = client.patch(
        f"/api/v1/users/{created['id']}",
        json={"email": "not-an-email"},
    )
    assert resp.status_code == 422
    assert _error_code(resp) == "VALIDATION_ERROR"


def test_patch_email_conflict_returns_409(client):
    first = _create(client, email="first@example.com").get_json()
    _create(client, email="second@example.com")

    resp = client.patch(
        f"/api/v1/users/{first['id']}",
        json={"email": "second@example.com"},
    )
    assert resp.status_code == 409
    assert _error_code(resp) == "EMAIL_ALREADY_EXISTS"


def test_patch_no_recognised_fields_returns_200_unchanged(client):
    created = _create(client).get_json()
    resp = client.patch(
        f"/api/v1/users/{created['id']}",
        json={"unknown_field": "whatever"},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["first_name"] == created["first_name"]
    assert body["updated_at"] == created["updated_at"]  # left unchanged


# --------------------------------------------------------------------------- #
# Delete — REQ-USR-C05
# --------------------------------------------------------------------------- #

def test_delete_existing_returns_204_then_get_404(client):
    created = _create(client).get_json()

    resp = client.delete(f"/api/v1/users/{created['id']}")
    assert resp.status_code == 204
    assert resp.data == b""

    # subsequent GET → 404
    resp_get = client.get(f"/api/v1/users/{created['id']}")
    assert resp_get.status_code == 404
    assert _error_code(resp_get) == "NOT_FOUND"


def test_delete_missing_returns_404(client):
    resp = client.delete("/api/v1/users/nonexistent")
    assert resp.status_code == 404
    assert _error_code(resp) == "NOT_FOUND"
