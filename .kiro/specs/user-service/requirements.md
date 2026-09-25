# Requirements Document

## Introduction

The user-service is a mandatory microservice of the TechConf platform. It acts as the
central registry for all platform users (attendees, speakers, organizers). Every other
service that needs to validate a user's existence or role calls this service via HTTP.
The service exposes a REST API at `/api/v1/users` on port 5001, conforms to the OpenAPI
contract in `contracts/openapi/user-service.yaml`, and must pass all IT-U01..IT-U08
acceptance tests.

---

## Glossary

- **User_Service**: The microservice described in this document; listens on the port
  provided by the `PORT` environment variable (default `5001`).
- **User**: A platform participant with fields `id`, `first_name`, `last_name`, `email`,
  `company`, `role`, `created_at`, `updated_at`.
- **Role**: An enumerated value — `attendee` (default), `speaker`, or `organizer`.
- **Email**: A string in valid e-mail format; stored and compared case-insensitively.
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

### Requirement 1: User Creation (REQ-USR-C01)

**User Story:** As a conference participant, I want to register on the platform, so that
I can sign up for events and use platform features.

#### Acceptance Criteria

1. WHEN a `POST /api/v1/users` request is received with a valid JSON body containing
   `first_name`, `last_name`, and `email`, THE User_Service SHALL create the User,
   persist it via the Repository, and respond with HTTP 201.

2. WHEN a User is created successfully, THE User_Service SHALL include a `Location`
   header containing the URL of the new resource (e.g. `/api/v1/users/{id}`).

3. WHEN a User is created successfully, THE User_Service SHALL return the full User
   object conforming to the `User` schema in the OpenAPI contract, including server-
   generated fields `id` (UUID v4), `created_at`, and `updated_at` (ISO 8601 UTC).

4. WHEN a `POST /api/v1/users` request body omits `first_name`, `last_name`, or `email`,
   THE User_Service SHALL respond with HTTP 422 and an Error_Body with
   `code = "VALIDATION_ERROR"`.

5. WHEN a `POST /api/v1/users` request body contains malformed JSON (not parseable),
   THE User_Service SHALL respond with HTTP 400 and an Error_Body.

6. WHEN a `POST /api/v1/users` request body contains a `role` field, THE User_Service
   SHALL accept the values `attendee`, `speaker`, and `organizer` only.

7. WHEN a `POST /api/v1/users` request body omits the `role` field, THE User_Service
   SHALL default the User's role to `attendee`.

---

### Requirement 2: Email Uniqueness and Normalisation (REQ-USR-B01, REQ-USR-B02)

**User Story:** As a platform administrator, I want each user to have a unique email
address stored in lowercase, so that login and search are unambiguous.

#### Acceptance Criteria

1. WHEN a `POST /api/v1/users` request is received and the `email` field (compared
   case-insensitively) already exists in the Repository, THE User_Service SHALL respond
   with HTTP 409 and an Error_Body with `code = "EMAIL_ALREADY_EXISTS"`.

2. THE User_Service SHALL store the `email` value converted to lowercase in the
   Repository, regardless of the case supplied by the client.

3. WHEN a User is returned in any response, THE User_Service SHALL return the `email`
   field in lowercase.

4. WHEN a `PUT /api/v1/users/{id}` or `PATCH /api/v1/users/{id}` request attempts to
   change the `email` to one that (case-insensitively) already belongs to a different
   User, THE User_Service SHALL respond with HTTP 409 and an Error_Body with
   `code = "EMAIL_ALREADY_EXISTS"`.

---

### Requirement 3: Retrieve a Single User (REQ-USR-C02)

**User Story:** As a service consumer, I want to retrieve a user by identifier, so that
I can validate existence and read user attributes.

#### Acceptance Criteria

1. WHEN a `GET /api/v1/users/{id}` request is received and the User exists in the
   Repository, THE User_Service SHALL respond with HTTP 200 and the full User object.

2. WHEN a `GET /api/v1/users/{id}` request is received and no User with that `id`
   exists, THE User_Service SHALL respond with HTTP 404 and an Error_Body with
   `code = "NOT_FOUND"`.

---

### Requirement 4: List Users with Pagination and Filters (REQ-USR-B03)

