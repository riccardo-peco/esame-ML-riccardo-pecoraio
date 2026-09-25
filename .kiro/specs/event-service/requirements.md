# Requirements Document

## Introduction

The event-service is a mandatory TechConf microservice for managing conferences, their
capacity, and their lifecycle. The service exposes a JSON REST API at
`/api/v1/events`, listens on the port supplied through `PORT` (default `5002`), and
validates each event organizer by calling user-service over HTTP. The immutable
interface source of truth is `Exam/techconf-exam/contracts/openapi/event-service.yaml`.
The service must satisfy the event-service acceptance scenarios IT-E01 through IT-E08
and support the mandatory end-to-end journey IT-J01 without modifying the immutable
contract or instructor integration tests.

## Glossary

- **Event_Service**: The microservice specified by this document.
- **User_Service**: The TechConf microservice queried by Event_Service to verify an
  organizer; its base URL comes from `USER_SERVICE_URL`.
- **Event**: A conference resource containing `id`, `title`, `description`,
  `organizer_id`, `venue`, `city`, `start_date`, `end_date`, `capacity`, `price`,
  `status`, `created_at`, and `updated_at`.
- **Organizer**: A user resource returned by User_Service whose `role` is `organizer`.
- **Event_Create_Payload**: A JSON object conforming to the OpenAPI `EventCreate`
  schema. Required fields are `title`, `organizer_id`, `venue`, `city`, `start_date`,
  `end_date`, `capacity`, and `price`; optional fields are `description` and `status`.
- **Event_Update_Payload**: A JSON object conforming to the OpenAPI `EventUpdate`
  schema and containing zero or more mutable Event fields.
- **Mutable_Event_Field**: One of `title`, `description`, `organizer_id`, `venue`,
  `city`, `start_date`, `end_date`, `capacity`, `price`, or `status`.
- **Read_Only_Event_Field**: One of the server-managed fields `id`, `created_at`, or
  `updated_at`.
- **Event_Status**: One of `draft`, `published`, or `cancelled`.
- **Valid_Status_Transition**: One of `draft` to `published`, `draft` to `cancelled`,
  or `published` to `cancelled`; retaining the current Event_Status is not a
  transition.
- **Resource_ID**: A server-generated UUID version 4 identifying an Event.
- **UTC_Timestamp**: An ISO 8601 date-time in UTC, represented with a `Z` suffix.
- **Page**: A JSON object with `items`, `page`, `page_size`, and `total`, conforming to
  the OpenAPI `EventPage` schema.
- **Repository**: A persistence abstraction used by business logic to create, read,
  list, replace, update, and delete Events.
- **Storage_Backend**: The Repository implementation selected by `STORAGE_BACKEND`:
  `memory`, `json`, or `sqlite`.
- **Error_Body**: A JSON object of the form
  `{"error":{"code":"UPPER_SNAKE","message":"...","details":{...}}}` that
  conforms to the OpenAPI `Error` schema.
- **Dependency_Failure**: A User_Service timeout, refused connection, transport error,
  HTTP 5xx response, or unusable response.
- **OpenAPI_Contract**: The immutable contract at
  `Exam/techconf-exam/contracts/openapi/event-service.yaml`.
- **Event_Service_Project**: The event-service source tree rooted at
  `Exam/techconf-exam/services/event-service`.
- **Event_Service_Test_Suite**: The automated unit, contract, and service-integration
  tests authored for Event_Service, excluding the immutable instructor integration
  tests.

## Requirements

### Requirement 1: Create an Event (REQ-EVT-C01)

**User Story:** As a conference organizer, I want to create an event, so that the event
can be prepared and published for attendees.

#### Acceptance Criteria

1. WHEN `POST /api/v1/events` receives a valid Event_Create_Payload with a verified
   Organizer, THE Event_Service SHALL persist one new Event through the Repository.
2. WHEN an Event is created, THE Event_Service SHALL generate the Event `id` as a UUID
   version 4.
3. WHEN an Event is created, THE Event_Service SHALL set `created_at` and `updated_at`
   to UTC_Timestamp values.
4. WHEN an Event is created successfully, THE Event_Service SHALL respond with HTTP
   201.
5. WHEN an Event is created successfully, THE Event_Service SHALL include a `Location`
   header whose value identifies `/api/v1/events/{id}` for the created Event.
