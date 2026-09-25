# Stato consegna — TechConf (esame Spec-Driven con Kiro)

Documento di avanzamento: cosa e' fatto, cosa manca, dove riprendere.
Aggiornato durante la sessione di sviluppo.

## Struttura del repository

I servizi vivono sotto `Exam/techconf-exam/services/<nome>-service`, coerente con
`Exam/techconf-exam/services.yaml` (cwd `services/<nome>-service`, comando `python -m app`).
La suite di collaudo immutabile e i contratti sono in `Exam/techconf-exam/`.

## Fatto

### user-service — COMPLETO (obbligatorio #1)
- Spec Requirements-First completa in `.kiro/specs/user-service/` (requirements, design, tasks: tutti i 17 task spuntati).
- Implementazione CRUD `/api/v1/users`, validazione, unicita' email case-insensitive,
  paginazione + filtri, 3 backend storage (memory/json/sqlite, solo stdlib), GET /health.
- Test: 92 verdi, coverage 94% (unit sui 3 backend, business, 9 contract test con assert_matches_contract).
- README di servizio + .coveragerc.

### event-service — IN CORSO (obbligatorio #2), T-01..T-08 su 19 fatti
Spec completa e committata in `.kiro/specs/event-service/` (requirements, design, tasks).
Task completati (un commit per task):
- T-01 scheletro app (python -m app), config (PORT/STORAGE_BACKEND/DATA_DIR/USER_SERVICE_URL), GET /health
- T-02 modello Event + EventStatus + is_valid_transition + repository/base
- T-03 memory_repo + factory
- T-04 json_repo
- T-05 sqlite_repo
- T-06 errors.py + error handler Flask (422 VALIDATION_ERROR/REFERENCE_NOT_FOUND/INVALID_ORGANIZER/
  INVALID_STATUS_TRANSITION, 404 NOT_FOUND, 503 DEPENDENCY_UNAVAILABLE, 400, 405)
- T-07 clients/user_client.py (GET user-service, timeout 2s, mapping 404->422 REFERENCE_NOT_FOUND,
  role!=organizer->422 INVALID_ORGANIZER, timeout/refused/5xx->503 DEPENDENCY_UNAVAILABLE)
- T-08 validation.py + POST /api/v1/events (validazione campi, date, default draft, check organizzatore, 201+Location)

## Da fare (riprendere da qui)

### event-service — task rimanenti T-09..T-19
- T-09 GET /api/v1/events lista con page/page_size + filtri status/city (422 su status invalido)
- T-10 GET /api/v1/events/{id} con 404
- T-11 PUT/PATCH /api/v1/events/{id}: validazione, 404, updated_at, re-validazione organizer
  quando organizer_id cambia, regole di transizione stato (REQ-EVT-B04)
- T-12 DELETE /api/v1/events/{id} con 204/404
- T-14 unit test repository (3 backend, tmp_path)
- T-15 unit test regole di business con user-service mockato con `responses`
- T-16 contract test per endpoint con assert_matches_contract
- T-17 integration test propri (avvia user-service reale: 201, 422 REFERENCE_NOT_FOUND, 503 DEPENDENCY_UNAVAILABLE)
- T-18 coverage >=80%, RIATTIVARE il blocco `event` in services.yaml, README event-service
- Le checkbox di tasks.md vanno aggiornate a mano (il task-tool Kiro non e' attivo su questa spec).

### registration-service — DA FARE INTERAMENTE (obbligatorio #3)
- Creare spec Requirements-First (`.kiro/specs/registration-service/`), poi implementare.
- Chiama user + event. Regole REQ-REG-B01..B09: user/event esistenti (422 REFERENCE_NOT_FOUND),
  evento published (422 EVENT_NOT_OPEN), no doppia iscrizione confirmed (409 ALREADY_REGISTERED),
  capienza (409 EVENT_FULL), amount = event.price, transizione confirmed->cancelled (422 altrimenti),
  endpoint stats, PUT -> 405, dipendenza giu' -> 503.

### Setup Kiro (§6.1) — MANCANTE, richiesto dalla checklist §9
- `.kiro/steering/product.md`, `tech.md`, `structure.md` (deve rispondere alle domande §7),
  `platform-standards.md` (il §4 della traccia).
- Almeno 1 Agent Hook (es. run test unit su salvataggio file Python).

### Consegna (§9) — MANCANTE
- BUGS.md con >= 2 bug chiusi (>=1 di implementazione), con issue e test di regressione.
- collaudo.txt = output di `pytest tests/integration -m mandatory`.
- README.md alla root (avvio, variabili d'ambiente, comandi test).
- .gitignore alla root (esiste solo in Exam/techconf-exam/): escludere data/, __pycache__, .coverage, .pytest_cache.
- Tag `v1.0.0` su main.

## Note operative
- Comando test per servizio (dalla cartella del servizio): `python -m pytest`
  e `python -m pytest --cov=. --cov-report=term-missing`.
- Suite di collaudo (dalla root della suite Exam/techconf-exam):
  `pip install -r tests/integration/requirements.txt` poi `pytest tests/integration -m mandatory -v`.
  Un servizio non dichiarato in services.yaml risulta SKIPPED, non fallito.
- Vincoli esame: NON modificare `contracts/` ne' `tests/integration/` (checksum, penalita' -20).
  NON scrivere codice prima del commit di tasks.md (workflow Requirements-First).
  URL degli altri servizi SOLO da variabili d'ambiente (*_SERVICE_URL).
