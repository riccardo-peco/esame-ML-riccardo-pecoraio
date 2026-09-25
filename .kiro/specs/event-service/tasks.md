# Implementation Plan: event-service

## Overview

Implementazione del **event-service** Flask per la gestione degli eventi (conferenze) della
piattaforma TechConf. Il servizio espone una REST API (prefisso `/api/v1/events`) con tre
backend di storage intercambiabili (memory, JSON, SQLite) e valida l'organizzatore
chiamando user-service via HTTP. I task vanno eseguiti **in ordine**, uno alla volta da Kiro
("Start task"), con un commit per task: `feat(event-service): <descrizione> [T-xx]`. Il
servizio si avvia con `python -m app` (come dichiarato in `services.yaml`).

## Tasks

- [x] **T-01** Scheletro del servizio: `app.py` avviabile con `python -m app`, `config.py`
  che legge `PORT`/`STORAGE_BACKEND`/`DATA_DIR`/`USER_SERVICE_URL`, endpoint `GET /health`
  → `200 {"status":"ok","service":"event-service"}`
  _Requirements: REQ-EVT-H01, REQ-EVT-CFG01_

- [x] **T-02** Modello dominio `Event` + enum `EventStatus` e interfaccia
  `repository/base.py` (id UUID v4, `created_at`/`updated_at`, `price` a 2 decimali)
  _Requirements: REQ-EVT-C01 (p.3), REQ-EVT-V01_

- [x] **T-03** `repository/memory_repo.py` + `factory.py` con default `memory`
  _Requirements: REQ-EVT-S01_

- [x] **T-04** `repository/json_repo.py`
  _Requirements: REQ-EVT-S01_

- [x] **T-05** `repository/sqlite_repo.py`
  _Requirements: REQ-EVT-S01_

- [x] **T-06** `errors.py` con formato errore comune + eccezioni di dominio + errorhandler
  Flask (mappatura 422 `VALIDATION_ERROR`/`REFERENCE_NOT_FOUND`/`INVALID_ORGANIZER`/
  `INVALID_STATUS_TRANSITION`, 404 `NOT_FOUND`, 503 `DEPENDENCY_UNAVAILABLE`), gestione
  `400` per JSON malformato e `405` per metodo non previsto
  _Requirements: REQ-EVT-OA01 (p.4), REQ-EVT-B05_

- [x] **T-07** `clients/user_client.py`: client HTTP verso user-service
  (`GET {USER_SERVICE_URL}/api/v1/users/{id}`, timeout 2s), mappatura 404 →
  `ReferenceNotFoundError`, `role!=organizer` → `InvalidOrganizerError`,
  timeout/ConnectionError/5xx → `DependencyUnavailableError`
  _Requirements: REQ-EVT-B01, REQ-EVT-B02, REQ-EVT-B05_

- [x] **T-08** `domain/service.py` + `POST /api/v1/events`: validazione campi
  (`title` 3–120, `venue` ≤100, `city` ≤60, `capacity` 1–10000, `price` ≥0,
  `description` ≤2000), `end_date` ≥ `start_date`, default `status=draft`, validazione
  organizzatore, `201` + `Location`
  _Requirements: REQ-EVT-C01, REQ-EVT-B01, REQ-EVT-B02, REQ-EVT-B03, REQ-EVT-V01_

- [ ] **T-09** `pagination.py` + `GET /api/v1/events` con `page`/`page_size` e filtri
  `status`/`city` (422 su `status` invalido)
  _Requirements: REQ-EVT-B06_

- [ ] **T-10** `GET /api/v1/events/{id}` con `404`
  _Requirements: REQ-EVT-C02_

- [ ] **T-11** `PUT`/`PATCH /api/v1/events/{id}`: validazione, `404`, `updated_at`,
  re-validazione organizzatore quando `organizer_id` cambia, regole di transizione stato
  (`draft→published`, `draft→cancelled`, `published→cancelled`, no-op; altrimenti 422
  `INVALID_STATUS_TRANSITION`)
  _Requirements: REQ-EVT-C03, REQ-EVT-C04, REQ-EVT-B02, REQ-EVT-B03, REQ-EVT-B04, REQ-EVT-B05_

- [ ] **T-12** `DELETE /api/v1/events/{id}` con `204`/`404`
  _Requirements: REQ-EVT-C05_

- [ ] **T-13** Checkpoint — assicurarsi che tutti i test passino; chiedere all'utente in
  caso di dubbi.

- [ ] **T-14** Unit test repository sui tre backend (`tmp_path` per json/sqlite)
  _Requirements: REQ-EVT-S01_

- [ ] **T-15** Unit test regole di business con chiamate a user-service mockate con
  `responses` (organizzatore valido, `INVALID_ORGANIZER`, `REFERENCE_NOT_FOUND`,
  `DEPENDENCY_UNAVAILABLE`, transizioni valide/invalide, date, validazione campi)
  _Requirements: REQ-EVT-B01, B02, B03, B04, B05, B06, C01–C05, V01_

- [ ] **T-16** Un test di contratto per endpoint con `assert_matches_contract`
  _Requirements: REQ-EVT-OA01, tutti gli endpoint del §5.2_

- [ ] **T-17** Integration test propri: fixture che avvia user-service reale su porta
  libera — caso positivo (201), organizzatore inesistente (422 `REFERENCE_NOT_FOUND`),
  user-service spento (503 `DEPENDENCY_UNAVAILABLE`)
  _Requirements: REQ-EVT-B01, REQ-EVT-B05_

- [ ] **T-18** Verifica coverage ≥ 80% (`pytest --cov=. --cov-report=term-missing`),
  aggiornamento `services.yaml` (blocco `event` non commentato) e sezione README per
  event-service (avvio, env var incl. `USER_SERVICE_URL`, comandi di test)
  _Requirements: checklist §9_

- [ ] **T-19** Checkpoint finale — assicurarsi che unit, contratto e integration test
  passino; chiedere all'utente in caso di dubbi.

## Notes

- Ogni task deve terminare con un commit usando il formato:
  `feat(event-service): <descrizione> [T-xx]`
- Il backend di storage è selezionabile via `STORAGE_BACKEND` (`memory` | `json` |
  `sqlite`); default `memory`. I test di unità usano `memory` salvo dove indicato;
  json/sqlite usano `tmp_path` di pytest.
- L'URL di user-service arriva **solo** da `USER_SERVICE_URL` (default
  `http://localhost:5001`), mai hard-coded. Timeout 2s.
- La coverage target è ≥ 80% misurata con `pytest --cov=. --cov-report=term-missing`.
- I test T-14/T-15/T-16 possono essere eseguiti in parallelo una volta completato T-12.
- Questo workflow crea solo gli artefatti di spec e pianificazione: l'implementazione
  avviene eseguendo i task da Kiro ("Start task"), uno alla volta.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["T-01"] },
    { "id": 1, "tasks": ["T-02"] },
    { "id": 2, "tasks": ["T-03", "T-06", "T-07"] },
    { "id": 3, "tasks": ["T-04", "T-05", "T-08"] },
    { "id": 4, "tasks": ["T-09", "T-10", "T-11", "T-12"] },
    { "id": 5, "tasks": ["T-14", "T-15", "T-16"] },
    { "id": 6, "tasks": ["T-17"] },
    { "id": 7, "tasks": ["T-18"] }
  ]
}
```