6. WHEN an Event is created successfully, THE Event_Service SHALL return the complete
   Event conforming to the OpenAPI `Event` schema.
7. WHEN an Event_Create_Payload omits `status`, THE Event_Service SHALL set Event_Status
   to `draft`.
8. WHEN an Event_Create_Payload supplies `status`, THE Event_Service SHALL accept only
   `draft`, `published`, or `cancelled`.
9. WHEN `POST /api/v1/events` receives malformed JSON, THE Event_Service SHALL respond
   with HTTP 400 and an Error_Body.

### Requirement 2: Validate Event Fields (REQ-EVT-V01)

**User Story:** As an API consumer, I want event fields validated consistently, so that
stored events satisfy the published interface contract.

#### Acceptance Criteria

1. IF an Event_Create_Payload omits `title`, `organizer_id`, `venue`, `city`,
   `start_date`, `end_date`, `capacity`, or `price`, THEN THE Event_Service SHALL
   respond with HTTP 422 and an Error_Body whose code is `VALIDATION_ERROR`.
2. IF `title` contains fewer than 3 or more than 120 characters, THEN THE Event_Service
   SHALL respond with HTTP 422 and an Error_Body whose code is `VALIDATION_ERROR`.
3. WHERE `description` is supplied, IF `description` is neither null nor a string of at
   most 2000 characters, THEN THE Event_Service SHALL respond with HTTP 422 and an
   Error_Body whose code is `VALIDATION_ERROR`.
4. IF `organizer_id` is not a UUID value, THEN THE Event_Service SHALL respond with
   HTTP 422 and an Error_Body whose code is `VALIDATION_ERROR`.
5. IF `venue` is not a string of at most 100 characters, THEN THE Event_Service SHALL
   respond with HTTP 422 and an Error_Body whose code is `VALIDATION_ERROR`.
6. IF `city` is not a string of at most 60 characters, THEN THE Event_Service SHALL
   respond with HTTP 422 and an Error_Body whose code is `VALIDATION_ERROR`.
7. IF `start_date` or `end_date` is not a calendar date in `YYYY-MM-DD` format, THEN THE
   Event_Service SHALL respond with HTTP 422 and an Error_Body whose code is
   `VALIDATION_ERROR`.
8. IF `capacity` is not an integer from 1 through 10000 inclusive, THEN THE
   Event_Service SHALL respond with HTTP 422 and an Error_Body whose code is
   `VALIDATION_ERROR`.
9. IF `price` is not a numeric EUR amount greater than or equal to `0.00`, THEN THE
   Event_Service SHALL respond with HTTP 422 and an Error_Body whose code is
   `VALIDATION_ERROR`.
10. WHEN Event_Service stores or returns `price`, THE Event_Service SHALL represent the
    amount at two-decimal EUR precision.
11. IF `status` is not an Event_Status, THEN THE Event_Service SHALL respond with HTTP
    422 and an Error_Body whose code is `VALIDATION_ERROR`.
12. IF a create or update payload contains a Read_Only_Event_Field or an undeclared
    field, THEN THE Event_Service SHALL respond with HTTP 422 and an Error_Body whose
    code is `VALIDATION_ERROR`.

### Requirement 3: Verify Organizer Existence (REQ-EVT-B01)

**User Story:** As a platform operator, I want each event to reference an existing user,
so that events do not contain dangling organizer references.

#### Acceptance Criteria

1. WHEN Event_Service validates an `organizer_id`, THE Event_Service SHALL request
   `GET /api/v1/users/{organizer_id}` from User_Service.
2. WHEN User_Service returns HTTP 200 for an `organizer_id`, THE Event_Service SHALL use
   the returned user resource for organizer-role validation.
3. WHEN User_Service returns HTTP 404 for an `organizer_id`, THE Event_Service SHALL
   respond with HTTP 422 and an Error_Body whose code is `REFERENCE_NOT_FOUND`.

### Requirement 4: Verify Organizer Role (REQ-EVT-B02)

**User Story:** As a platform administrator, I want only organizers to own events, so
that attendee and speaker accounts cannot organize conferences.

#### Acceptance Criteria

1. WHEN User_Service returns a user whose `role` is `organizer`, THE Event_Service SHALL
   accept the user as the Organizer.
2. IF User_Service returns a user whose `role` is not `organizer`, THEN THE
   Event_Service SHALL respond with HTTP 422 and an Error_Body whose code is
   `INVALID_ORGANIZER`.

