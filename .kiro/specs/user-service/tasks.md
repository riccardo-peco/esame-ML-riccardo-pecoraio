# Implementation Plan: user-service

## Overview

Implementazione del **user-service** Flask per la gestione degli utenti della conferenza. Il servizio espone una REST API (prefisso `/api/v1/users`) con tre backend di storage intercambiabili (memory, JSON, SQLite). I task vanno eseguiti **in ordine**, uno alla volta da Kiro ("Start task"), con un commit per task: `feat(user-service): <descrizione> [T-xx]`.

## Tasks

- [x] **T-01** Scheletro del servizio: `app.py`, `config.py` (legge `PORT`/`STORAGE_BACKEND`/`DATA_DIR`), endpoint `GET /health`
  _Requirements: REQ-USR-06, REQ-USR-08_

- [x] **T-02** Modello dominio `User` e interfaccia `repository/base.py` (id UUID v4, `created_at`/`updated_at`)
  _Requirements: REQ-USR-01 (p.1)_

- [x] **T-03** `repository/memory_repo.py` + `factory.py` con default `memory`
  _Requirements: REQ-USR-07_

- [x] **T-04** `repository/json_repo.py`
  _Requirements: REQ-USR-07_

- [x] **T-05** `repository/sqlite_repo.py`
  _Requirements: REQ-USR-07_

- [x] **T-06** `errors.py` con formato errore comune + errorhandler Flask per `ValidationError`/`NotFoundError`/`ConflictError`, gestione `400` per JSON malformato
  _Requirements: REQ-USR-01 (p.7)_

- [x] **T-07** `POST /api/v1/users`: validazione campi, default `role=attendee`, `201` + `Location`
  _Requirements: REQ-USR-01_

- [x] **T-08** Unicità email case-insensitive e normalizzazione lowercase su creazione
  _Requirements: REQ-USR-B01, REQ-USR-B02_

- [x] **T-09** `pagination.py` + `GET /api/v1/users` con `page`/`page_size` e validazione
  _Requirements: REQ-USR-02_

- [x] **T-10** Filtri `role` ed `email` sulla lista
  _Requirements: REQ-USR-B03_

- [x] **T-11** `GET /api/v1/users/{id}` con `404`
  _Requirements: REQ-USR-03_

- [x] **T-12** `PUT`/`PATCH /api/v1/users/{id}` (validazione, unicità email, `404`, `updated_at`)
  _Requirements: REQ-USR-04, REQ-USR-B01, REQ-USR-B02_

- [x] **T-13** `DELETE /api/v1/users/{id}` con `204`/`404`
  _Requirements: REQ-USR-05_

- [x] **T-14** Unit test repository sui tre backend (`tmp_path` per json/sqlite)
  _Requirements: REQ-USR-07_

- [x] **T-15** Unit test regole di business (creazione, unicità, filtri, transizioni CRUD)
  _Requirements: REQ-USR-01, B01, B02, B03, 02–05_

- [x] **T-16** Un test di contratto per endpoint con `assert_matches_contract`
  _Requirements: tutti gli endpoint del §5.1_

- [x] **T-17** Verifica coverage ≥ 80% (`pytest --cov=. --cov-report=term-missing`) e sezione README per user-service (avvio, env var, comando test)
  _Requirements: checklist §9_

## Task Dependency Graph

```
T-01 (scheletro app)
└── T-02 (modello User + base repo)
    ├── T-03 (memory_repo + factory)
    │   ├── T-04 (json_repo)
    │   ├── T-05 (sqlite_repo)
    │   └── T-06 (errors + handlers)
    │       ├── T-07 (POST /users)
    │       │   ├── T-08 (unicità email)
    │       │   │   ├── T-09 (GET /users + paginazione)
    │       │   │   │   └── T-10 (filtri role/email)
    │       │   │   ├── T-11 (GET /users/{id})
    │       │   │   ├── T-12 (PUT/PATCH /users/{id})
    │       │   │   └── T-13 (DELETE /users/{id})
    │       │   └── T-14 (unit test repository)
    │       └── T-15 (unit test business logic)
    └── T-16 (contract test)
        └── T-17 (coverage + README)
```

## Notes

- Ogni task deve terminare con un commit usando il formato: `feat(user-service): <descrizione> [T-xx]`
- Il backend di storage è selezionabile via variabile d'ambiente `STORAGE_BACKEND` (`memory` | `json` | `sqlite`); default `memory`
- I test di unità usano sempre il backend `memory` salvo dove indicato; json/sqlite usano `tmp_path` di pytest
- La coverage target è ≥ 80% misurata con `pytest --cov=. --cov-report=term-missing`
- I task T-14/T-15/T-16 possono essere eseguiti in parallelo una volta completati T-05/T-13
