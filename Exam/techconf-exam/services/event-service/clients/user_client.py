"""
clients/user_client.py — HTTP client to the user-service, isolated behind a small
interface so it can be mocked with the `responses` library in unit tests.

The client reads NOTHING from the environment directly: the caller passes `base_url`
(from config.USER_SERVICE_URL). This keeps it fully mockable.

Requirements: REQ-EVT-B01, REQ-EVT-B02, REQ-EVT-B05.
"""
import requests

from errors import (
    ReferenceNotFoundError,
    InvalidOrganizerError,
    DependencyUnavailableError,
)


class UserClient:
    """Thin HTTP client used to validate an Event's organizer against user-service."""

    def __init__(self, base_url: str, timeout: float = 2.0):
        # strip trailing slash so the URL join stays robust
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def validate_organizer(self, organizer_id: str) -> None:
        """
        Validate that `organizer_id` references an existing user with role == "organizer".

        Returns None when the organizer is valid, otherwise raises a domain exception:
          * InvalidOrganizerError      — user exists but role != "organizer"
          * ReferenceNotFoundError     — user does not exist (HTTP 404)
          * DependencyUnavailableError — user-service unreachable, timed out, or 5xx
        """
        url = f"{self.base_url}/api/v1/users/{organizer_id}"
        try:
            response = requests.get(url, timeout=self.timeout)
        except requests.exceptions.RequestException:
            # covers Timeout, ConnectionError (connection refused), and any other
            # transport-level failure
            raise DependencyUnavailableError("user-service is unreachable")

        status = response.status_code
        if status == 200:
            body = response.json()
            if body.get("role") != "organizer":
                raise InvalidOrganizerError(
                    f"user {organizer_id} is not an organizer"
                )
            return None
        if status == 404:
            raise ReferenceNotFoundError(f"organizer {organizer_id} not found")
        if status >= 500:
            raise DependencyUnavailableError("user-service returned a server error")

        # any other unexpected status is treated as a dependency failure
        raise DependencyUnavailableError(
            f"unexpected status {status} from user-service"
        )