**User Story:** As an event organizer, I want to browse the user list with filters, so
that I can find participants by role or email.

#### Acceptance Criteria

1. WHEN a `GET /api/v1/users` request is received, THE User_Service SHALL return a
   paginated Page of Users ordered consistently.

2. WHEN a `GET /api/v1/users` request includes a `page` query parameter, THE
   User_Service SHALL return the corresponding page of results (default `page = 1`).

3. WHEN a `GET /api/v1/users` request includes a `page_size` query parameter (1–100),
   THE User_Service SHALL limit the response to that number of items per page (default
   `page_size = 20`).

4. WHEN a `GET /api/v1/users` request includes a `role` query parameter, THE
   User_Service SHALL return only Users whose `role` matches the supplied value.

5. WHEN a `GET /api/v1/users` request includes an `email` query parameter, THE
   User_Service SHALL return only Users whose stored (lowercase) `email` matches the
   supplied value (case-insensitive comparison).

6. WHEN a `GET /api/v1/users` request includes an invalid `role` value, THE
   User_Service SHALL respond with HTTP 422 and an Error_Body with
   `code = "VALIDATION_ERROR"`.

7. THE User_Service SHALL include `page`, `page_size`, and `total` fields in every
   paginated response alongside the `items` array.

---

### Requirement 5: Full Replacement of a User (REQ-USR-C03)

**User Story:** As a platform user, I want to replace all my profile fields at once, so
that I can keep my information up to date.

#### Acceptance Criteria

1. WHEN a `PUT /api/v1/users/{id}` request is received with a valid complete body and
   the User exists, THE User_Service SHALL replace all mutable fields, update
   `updated_at` to the current UTC timestamp, and respond with HTTP 200 and the updated
   User object.

2. WHEN a `PUT /api/v1/users/{id}` request is received and no User with that `id`
   exists, THE User_Service SHALL respond with HTTP 404 and an Error_Body with
   `code = "NOT_FOUND"`.

3. WHEN a `PUT /api/v1/users/{id}` request body is missing a required field, THE
   User_Service SHALL respond with HTTP 422 and an Error_Body with
   `code = "VALIDATION_ERROR"`.

4. WHEN a `PUT /api/v1/users/{id}` request body contains malformed JSON, THE
   User_Service SHALL respond with HTTP 400 and an Error_Body.

---

### Requirement 6: Partial Update of a User (REQ-USR-C04)

**User Story:** As a platform user, I want to update only specific profile fields, so
that I do not have to resend unchanged data.

#### Acceptance Criteria

1. WHEN a `PATCH /api/v1/users/{id}` request is received with a partial valid body and
   the User exists, THE User_Service SHALL update only the supplied fields, update
   `updated_at` to the current UTC timestamp, and respond with HTTP 200 and the updated
   User object.

2. WHEN a `PATCH /api/v1/users/{id}` request is received and no User with that `id`
   exists, THE User_Service SHALL respond with HTTP 404 and an Error_Body with
   `code = "NOT_FOUND"`.

3. WHEN a `PATCH /api/v1/users/{id}` request body contains a field value that violates
   length or format constraints, THE User_Service SHALL respond with HTTP 422 and an
   Error_Body with `code = "VALIDATION_ERROR"`.

4. WHEN a `PATCH /api/v1/users/{id}` request body contains malformed JSON, THE
   User_Service SHALL respond with HTTP 400 and an Error_Body.

5. WHEN a `PATCH /api/v1/users/{id}` request body supplies no recognised fields, THE
   User_Service SHALL leave the User unchanged and respond with HTTP 200 and the
   current User object.

---

### Requirement 7: Delete a User (REQ-USR-C05)

**User Story:** As a platform administrator, I want to remove a user from the registry,
so that stale accounts do not pollute the system.

#### Acceptance Criteria

1. WHEN a `DELETE /api/v1/users/{id}` request is received and the User exists, THE
   User_Service SHALL remove the User from the Repository and respond with HTTP 204 and
   no body.

2. WHEN a `DELETE /api/v1/users/{id}` request is received and no User with that `id`
   exists, THE User_Service SHALL respond with HTTP 404 and an Error_Body with
   `code = "NOT_FOUND"`.