### Requirement 5: Enforce Event Date Order (REQ-EVT-B03)

**User Story:** As a conference organizer, I want event dates kept in chronological
order, so that event schedules are meaningful.

#### Acceptance Criteria

1. WHEN `end_date` is equal to or later than `start_date`, THE Event_Service SHALL
   accept the date interval.
2. IF `end_date` is earlier than `start_date`, THEN THE Event_Service SHALL respond with
   HTTP 422 and an Error_Body whose code is `VALIDATION_ERROR`.
3. WHEN a PUT or PATCH request changes either event date, THE Event_Service SHALL
   validate the resulting pair of `start_date` and `end_date`.

### Requirement 6: Enforce Event Lifecycle (REQ-EVT-B04)

**User Story:** As a conference organizer, I want controlled event lifecycle changes,
so that published or cancelled events cannot return to an earlier state.

#### Acceptance Criteria

1. WHEN an existing Event changes from `draft` to `published`, THE Event_Service SHALL
   persist the new Event_Status.
2. WHEN an existing Event changes from `draft` to `cancelled`, THE Event_Service SHALL
   persist the new Event_Status.
3. WHEN an existing Event changes from `published` to `cancelled`, THE Event_Service
   SHALL persist the new Event_Status.
4. WHEN an update supplies the current Event_Status, THE Event_Service SHALL retain the
   current Event_Status without reporting a transition error.
5. IF an update requests a status change other than a Valid_Status_Transition, THEN THE
   Event_Service SHALL respond with HTTP 422 and an Error_Body whose code is
   `INVALID_STATUS_TRANSITION`.
6. WHEN a lifecycle change succeeds, THE Event_Service SHALL update `updated_at` to a
   UTC_Timestamp later than the previous `updated_at` value.

### Requirement 7: Handle User-Service Failures (REQ-EVT-B05)

**User Story:** As an API consumer, I want dependency failures reported consistently,
so that temporary infrastructure failures are distinguishable from invalid organizer
references.

#### Acceptance Criteria

1. WHEN Event_Service calls User_Service, THE Event_Service SHALL use a 2-second HTTP
   timeout.
2. IF a User_Service request results in a Dependency_Failure, THEN THE Event_Service
   SHALL respond with HTTP 503 and an Error_Body whose code is
   `DEPENDENCY_UNAVAILABLE`.
3. IF User_Service returns HTTP 500 through 599, THEN THE Event_Service SHALL respond
   with HTTP 503 and an Error_Body whose code is `DEPENDENCY_UNAVAILABLE`.
4. IF User_Service returns a response that cannot be used to verify the user identifier
   and role, THEN THE Event_Service SHALL respond with HTTP 503 and an Error_Body whose
   code is `DEPENDENCY_UNAVAILABLE`.

### Requirement 8: List and Filter Events (REQ-EVT-B06, REQ-EVT-C02)

**User Story:** As an attendee, I want to browse events by status and city, so that I can
find relevant conferences.

#### Acceptance Criteria

1. WHEN `GET /api/v1/events` is received without pagination parameters, THE
   Event_Service SHALL return HTTP 200 with Page values `page = 1` and
   `page_size = 20`.
2. WHEN `GET /api/v1/events` supplies valid `page` and `page_size` parameters, THE
   Event_Service SHALL return the corresponding Page of Events.
3. WHEN Event_Service returns a Page, THE Event_Service SHALL set `total` to the number
   of Events matching all supplied filters before pagination.
4. WHEN Event_Service returns a Page, THE Event_Service SHALL return Events in a stable
   deterministic order.
5. WHEN `GET /api/v1/events` supplies a `status` filter, THE Event_Service SHALL return
   only Events whose Event_Status equals the supplied value.
6. WHEN `GET /api/v1/events` supplies a `city` filter, THE Event_Service SHALL return
   only Events whose `city` matches the supplied value.
7. WHEN `GET /api/v1/events` supplies both `status` and `city`, THE Event_Service SHALL
   return only Events matching both filters.
8. IF `page` is not an integer greater than or equal to 1, THEN THE Event_Service SHALL
   respond with HTTP 422 and an Error_Body whose code is `VALIDATION_ERROR`.
