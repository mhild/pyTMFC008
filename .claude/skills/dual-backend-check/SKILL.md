---
name: dual-backend-check
description: Quickly verify a change against both PostgreSQL and Oracle (unit tests, migrations, integration tests per backend; no benchmark, no report). Use after any change to the query layer, models, migrations, API handlers or tests, before committing.
---

# Check a change against PostgreSQL and Oracle

Every feature must behave identically on both backends; the integration tests are backend-neutral and must
pass unchanged on both. For full results plus benchmark use the `test-report` skill instead.

1. **Unit tests (no database):** `pytest tests/pytest/test_query.py -q`
   – parser and both SQL renderers; fast, run them first.
2. **Databases:** `docker compose up -d db oracle`, wait for `healthy` in `docker compose ps`. An external database
   works the same: point `PG` / `ORA` at its host instead (the stack's databases are only a convenience).
   ```bash
   export PG=postgresql+asyncpg://app:secret@localhost:5432/app_db
   export ORA='oracle+oracledb_async://app:secret@localhost:1521/?service_name=FREEPDB1'
   ```
3. **Migrations:** `DATABASE_URL=$PG alembic upgrade head` and the same for `$ORA`.
   If the change adds a migration, also check that it reverses on both:
   `alembic downgrade -1 && alembic upgrade head` per backend. Oracle DDL is not transactional – a failed
   migration can leave a half-applied state; clean up by hand before retrying.
4. **Start one API per backend** in the background with pid files (don't `pkill -f` – it can kill your own shell):
   ```bash
   DATABASE_URL=$PG  nohup uvicorn openapi_server.main:app --port 8001 > <scratchpad>/pg.log 2>&1 & echo $! > <scratchpad>/pg.pid
   DATABASE_URL=$ORA nohup uvicorn openapi_server.main:app --port 8002 > <scratchpad>/ora.log 2>&1 & echo $! > <scratchpad>/ora.pid
   ```
   Wait until `curl -sf 'http://127.0.0.1:800{1,2}/service?limit=1'` succeeds.
5. **Integration tests per backend:**
   ```bash
   TMF_BASE_URL=http://127.0.0.1:8001 pytest tests/pytest -q
   TMF_BASE_URL=http://127.0.0.1:8002 pytest tests/pytest -q
   ```
   Tests skip (not fail) when the API is unreachable – a run with only skips means the server didn't start;
   look at the uvicorn log.
6. **Stop the APIs** via the pid files; leave the database containers running.
7. Report the pytest summary line per backend; on failure include the failing output and the uvicorn log excerpt.

## Typical backend differences

* **Oracle array filters:** a filter after a key needs `[*]` (`$.a[*] ? (...)`), otherwise conditions match across
  different array elements. `render._path_text` adds it – keep it when changing the renderer.
* **Oracle JSON_EXISTS:** the path must be a literal; values go in via `PASSING :bind AS "vN"`. Never put user input
  into the path text – only validated keys (`KEY_RE`) and fixed tokens.
* **Oracle numbers** come back as `Decimal`; `models._plain_numbers` converts them – needed for anything that
  serializes payloads (e.g. PATCH).
* **PostgreSQL index use:** only operators (`@?`, `@>`) use the GIN index, `jsonb_path_exists()` does not.
  Its row estimates for JSON conditions are a flat guess – verify plans with `scripts/bench.py --plans` when a query
  gets slower.
