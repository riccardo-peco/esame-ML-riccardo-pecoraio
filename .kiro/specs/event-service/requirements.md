# Requirements Document

## Introduction

The event-service is a mandatory microservice of the TechConf platform. It manages
conferences (events) with a lifecycle and a fixed capacity. It is called by the
registration-service and the feedback-service, and it in turn calls the user-service to
validate that the declared organizer exists and holds the `organizer` role. The service
exposes a REST API at `/api/v1/events` on port 5002, conforms to the OpenAPI contract in
`contracts/openapi/event-service.yaml`, and must pass all IT-E01..IT-E08 acceptance tests
(and participates in the end-to-end IT-J01/IT-J02 flows).

---

## Glossary

- **Event_Service**: The microservice described in this document; listens on the port
  provided by the `PORT` environment variable (default `5002`).
- **Event**: A conference resource with fields `id`, `title`, `description`,
  `organizer_id`, `venue`, `city`, `start_date`, `end_date`, `capacity`, `price`,
  `status`, `created_at`, `updated_at`.
- **Event_Status**: An enumerated value — `draft` (default), `published`, or `cancelled`.
- **Organizer**: A User in the User_Service whose `role` equals `organizer`.
- **User_Service**: The external microservice at the URL given by `USER_SERVICE_URL`
  (default `http://localhost:5001`), queried to validate an Event's `organizer_id`.
- **Repository**: The storage layer abstraction that isolates persistence from business
  logic; implementations: `memory`, `json`, `sqlite`.
- **Storage_Backend**: Runtime selection of the Repository implementation via the
  `STORAGE_BACKEND` environment variable (`memory` | `json` | `sqlite`).
- **Page**: A paginated slice of a collection with fields `items`, `page`, `page_size`,
  `total`.
- **Error_Body**: A JSON object `{"error": {"code": "UPPER_SNAKE", "message": "...",
  "details": {...}}}`.

---

## Requirements

---

### Requirement 1: Event Creation (REQ-EVT-C01)

**User Story:** As an event organizer, I want to create a conference event, so that
participants can later register for it.

#### Acceptance Criteria

1. WHEN a `POST /api/v1/events` request is received with a valid JSON body containing
   `title`, `organizer_id`, `venue`, `city`, `start_date`, `end_date`, `capacity`, and
   `price`, THE Event_Service SHALL create the Event, persist it via the Repository, and
   respond with HTTP 201.

2. WHEN an Event is created successfully, THE Event_Service SHALL include a `Location`
   header containing the URL of the new resource (e.g. `/api/v1/events/{id}`).

3. WHEN an Event is created successfully, THE Event_Service SHALL return the full Event
   object conforming to the `Event` schema in the OpenAPI contract, including server-
   generated fields `id` (UUID v4), `created_at`, and `updated_at` (ISO 8601 UTC).

4. WHEN a `POST /api/v1/events` request body omits any required field (`title`,
   `organizer_id`, `venue`, `city`, `start_date`, `end_date`, `capacity`, `price`), THE
   Event_Service SHALL respond with HTTP 422 and an Error_Body with
   `code = "VALIDATION_ERROR"`.

5. WHEN a `POST /api/v1/events` request body contains malformed JSON (not parseable),
   THE Event_Service SHALL respond with HTTP 400 and an Error_Body.

6. WHEN a `POST /api/v1/events` request body omits the `status` field, THE Event_Service
   SHALL default the Event's `status` to `draft`.

7. WHEN a `POST /api/v1/events` request body contains a `status` field, THE
   Event_Service SHALL accept only the values `draft`, `published`, and `cancelled`.

---

### Requirement 2: Organizer Reference Validation (REQ-EVT-B01, REQ-EVT-B02, REQ-EVT-B05)

**User Story:** As a platform administrator, I want every event to reference a real
organizer, so that only authorised users can own events.

#### Acceptance Criteria

1. WHEN a `POST /api/v1/events` request is received, THE Event_Service SHALL validate the
   supplied `organizer_id` by calling `GET {USER_SERVICE_URL}/api/v1/users/{organizer_id}`
   with a 2-second timeout.

2. IF the User_Service responds with HTTP 404 for the supplied `organizer_id`, THEN THE
   Event_Service SHALL respond with HTTP 422 and an Error_Body with
   `code = "REFERENCE_NOT_FOUND"`.