9. IF `page_size` is not an integer from 1 through 100 inclusive, THEN THE Event_Service
   SHALL respond with HTTP 422 and an Error_Body whose code is `VALIDATION_ERROR`.
10. IF a `status` filter is not an Event_Status, THEN THE Event_Service SHALL respond
    with HTTP 422 and an Error_Body whose code is `VALIDATION_ERROR`.

### Requirement 9: Retrieve an Event (REQ-EVT-C03)

**User Story:** As a service consumer, I want to retrieve an event by identifier, so
that I can validate the event and read its attributes.

#### Acceptance Criteria

1. WHEN `GET /api/v1/events/{id}` identifies a stored Event, THE Event_Service SHALL
   respond with HTTP 200 and the complete Event.
2. WHEN `GET /api/v1/events/{id}` identifies no stored Event, THE Event_Service SHALL
   respond with HTTP 404 and an Error_Body whose code is `NOT_FOUND`.

### Requirement 10: Replace an Event (REQ-EVT-C04)

**User Story:** As a conference organizer, I want to replace an event's mutable data, so
that I can submit a complete revised event representation.

#### Acceptance Criteria

1. WHEN `PUT /api/v1/events/{id}` identifies a stored Event and receives a valid
   Event_Create_Payload, THE Event_Service SHALL replace the supplied
   Mutable_Event_Fields.
2. WHEN a valid PUT payload omits optional `description`, THE Event_Service SHALL set
   the Event `description` to null.
3. WHEN a valid PUT payload omits optional `status`, THE Event_Service SHALL retain the
   current Event_Status.
4. WHEN a PUT request changes `organizer_id`, THE Event_Service SHALL validate the new
   organizer through User_Service before persisting the replacement.
5. WHEN a PUT request supplies `organizer_id` equal to the stored `organizer_id`, THE
   Event_Service SHALL validate the Organizer through User_Service before persisting
   the replacement.
6. WHEN a PUT request changes Event_Status, THE Event_Service SHALL enforce
   Valid_Status_Transition rules before persisting the replacement.
7. WHEN an Event replacement succeeds, THE Event_Service SHALL preserve `id` and
   `created_at`.
8. WHEN an Event replacement succeeds, THE Event_Service SHALL set `updated_at` to a
   UTC_Timestamp later than the previous `updated_at` value.
9. WHEN an Event replacement succeeds, THE Event_Service SHALL respond with HTTP 200
   and the complete updated Event.
10. WHEN `PUT /api/v1/events/{id}` identifies no stored Event, THE Event_Service SHALL
    respond with HTTP 404 and an Error_Body whose code is `NOT_FOUND`.
11. IF a PUT payload omits a required Event_Create_Payload field, THEN THE Event_Service
    SHALL respond with HTTP 422 and an Error_Body whose code is `VALIDATION_ERROR`.
12. WHEN `PUT /api/v1/events/{id}` receives malformed JSON, THE Event_Service SHALL
    respond with HTTP 400 and an Error_Body.

### Requirement 11: Partially Update an Event (REQ-EVT-C05)

**User Story:** As a conference organizer, I want to update selected event fields, so
that unchanged fields do not need to be resubmitted.

#### Acceptance Criteria

1. WHEN `PATCH /api/v1/events/{id}` identifies a stored Event and receives a valid
   Event_Update_Payload, THE Event_Service SHALL change only the supplied
   Mutable_Event_Fields.
2. WHEN a PATCH request changes `organizer_id`, THE Event_Service SHALL validate the
   new organizer through User_Service before persisting the update.
3. WHEN a PATCH request changes Event_Status, THE Event_Service SHALL enforce
   Valid_Status_Transition rules before persisting the update.
4. WHEN a PATCH request changes `start_date` or `end_date`, THE Event_Service SHALL
   validate the resulting complete date interval before persisting the update.
5. WHEN an Event_Update_Payload contains no fields, THE Event_Service SHALL retain the
   stored Event values.
6. WHEN an Event partial update succeeds, THE Event_Service SHALL preserve `id` and
   `created_at`.
7. WHEN an Event partial update changes at least one value, THE Event_Service SHALL set
   `updated_at` to a UTC_Timestamp later than the previous `updated_at` value.
8. WHEN an Event partial update succeeds, THE Event_Service SHALL respond with HTTP 200
   and the complete updated Event.
9. WHEN `PATCH /api/v1/events/{id}` identifies no stored Event, THE Event_Service SHALL
   respond with HTTP 404 and an Error_Body whose code is `NOT_FOUND`.