3. WHEN a User is deleted, THE User_Service SHALL return HTTP 404 for any subsequent
   `GET /api/v1/users/{id}` request for the same `id`.

---

### Requirement 8: Field Validation Constraints (REQ-USR-V01)

**User Story:** As an API consumer, I want field validation to be enforced consistently,
so that only well-formed data enters the system.

#### Acceptance Criteria

1. IF a `first_name` or `last_name` value has fewer than 1 or more than 50 characters,
   THEN THE User_Service SHALL respond with HTTP 422 and an Error_Body with
   `code = "VALIDATION_ERROR"`.

2. IF an `email` value does not conform to a valid email format, THEN THE User_Service
   SHALL respond with HTTP 422 and an Error_Body with `code = "VALIDATION_ERROR"`.

3. IF a `company` value exceeds 100 characters, THEN THE User_Service SHALL respond
   with HTTP 422 and an Error_Body with `code = "VALIDATION_ERROR"`.

4. IF a `role` value is not one of `attendee`, `speaker`, `organizer`, THEN THE
   User_Service SHALL respond with HTTP 422 and an Error_Body with
   `code = "VALIDATION_ERROR"`.

5. THE User_Service SHALL NOT accept `id`, `created_at`, or `updated_at` as writable
   fields in create or update requests; any supplied values for these fields SHALL be
   ignored.

---

### Requirement 9: Health Endpoint (REQ-USR-H01)

**User Story:** As a platform operator, I want a health check endpoint, so that
orchestration tooling can verify the service is running.

#### Acceptance Criteria

1. WHEN a `GET /health` request is received, THE User_Service SHALL respond with
   HTTP 200 and a JSON body conforming to `{"status": "ok", "service": "<name>"}`.

2. THE User_Service SHALL respond to `GET /health` regardless of the state of the
   Repository backend.

---

### Requirement 10: Pluggable Storage Backend (REQ-USR-S01)

**User Story:** As a developer, I want to switch the persistence backend without
changing business logic, so that I can run tests in memory and deploy with a durable
store.

#### Acceptance Criteria

1. WHEN the `STORAGE_BACKEND` environment variable is set to `memory`, THE
   User_Service SHALL store all data in-process with no file I/O.

2. WHEN the `STORAGE_BACKEND` environment variable is set to `json`, THE User_Service
   SHALL persist data as JSON files in the directory specified by `DATA_DIR`
   (default `./data`).

3. WHEN the `STORAGE_BACKEND` environment variable is set to `sqlite`, THE
   User_Service SHALL persist data in a SQLite database file in `DATA_DIR` using only
   the Python standard library `sqlite3` module.

4. WHEN `STORAGE_BACKEND` is not set, THE User_Service SHALL default to the `memory`
   backend.

5. THE User_Service SHALL expose the same HTTP API behaviour regardless of which
   Storage_Backend is active; switching backends SHALL NOT require changes to business
   logic or route handlers.

---

### Requirement 11: Service Configuration via Environment Variables (REQ-USR-CFG01)

**User Story:** As a platform operator, I want service configuration to come exclusively
from environment variables, so that the same image or process can run in any environment.

#### Acceptance Criteria

1. WHEN the `PORT` environment variable is set, THE User_Service SHALL listen on the
   specified port.

2. WHEN the `PORT` environment variable is not set, THE User_Service SHALL default to
   port `5001`.

3. THE User_Service SHALL read all runtime configuration (`PORT`, `STORAGE_BACKEND`,
   `DATA_DIR`) from environment variables at startup, not from hard-coded values in
   the source code.

---

### Requirement 12: Response Contract Conformance (REQ-USR-OA01)

**User Story:** As a service consumer, I want every response to conform to the OpenAPI
contract, so that clients can rely on a stable, documented interface.

#### Acceptance Criteria

1. THE User_Service SHALL return responses that conform to the schemas defined in
   `contracts/openapi/user-service.yaml` for every endpoint and status code.

2. THE User_Service SHALL set `Content-Type: application/json` on all responses that
   carry a body.

3. THE User_Service SHALL NOT include fields in response bodies beyond those declared
   in the corresponding OpenAPI schema (`additionalProperties: false`).