3. IF the User_Service returns a User whose `role` is not `organizer`, THEN THE
   Event_Service SHALL respond with HTTP 422 and an Error_Body with
   `code = "INVALID_ORGANIZER"`.

4. IF the User_Service is unreachable (connection refused, timeout, or HTTP 5xx) during
   organizer validation, THEN THE Event_Service SHALL respond with HTTP 503 and an
   Error_Body with `code = "DEPENDENCY_UNAVAILABLE"`.

5. WHEN a `PUT /api/v1/events/{id}` or `PATCH /api/v1/events/{id}` request changes the
   `organizer_id` to a new value, THE Event_Service SHALL re-validate the new
   `organizer_id` against the User_Service using the same rules as on creation.

6. WHEN a `PUT /api/v1/events/{id}` or `PATCH /api/v1/events/{id}` request does not change
   the `organizer_id`, THE Event_Service SHALL NOT call the User_Service for organizer
   validation.

---

### Requirement 3: Date Range Validation (REQ-EVT-B03)

**User Story:** As an organizer, I want the event dates to be consistent, so that an event
never ends before it starts.

#### Acceptance Criteria

1. WHEN a `POST`, `PUT`, or `PATCH` request results in an Event whose `end_date` is
   earlier than its `start_date`, THE Event_Service SHALL respond with HTTP 422 and an
   Error_Body with `code = "VALIDATION_ERROR"`.

2. WHEN a `POST`, `PUT`, or `PATCH` request results in an Event whose `end_date` is equal
   to or later than its `start_date`, THE Event_Service SHALL accept the date range.

3. IF a `start_date` or `end_date` value is not a valid `YYYY-MM-DD` date, THEN THE
   Event_Service SHALL respond with HTTP 422 and an Error_Body with
   `code = "VALIDATION_ERROR"`.

---

### Requirement 4: Retrieve a Single Event (REQ-EVT-C02)

**User Story:** As a service consumer, I want to retrieve an event by identifier, so that
I can validate existence and read event attributes.

#### Acceptance Criteria

1. WHEN a `GET /api/v1/events/{id}` request is received and the Event exists in the
   Repository, THE Event_Service SHALL respond with HTTP 200 and the full Event object.

2. WHEN a `GET /api/v1/events/{id}` request is received and no Event with that `id`
   exists, THE Event_Service SHALL respond with HTTP 404 and an Error_Body with
   `code = "NOT_FOUND"`.

---

### Requirement 5: List Events with Pagination and Filters (REQ-EVT-B06)

**User Story:** As a participant, I want to browse events with filters, so that I can find
conferences by status or city.

#### Acceptance Criteria

1. WHEN a `GET /api/v1/events` request is received, THE Event_Service SHALL return a
   paginated Page of Events ordered consistently.

2. WHEN a `GET /api/v1/events` request includes a `page` query parameter, THE
   Event_Service SHALL return the corresponding page of results (default `page = 1`).

3. WHEN a `GET /api/v1/events` request includes a `page_size` query parameter (1–100),
   THE Event_Service SHALL limit the response to that number of items per page (default
   `page_size = 20`).

4. WHEN a `GET /api/v1/events` request includes a `status` query parameter, THE
   Event_Service SHALL return only Events whose `status` matches the supplied value.

5. WHEN a `GET /api/v1/events` request includes a `city` query parameter, THE
   Event_Service SHALL return only Events whose `city` matches the supplied value.

6. WHEN a `GET /api/v1/events` request includes an invalid `status` value, THE
   Event_Service SHALL respond with HTTP 422 and an Error_Body with
   `code = "VALIDATION_ERROR"`.

7. THE Event_Service SHALL include `page`, `page_size`, and `total` fields in every
   paginated response alongside the `items` array.

---

### Requirement 6: Full Replacement of an Event (REQ-EVT-C03)

**User Story:** As an organizer, I want to replace all event fields at once, so that I can
keep event information up to date.

#### Acceptance Criteria

1. WHEN a `PUT /api/v1/events/{id}` request is received with a valid complete body and the
   Event exists, THE Event_Service SHALL replace all mutable fields, update `updated_at`
   to the current UTC timestamp, and respond with HTTP 200 and the updated Event object.

2. WHEN a `PUT /api/v1/events/{id}` request is received and no Event with that `id`
   exists, THE Event_Service SHALL respond with HTTP 404 and an Error_Body with
   `code = "NOT_FOUND"`.

