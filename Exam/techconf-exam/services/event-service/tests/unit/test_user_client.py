"""
Unit tests for clients/user_client.py — all HTTP calls mocked with `responses`.

Requirements: REQ-EVT-B01, REQ-EVT-B02, REQ-EVT-B05.
"""
import pytest
import requests
import responses

from clients.user_client import UserClient
from errors import (
    ReferenceNotFoundError,
    InvalidOrganizerError,
    DependencyUnavailableError,
)

BASE_URL = "http://user-service.test"
ORG_ID = "11111111-1111-4111-8111-111111111111"
URL = f"{BASE_URL}/api/v1/users/{ORG_ID}"


@responses.activate
def test_valid_organizer_returns_none():
    """REQ-EVT-B01: 200 with role=organizer → no exception."""
    responses.add(responses.GET, URL, json={"id": ORG_ID, "role": "organizer"}, status=200)
    client = UserClient(BASE_URL)
    assert client.validate_organizer(ORG_ID) is None


@responses.activate
def test_non_organizer_role_raises_invalid_organizer():
    """REQ-EVT-B01: 200 with role=attendee → InvalidOrganizerError."""
    responses.add(responses.GET, URL, json={"id": ORG_ID, "role": "attendee"}, status=200)
    client = UserClient(BASE_URL)
    with pytest.raises(InvalidOrganizerError):
        client.validate_organizer(ORG_ID)


@responses.activate
def test_missing_user_raises_reference_not_found():
    """REQ-EVT-B01/B02: 404 → ReferenceNotFoundError."""
    responses.add(responses.GET, URL, json={"error": {"code": "NOT_FOUND"}}, status=404)
    client = UserClient(BASE_URL)
    with pytest.raises(ReferenceNotFoundError):
        client.validate_organizer(ORG_ID)


@responses.activate
def test_server_error_raises_dependency_unavailable():
    """REQ-EVT-B05: 5xx → DependencyUnavailableError."""
    responses.add(responses.GET, URL, status=500)
    client = UserClient(BASE_URL)
    with pytest.raises(DependencyUnavailableError):
        client.validate_organizer(ORG_ID)


@responses.activate
def test_connection_error_raises_dependency_unavailable():
    """REQ-EVT-B05: connection failure → DependencyUnavailableError."""
    responses.add(responses.GET, URL, body=requests.exceptions.ConnectionError("refused"))
    client = UserClient(BASE_URL)
    with pytest.raises(DependencyUnavailableError):
        client.validate_organizer(ORG_ID)


@responses.activate
def test_timeout_raises_dependency_unavailable():
    """REQ-EVT-B05: timeout → DependencyUnavailableError."""
    responses.add(responses.GET, URL, body=requests.exceptions.Timeout("timed out"))
    client = UserClient(BASE_URL)
    with pytest.raises(DependencyUnavailableError):
        client.validate_organizer(ORG_ID)


def test_base_url_trailing_slash_is_stripped():
    """URL join stays robust when base_url has a trailing slash."""
    client = UserClient(BASE_URL + "/")
    assert client.base_url == BASE_URL
