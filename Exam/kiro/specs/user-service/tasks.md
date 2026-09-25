# Tasks — user-service

Esegui i task **in ordine**, uno alla volta da Kiro ("Start task"), con un commit per task: `feat(user-service): <descrizione> [T-xx]`.

- [ ] **T-01** Scheletro del servizio: `app.py`, `config.py` (legge `PORT`/`STORAGE_BACKEND`/`DATA_DIR`), endpoint `GET /health`
  _Requirements: REQ-USR-06, REQ-USR-08_

- [ ] **T-02** Modello dominio `User` e interfaccia `repository/base.py` (id UUID v4, `created_at`/`updated_at`)
  _Requirements: REQ-USR-01 (p.1)_

- [ ] **T-03** `repository/memory_repo.py` + `factory.py` con default `memory`
  _Requirements: REQ-USR-07_

- [ ] **T-04** `repository/json_repo.py`
  _Requirements: REQ-USR-07_

- [ ] **T-05** `repository/sqlite_repo.py`
  _Requirements: REQ-USR-07_

- [ ] **T-06** `errors.py` con formato errore comune + errorhandler Flask per `ValidationError`/`NotFoundError`/`ConflictError`, gestione `400` per JSON malformato
  _Requirements: REQ-USR-01 (p.7)_

- [ ] **T-07** `POST /api/v1/users`: validazione campi, default `role=attendee`, `201` + `Location`
  _Requirements: REQ-USR-01_

- [ ] **T-08** Unicità email case-insensitive e normalizzazione lowercase su creazione
  _Requirements: REQ-USR-B01, REQ-USR-B02_

- [ ] **T-09** `pagination.py` + `GET /api/v1/users` con `page`/`page_size` e validazione
  _Requirements: REQ-USR-02_

- [ ] **T-10** Filtri `role` ed `email` sulla lista
  _Requirements: REQ-USR-B03_

- [ ] **T-11** `GET /api/v1/users/{id}` con `404`
  _Requirements: REQ-USR-03_

- [ ] **T-12** `PUT`/`PATCH /api/v1/users/{id}` (validazione, unicità email, `404`, `updated_at`)
  _Requirements: REQ-USR-04, REQ-USR-B01, REQ-USR-B02_

- [ ] **T-13** `DELETE /api/v1/users/{id}` con `204`/`404`
  _Requirements: REQ-USR-05_

- [ ] **T-14** Unit test repository sui tre backend (`tmp_path` per json/sqlite)
  _Requirements: REQ-USR-07_

- [ ] **T-15** Unit test regole di business (creazione, unicità, filtri, transizioni CRUD)
  _Requirements: REQ-USR-01, B01, B02, B03, 02–05_

- [ ] **T-16** Un test di contratto per endpoint con `assert_matches_contract`
  _Requirements: tutti gli endpoint del §5.1_

- [ ] **T-17** Verifica coverage ≥ 80% (`pytest --cov=. --cov-report=term-missing`) e sezione README per user-service (avvio, env var, comando test)
  _Requirements: checklist §9_