3. WHEN a `PUT /api/v1/events/{id}` request body is missing a required field, THE
   Event_Service SHALL respond with HTTP 422 and an Error_Body with
   `code = "VALIDATION_ERROR"`.

4. WHEN a `PUT /api/v1/events/{id}` request body contains malformed JSON, THE
   Event_Service SHALL respond with HTTP 400 and an Error_Body.

5. IF the User_Service is unreachable while validating a changed `organizer_id` during a
   `PUT /api/v1/events/{id}` request, THEN THE Event_Service SHALL respond with HTTP 503
   and an Error_Body with `code = "DEPENDENCY_UNAVAILABLE"`.

---

### Requirement 7: Partial Update of an Event (REQ-EVT-C04)

**User Story:** As an organizer, I want to update only specific event fields, so that I do
not have to resend unchanged data.

#### Acceptance Criteria

1. WHEN a `PATCH /api/v1/events/{id}` request is received with a partial valid body and
   the Event exists, THE Event_Service SHALL update only the supplied fields, update
   `updated_at` to the current UTC timestamp, and respond with HTTP 200 and the updated
   Event object.

2. WHEN a `PATCH /api/v1/events/{id}` request is received and no Event with that `id`
   exists, THE Event_Service SHALL respond with HTTP 404 and an Error_Body with
   `code = "NOT_FOUND"`.

3. WHEN a `PATCH /api/v1/events/{id}` request body contains a field value that violates a
   length, format, or range constraint, THE Event_Service SHALL respond with HTTP 422 and
   an Error_Body with `code = "VALIDATION_ERROR"`.

4. WHEN a `PATCH /api/v1/events/{id}` request body contains malformed JSON, THE
   Event_Service SHALL respond with HTTP 400 and an Error_Body.

5. IF the User_Service is unreachable while validating a changed `organizer_id` during a
   `PATCH /api/v1/events/{id}` request, THEN THE Event_Service SHALL respond with HTTP 503
   and an Error_Body with `code = "DEPENDENCY_UNAVAILABLE"`.

---

### Requirement 8: Event Status Transitions (REQ-EVT-B04)

**User Story:** As an organizer, I want event status changes to follow a defined
lifecycle, so that events move through valid states only.

#### Acceptance Criteria

1. WHEN a `PUT` or `PATCH` request changes an Event's `status` from `draft` to
   `published`, THE Event_Service SHALL apply the change and respond with HTTP 200.

2. WHEN a `PUT` or `PATCH` request changes an Event's `status` from `draft` to
   `cancelled`, THE Event_Service SHALL apply the change and respond with HTTP 200.

3. WHEN a `PUT` or `PATCH` request changes an Event's `status` from `published` to
   `cancelled`, THE Event_Service SHALL apply the change and respond with HTTP 200.

4. WHEN a `PUT` or `PATCH` request leaves an Event's `status` unchanged, THE
   Event_Service SHALL treat the transition as valid.

5. IF a `PUT` or `PATCH` request requests a status transition other than `draft→published`,
   `draft→cancelled`, `published→cancelled`, or a no-op transition, THEN THE Event_Service
   SHALL respond with HTTP 422 and an Error_Body with `code = "INVALID_STATUS_TRANSITION"`.

---

### Requirement 9: Delete an Event (REQ-EVT-C05)

**User Story:** As an organizer, I want to remove an event from the catalog, so that
obsolete events do not appear in listings.

#### Acceptance Criteria

1. WHEN a `DELETE /api/v1/events/{id}` request is received and the Event exists, THE
   Event_Service SHALL remove the Event from the Repository and respond with HTTP 204 and
   no body.

2. WHEN a `DELETE /api/v1/events/{id}` request is received and no Event with that `id`
   exists, THE Event_Service SHALL respond with HTTP 404 and an Error_Body with
   `code = "NOT_FOUND"`.

3. WHEN an Event is deleted, THE Event_Service SHALL return HTTP 404 for any subsequent
   `GET /api/v1/events/{id}` request for the same `id`.

---

### Requirement 10: Field Validation Constraints (REQ-EVT-V01)

**User Story:** As an API consumer, I want field validation to be enforced consistently,
so that only well-formed data enters the system.

#### Acceptance Criteria

1. IF a `title` value has fewer than 3 or more than 120 characters, THEN THE
   Event_Service SHALL respond with HTTP 422 and an Error_Body with
   `code = "VALIDATION_ERROR"`.

2. IF a `description` value exceeds 2000 characters, THEN THE Event_Service SHALL respond
   with HTTP 422 and an Error_Body with `code = "VALIDATION_ERROR"`.