10. WHEN `PATCH /api/v1/events/{id}` receives malformed JSON, THE Event_Service SHALL
    respond with HTTP 400 and an Error_Body.

### Requirement 12: Delete an Event (REQ-EVT-C06)

**User Story:** As a platform administrator, I want to delete an event, so that obsolete
conference records can be removed.

#### Acceptance Criteria

1. WHEN `DELETE /api/v1/events/{id}` identifies a stored Event, THE Event_Service SHALL
   delete the Event from the Repository.
2. WHEN an Event is deleted successfully, THE Event_Service SHALL respond with HTTP 204
   and no response body.
3. WHEN `DELETE /api/v1/events/{id}` identifies no stored Event, THE Event_Service SHALL
   respond with HTTP 404 and an Error_Body whose code is `NOT_FOUND`.
4. WHEN an Event has been deleted, THE Event_Service SHALL respond with HTTP 404 to a
   subsequent `GET /api/v1/events/{id}` request for the deleted Resource_ID.

### Requirement 13: Produce Standard HTTP Errors (REQ-EVT-ERR01)

**User Story:** As an API consumer, I want uniform error responses, so that failures can
be handled predictably.

#### Acceptance Criteria

1. WHEN Event_Service returns HTTP 400, 404, 405, 422, 409, or 503 with a response body,
   THE Event_Service SHALL return an Error_Body containing `code` and `message`.
2. WHERE contextual error information is available, THE Event_Service SHALL include the
   contextual information in the Error_Body `details` object.
3. WHEN a request uses a method not declared for an Event_Service path, THE
   Event_Service SHALL respond with HTTP 405 and an Error_Body.
4. WHEN Event_Service receives malformed JSON at an endpoint that consumes JSON, THE
   Event_Service SHALL respond with HTTP 400 and an Error_Body.
5. WHEN an Event resource cannot be found for a single-resource operation, THE
   Event_Service SHALL use Error_Body code `NOT_FOUND`.
6. WHEN request data violates a schema constraint without violating a more specific
   business rule, THE Event_Service SHALL use Error_Body code `VALIDATION_ERROR`.

### Requirement 14: Expose Service Health (REQ-EVT-H01)

**User Story:** As a platform operator, I want a health endpoint, so that orchestration
and test tooling can determine whether event-service is running.

#### Acceptance Criteria

1. WHEN `GET /health` is received, THE Event_Service SHALL respond with HTTP 200.
2. WHEN `GET /health` is received, THE Event_Service SHALL return
   `{"status":"ok","service":"event-service"}`.
3. WHEN User_Service is unavailable, THE Event_Service SHALL continue to return the
   health response without calling User_Service.

### Requirement 15: Support Pluggable Persistence (REQ-EVT-S01)

**User Story:** As a developer, I want interchangeable persistence backends, so that the
service can run transiently or retain data without changing business logic.

#### Acceptance Criteria

1. WHERE Storage_Backend is `memory`, THE Event_Service SHALL store Events in process
   without persistent file I/O.
2. WHERE Storage_Backend is `json`, THE Event_Service SHALL persist Events in a JSON
   file under `DATA_DIR`.
3. WHERE Storage_Backend is `sqlite`, THE Event_Service SHALL persist Events in a SQLite
   database under `DATA_DIR` using the Python standard-library `sqlite3` module.
4. WHEN `STORAGE_BACKEND` is absent, THE Event_Service SHALL select the `memory`
   Storage_Backend.
5. WHEN `DATA_DIR` is absent, THE Event_Service SHALL use `./data` as the data directory
   for file-backed repositories.
6. THE Event_Service SHALL expose identical domain and HTTP behavior for `memory`,
   `json`, and `sqlite` Storage_Backends.
7. THE Event_Service SHALL select a Storage_Backend without requiring changes to route
   handlers or business rules.

### Requirement 16: Read Runtime Configuration (REQ-EVT-CFG01)

**User Story:** As a platform operator, I want runtime settings supplied through the
environment, so that the same service code can run in development and test environments.

#### Acceptance Criteria

1. WHEN `PORT` is set, THE Event_Service SHALL listen on the specified TCP port.
2. WHEN `PORT` is absent, THE Event_Service SHALL listen on TCP port 5002.
3. WHEN `USER_SERVICE_URL` is set, THE Event_Service SHALL use that value as the
   User_Service base URL.
