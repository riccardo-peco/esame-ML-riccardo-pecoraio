# Design — user-service

Riferimento contratto: `contracts/openapi/user-service.yaml` (fonte di verità per campi, tipi e status code — ogni endpoint qui sotto deve rispettarlo).

## Componenti

```
services/user-service/
  app.py               # crea la app Flask, registra la blueprint, avvia su PORT
  config.py            # legge PORT, STORAGE_BACKEND, DATA_DIR
  api/routes.py         # HTTP: parsing query/body, chiamata al service layer, status code
  domain/
    models.py            # dataclass User
    service.py            # REQ-USR-01, B01, B02, B03, 02..05 (regole di business)
  repository/
    base.py                # interfaccia: create/get/list/update/delete
    memory_repo.py
    json_repo.py
    sqlite_repo.py
    factory.py              # sceglie l'implementazione da STORAGE_BACKEND
  errors.py                 # formato errore comune {"error": {code, message, details}}
  pagination.py              # helper page/page_size/total
  tests/
    unit/
    integration/            # non necessari qui: user-service non chiama altri servizi (§5.1: "Chiama —")
```

## Persistenza

`repository/base.py` definisce l'interfaccia usata da `domain/service.py`. `factory.py`, chiamato da `app.py` all'avvio, istanzia `MemoryUserRepository`, `JsonUserRepository` o `SqliteUserRepository` in base a `STORAGE_BACKEND` e la inietta nel service layer. Le tre implementazioni espongono la stessa interfaccia (`create`, `get`, `list(filters, page, page_size)`, `update`, `delete`), quindi `domain/service.py` non sa mai quale backend è attivo.

- `memory`: dizionario `{id: User}` in RAM.
- `json`: un file `DATA_DIR/users.json` con lock su file per evitare scritture concorrenti corrotte (accettabile: unico processo per servizio).
- `sqlite`: `DATA_DIR/users.db`, tabella `users`, libreria standard `sqlite3`.

L'indice per l'unicità email (REQ-USR-B01) è calcolato a runtime nel service layer con un confronto case-insensitive sulla lista letta dal repository, non delegato al backend, così il comportamento è identico sui tre backend.

## Chiamate ad altri servizi

Nessuna: user-service è la base della catena (§2 dell'architettura), non chiama né event-service né registration-service.

## Gestione errori

`errors.py` espone `error_response(code, message, details=None)` → JSON nel formato piattaforma, usato da tutti gli endpoint. Le eccezioni di dominio (`ValidationError`, `NotFoundError`, `ConflictError`) sono catturate da un errorhandler Flask registrato in `app.py`, che le mappa a 422/404/409.

## Strategia di test

- **Unit**: repository testato con tutti e tre i backend usando `tmp_path` per `json`/`sqlite`; regole di business (`REQ-USR-01`, `B01`, `B02`, `B03`, `02`–`05`) testate sul service layer senza Flask; almeno un test per endpoint che valida la risposta con `contracts.validator.assert_matches_contract("user-service", method, path, response)`.
- **Contratto**: incluso nei test unit come sopra (nessun test separato).
- **Integrazione propria**: non richiesta per user-service, dato che non ha dipendenze in uscita (il requisito del §6.3 si applica ai servizi che *chiamano* altri servizi).
- **Copertura**: `pytest --cov=. --cov-report=term-missing`, target ≥ 80%.