3. IF a `venue` value exceeds 100 characters, THEN THE Event_Service SHALL respond with
   HTTP 422 and an Error_Body with `code = "VALIDATION_ERROR"`.

4. IF a `city` value exceeds 60 characters, THEN THE Event_Service SHALL respond with
   HTTP 422 and an Error_Body with `code = "VALIDATION_ERROR"`.

5. IF a `capacity` value is less than 1 or greater than 10000, THEN THE Event_Service
   SHALL respond with HTTP 422 and an Error_Body with `code = "VALIDATION_ERROR"`.

6. IF a `price` value is less than 0, THEN THE Event_Service SHALL respond with HTTP 422
   and an Error_Body with `code = "VALIDATION_ERROR"`.

7. THE Event_Service SHALL store and return the `price` value as a number with 2 decimal
   places, with an implicit currency of EUR.

8. THE Event_Service SHALL NOT accept `id`, `created_at`, or `updated_at` as writable
   fields in create or update requests; any supplied values for these fields SHALL be
   ignored.

---

### Requirement 11: Health Endpoint (REQ-EVT-H01)

**User Story:** As a platform operator, I want a health check endpoint, so that
orchestration tooling can verify the service is running.

#### Acceptance Criteria

1. WHEN a `GET /health` request is received, THE Event_Service SHALL respond with HTTP 200
   and a JSON body conforming to `{"status": "ok", "service": "event-service"}`.

2. THE Event_Service SHALL respond to `GET /health` regardless of the state of the
   Repository backend or the reachability of the User_Service.

---

### Requirement 12: Pluggable Storage Backend (REQ-EVT-S01)

**User Story:** As a developer, I want to switch the persistence backend without changing
business logic, so that I can run tests in memory and deploy with a durable store.

#### Acceptance Criteria

1. WHEN the `STORAGE_BACKEND` environment variable is set to `memory`, THE Event_Service
   SHALL store all data in-process with no file I/O.

2. WHEN the `STORAGE_BACKEND` environment variable is set to `json`, THE Event_Service
   SHALL persist data as JSON files in the directory specified by `DATA_DIR`
   (default `./data`).

3. WHEN the `STORAGE_BACKEND` environment variable is set to `sqlite`, THE Event_Service
   SHALL persist data in a SQLite database file in `DATA_DIR` using only the Python
   standard library `sqlite3` module.

4. WHEN `STORAGE_BACKEND` is not set, THE Event_Service SHALL default to the `memory`
   backend.

5. THE Event_Service SHALL expose the same HTTP API behaviour regardless of which
   Storage_Backend is active; switching backends SHALL NOT require changes to business
   logic or route handlers.

---

### Requirement 13: Service Configuration via Environment Variables (REQ-EVT-CFG01)

**User Story:** As a platform operator, I want service configuration to come exclusively
from environment variables, so that the same process can run in any environment.

#### Acceptance Criteria

1. WHEN the `PORT` environment variable is set, THE Event_Service SHALL listen on the
   specified port.

2. WHEN the `PORT` environment variable is not set, THE Event_Service SHALL default to
   port `5002`.

3. WHEN the `USER_SERVICE_URL` environment variable is set, THE Event_Service SHALL use
   its value as the base URL for all User_Service calls.

4. WHEN the `USER_SERVICE_URL` environment variable is not set, THE Event_Service SHALL
   default to `http://localhost:5001`.

5. THE Event_Service SHALL read all runtime configuration (`PORT`, `STORAGE_BACKEND`,
   `DATA_DIR`, `USER_SERVICE_URL`) from environment variables at startup, not from
   hard-coded values in the source code.

---

### Requirement 14: Response Contract Conformance (REQ-EVT-OA01)

**User Story:** As a service consumer, I want every response to conform to the OpenAPI
contract, so that clients can rely on a stable, documented interface.

#### Acceptance Criteria

1. THE Event_Service SHALL return responses that conform to the schemas defined in
   `contracts/openapi/event-service.yaml` for every endpoint and status code.

2. THE Event_Service SHALL set `Content-Type: application/json` on all responses that
   carry a body.

3. THE Event_Service SHALL NOT include fields in response bodies beyond those declared in
   the corresponding OpenAPI schema (`additionalProperties: false`).

4. WHEN an unsupported HTTP method is used on a defined route, THE Event_Service SHALL
   respond with HTTP 405.
