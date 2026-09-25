# user-service

Microservizio registro utenti della piattaforma **TechConf**. Gestisce anagrafica e
ruoli dei partecipanti (attendee, speaker, organizer) ed espone una REST API su cui si
appoggiano gli altri servizi per validare l'esistenza e il ruolo di un utente.

Conforme al contratto OpenAPI `contracts/openapi/user-service.yaml`.

## Avvio / Running the service

```
pip install -r requirements.txt
python app.py
```

Il servizio è in ascolto sulla porta **5001** di default (configurabile via `PORT`).
Endpoint di verifica: `GET http://localhost:5001/health`.

## Variabili d'ambiente / Environment variables

Tutta la configurazione è letta dalle variabili d'ambiente all'avvio (nessun valore
hard-coded nel sorgente).

| Variabile         | Default    | Descrizione                                                        |
|-------------------|------------|--------------------------------------------------------------------|
| `PORT`            | `5001`     | Porta TCP su cui il servizio ascolta.                              |
| `STORAGE_BACKEND` | `memory`   | Backend di persistenza: `memory` \| `json` \| `sqlite`.            |
| `DATA_DIR`        | `./data`   | Directory usata dai backend `json`/`sqlite` per persistere i dati. |

I tre backend espongono la stessa API HTTP: cambiare backend non richiede modifiche alla
logica di business o alle route.

## Endpoints

| Metodo | Path                     | Descrizione                                                        |
|--------|--------------------------|--------------------------------------------------------------------|
| GET    | `/health`                | Health check → `{"status": "ok", "service": "user-service"}`.      |
| POST   | `/api/v1/users`          | Crea un utente (default `role=attendee`); risponde `201` + `Location`. |
| GET    | `/api/v1/users`          | Lista paginata; query: `page`, `page_size` (1–100), `role`, `email`. |
| GET    | `/api/v1/users/{id}`     | Recupera un utente per id (`404` se assente).                      |
| PUT    | `/api/v1/users/{id}`     | Sostituzione completa dell'utente.                                 |
| PATCH  | `/api/v1/users/{id}`     | Aggiornamento parziale dei campi.                                  |
| DELETE | `/api/v1/users/{id}`     | Elimina un utente (`204` / `404`).                                 |

Le email sono normalizzate e confrontate in minuscolo; l'unicità (case-insensitive) è
garantita in creazione e aggiornamento (`409 EMAIL_ALREADY_EXISTS`).

## Test

```
python -m pytest
python -m pytest --cov=. --cov-report=term-missing
```

Suite: **92 test**, tutti verdi. Copertura totale del codice di produzione **94%**
(≥ 80% richiesto dalla checklist §9). La configurazione di coverage è in `.coveragerc`
(esclude `tests/` e il blocco `if __name__ == "__main__":`).