4. WHEN `USER_SERVICE_URL` is absent, THE Event_Service SHALL use
   `http://localhost:5001` as the User_Service base URL.
5. THE Event_Service SHALL read `PORT`, `USER_SERVICE_URL`, `STORAGE_BACKEND`, and
   `DATA_DIR` from environment variables at startup.
6. THE Event_Service SHALL run with working directory
   `Exam/techconf-exam/services/event-service` when that directory is configured as the
   event-service `cwd` in `services.yaml`.

### Requirement 17: Conform to the OpenAPI Contract (REQ-EVT-OA01)

**User Story:** As a service consumer, I want responses to match the immutable OpenAPI
contract, so that integrations can rely on a stable interface.

#### Acceptance Criteria

1. THE Event_Service SHALL implement every operation declared by OpenAPI_Contract:
   health, createEvent, listEvents, getEvent, replaceEvent, updateEvent, and
   deleteEvent.
2. WHEN Event_Service returns a response body, THE Event_Service SHALL set
   `Content-Type` to `application/json`.
3. WHEN Event_Service returns an Event, Page, Health, or Error response, THE
   Event_Service SHALL include only fields allowed by the corresponding OpenAPI schema.
4. THE Event_Service SHALL use snake_case JSON field names.
5. THE Event_Service SHALL return the success and error status codes declared for each
   operation by OpenAPI_Contract.
6. THE Event_Service SHALL preserve OpenAPI_Contract and the instructor integration
   tests without modification.

### Requirement 18: Use the Prescribed Technology Platform (REQ-EVT-PLAT01)

**User Story:** As a TechConf developer, I want event-service to use the prescribed
runtime and test toolchain, so that the service runs in the shared exam environment.

#### Acceptance Criteria

1. THE Event_Service SHALL run on Python 3.12.
2. THE Event_Service SHALL expose the HTTP interface using Flask.
3. WHEN Event_Service calls User_Service, THE Event_Service SHALL use the `requests`
   runtime dependency.
4. THE Event_Service SHALL require no external database management system.
5. THE Event_Service_Test_Suite SHALL run with `pytest` and measure coverage with
   `pytest-cov`.
6. WHERE a unit test simulates User_Service HTTP behavior, THE Event_Service_Test_Suite
   SHALL use `responses`.
7. THE Event_Service_Project SHALL exclude runtime data under `data/` from Git.

## Traceability Summary

| Exam or contract concern | Requirement coverage |
|---|---|
| Event fields and read-only metadata | REQ-EVT-C01, REQ-EVT-V01 |
| POST `/api/v1/events` and 400/422/503 behavior | REQ-EVT-C01, REQ-EVT-V01, REQ-EVT-B01, REQ-EVT-B02, REQ-EVT-B03, REQ-EVT-B05 |
| GET collection, pagination, `status`/`city` filters | REQ-EVT-C02, REQ-EVT-B06 |
| GET by Resource_ID and 404 | REQ-EVT-C03 |
| PUT replacement and 400/404/422/503 behavior | REQ-EVT-C04, REQ-EVT-B01 through REQ-EVT-B05 |
| PATCH update and 400/404/422/503 behavior | REQ-EVT-C05, REQ-EVT-B01 through REQ-EVT-B05 |
| DELETE and 204/404 behavior | REQ-EVT-C06 |
| Organizer existence | REQ-EVT-B01 |
| Organizer role | REQ-EVT-B02 |
| Date ordering | REQ-EVT-B03 |
| Lifecycle transitions | REQ-EVT-B04 |
| Dependency resilience and 2-second timeout | REQ-EVT-B05 |
| Event list filters | REQ-EVT-B06 |
| Error envelope and 405 behavior | REQ-EVT-ERR01 |
| Health endpoint | REQ-EVT-H01 |
| memory/json/sqlite persistence | REQ-EVT-S01 |
| `PORT`, `USER_SERVICE_URL`, `STORAGE_BACKEND`, `DATA_DIR` | REQ-EVT-CFG01 |
| OpenAPI response conformance | REQ-EVT-OA01 |
| Python/Flask/requests and pytest toolchain | REQ-EVT-PLAT01 |
| Runtime data excluded from Git | REQ-EVT-S01, REQ-EVT-PLAT01 |
