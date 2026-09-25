# Requirements — user-service

Base path `/api/v1/users`, porta `5001`. Anagrafica utenti della piattaforma.

### REQ-USR-01 — Creazione utente
**User story:** As a client application, I want to register a new user, so that they can take part in conferences.

**Acceptance criteria**
1. WHEN a client submits `POST /api/v1/users` with a valid body THE user-service SHALL create the user with a server-generated UUID v4 `id`, `created_at` and `updated_at` in ISO 8601 UTC, and respond `201` with header `Location` and a body matching `contracts/openapi/user-service.yaml`
2. IF `first_name` or `last_name` is missing, empty, or longer than 50 characters THEN THE user-service SHALL respond `422` with error code `VALIDATION_ERROR`
3. IF `email` is missing or not a valid email format THEN THE user-service SHALL respond `422` with error code `VALIDATION_ERROR`
4. IF `company` is present and longer than 100 characters THEN THE user-service SHALL respond `422` with error code `VALIDATION_ERROR`
5. IF `role` is present and not one of `attendee`, `speaker`, `organizer` THEN THE user-service SHALL respond `422` with error code `VALIDATION_ERROR`
6. WHEN `role` is not provided THE user-service SHALL default it to `attendee`
7. IF the request body is not valid JSON THEN THE user-service SHALL respond `400`

### REQ-USR-B01 — Email univoca
**User story:** As the platform, I want each email to identify a single user, so that accounts stay unambiguous.

**Acceptance criteria**
1. IF an existing user has the same `email`, compared case-insensitively, THEN THE user-service SHALL respond `409` with error code `EMAIL_ALREADY_EXISTS`
2. This rule applies both on `POST` and on `PUT`/`PATCH` when the email is changed to one already in use by another user

### REQ-USR-B02 — Email normalizzata
**Acceptance criteria**
1. WHEN a user is created or its email updated THE user-service SHALL store `email` lower-cased, regardless of the case submitted by the client

### REQ-USR-02 — Lista paginata e filtri
**User story:** As a client application, I want to list and filter users, so that I can find the right ones.

**Acceptance criteria**
1. WHEN a client calls `GET /api/v1/users` THE user-service SHALL respond `200` with `{"items": [...], "page": 1, "page_size": 20, "total": N}` using defaults `page=1`, `page_size=20`
2. IF `page_size` is greater than 100 THEN THE user-service SHALL respond `422` with error code `VALIDATION_ERROR`
3. IF `page` or `page_size` is not a positive integer THEN THE user-service SHALL respond `422` with error code `VALIDATION_ERROR`

### REQ-USR-B03 — Filtri per role ed email
**Acceptance criteria**
1. WHEN `role` is provided as a query parameter THE user-service SHALL return only users with that `role`
2. WHEN `email` is provided as a query parameter THE user-service SHALL return only the user matching that email, case-insensitively

### REQ-USR-03 — Lettura per id
**Acceptance criteria**
1. WHEN a client calls `GET /api/v1/users/{id}` with an existing `id` THE user-service SHALL respond `200` with the user
2. IF `id` does not correspond to any user THEN THE user-service SHALL respond `404` with error code `NOT_FOUND`

### REQ-USR-04 — Aggiornamento (PUT / PATCH)
**Acceptance criteria**
1. WHEN a client calls `PUT /api/v1/users/{id}` with a full valid body on an existing user THE user-service SHALL replace the updatable fields, update `updated_at`, and respond `200`
2. WHEN a client calls `PATCH /api/v1/users/{id}` with a partial valid body on an existing user THE user-service SHALL update only the provided fields, update `updated_at`, and respond `200`
3. IF `id` does not correspond to any user THEN THE user-service SHALL respond `404` with error code `NOT_FOUND`
4. Validation rules from REQ-USR-01 (points 2–5) and uniqueness from REQ-USR-B01 apply identically on update

### REQ-USR-05 — Cancellazione
**Acceptance criteria**
1. WHEN a client calls `DELETE /api/v1/users/{id}` on an existing user THE user-service SHALL delete it and respond `204`
2. IF `id` does not correspond to any user THEN THE user-service SHALL respond `404` with error code `NOT_FOUND`

### REQ-USR-06 — Health check
**Acceptance criteria**
1. WHEN a client calls `GET /health` THE user-service SHALL respond `200` with `{"status": "ok", "service": "user-service"}`

### REQ-USR-07 — Persistenza intercambiabile
**Acceptance criteria**
1. WHEN `STORAGE_BACKEND` is `memory`, `json`, or `sqlite` THE user-service SHALL persist and read data through the corresponding repository without any change to the business rules above
2. WHEN `STORAGE_BACKEND` is `json` or `sqlite` THE user-service SHALL store files under `DATA_DIR` (default `./data`)

### REQ-USR-08 — Avvio e porta
**Acceptance criteria**
1. WHEN the process starts THE user-service SHALL listen on the port given by the `PORT` environment variable