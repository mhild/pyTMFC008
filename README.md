# pyTMFC008 – TMF638 Service Inventory on JSON columns (PostgreSQL & Oracle)

PoC of the TM Forum component *Service Inventory* (TMFC008) with a TMF638 v5 API (FastAPI).
Each service is stored as **one JSON document in a single column**; CRUD and
TMF630 query parameters map directly onto the database's JSON operators:

| | PostgreSQL 16 | Oracle 23ai Free |
|---|---|---|
| Column type | `JSONB` | `JSON` (native, OSON binary format) |
| Filter | `payload @? CAST(:p AS jsonpath)` | `JSON_EXISTS(payload, '<path>' PASSING :v0 AS "v0")` |
| Index | 1 × GIN `jsonb_path_ops` (covers every attribute) | Multivalue indexes per search path (+ JSON search index if Oracle Text is installed) |

## Getting started

1. Start the databases:
   ```bash
   docker compose up -d db oracle            # Oracle needs 1–2 min on first start
   ```
2. Start the app – **either** against PostgreSQL, using `DATABASE_URL` from `.env` (default):
   ```bash
   docker compose up -d --build app
   ```
   **or** against Oracle, by overriding `DATABASE_URL` for this one command:
   ```bash
   DATABASE_URL='oracle+oracledb_async://app:secret@oracle:1521/?service_name=FREEPDB1' \
     docker compose up -d --build app
   ```

The backend is chosen solely by `DATABASE_URL`. `docker-compose.yml` passes `${DATABASE_URL}` to the app, and
Docker Compose takes a variable set in the shell over the value in `.env`. So the second variant doesn't need
`.env` to be edited; alternatively switch the commented `DATABASE_URL` line in `.env`.
There is only one `app` container: starting it with a different `DATABASE_URL` recreates it against the other
database. Inside the compose network the databases are reached by their service names (`db`, `oracle`); from the host
use `localhost` (see below).

The entrypoint waits for the database (`scripts/wait_for_db.py`) and runs `alembic upgrade head`.
API: http://127.0.0.1:8080/service, OpenAPI UI: http://127.0.0.1:8080/docs

Locally without a container (databases from compose, ports 5432/1521):

```bash
DATABASE_URL=postgresql+asyncpg://app:secret@localhost:5432/app_db alembic upgrade head
DATABASE_URL=postgresql+asyncpg://app:secret@localhost:5432/app_db uvicorn openapi_server.main:app --port 8080
```

## Queries (TMF630)

| Kind | Example |
|---|---|
| Attribute filter (any attribute) | `?serviceType=Cloud&state=active` |
| OR via comma | `?state=active,suspended` |
| Dotted path (also through arrays) | `?relatedParty.partyOrPartyRole.name=Peter Meyer` |
| Several attributes of the same array element | `?serviceCharacteristic.name=mac&serviceCharacteristic.value=00:11:22:33:44:55` |
| Through a reference to another service | `?serviceRelationship.service.serviceCharacteristic.name=mac&serviceRelationship.service.serviceCharacteristic.value=00:11:22:33:44:55` |
| Operators | `?startDate.gte=2024-01-01`, `?startDate>=2024-01-01`, `.gt .lt .lte .ne` |
| JSONPath | `?filter=$.serviceCharacteristic[?(@.name=='mac' && @.value=='00:11:22:33:44:55')]` |
| Projection | `?fields=name,state` (`id`, `href`, `@type` are always included) |
| Pagination | `?offset=200&limit=100` (default 100, max. 1000); headers `X-Total-Count`, `X-Result-Count`; `206` for partial results |

JSONPath supports `.a`, `['a']`, `[*]`, `[?( … )]` with `== != < <= > >=`, `&&`, `||`, `!`,
existence (`[?(@.endDate)]`) and string/number/boolean/`null`.
Filters inside an array are evaluated **per element** (`name` and `value` must belong to the same characteristic).
The same applies to attribute filters: parameters sharing a path prefix are combined into one per-element filter
(`$.serviceCharacteristic[*] ? (@.name == "mac" && @.value == "…")`). Repeating the *same* parameter
(`serviceCharacteristic.name=mac&serviceCharacteristic.name=vlan`) is a separate condition: both elements must exist.

### Searching through relationships

A path that continues through `serviceRelationship[].service` or `supportingService[]` addresses the
**referenced service** (TMF638 `ServiceRefOrValue`). Example: find all services A that depend on a service B with
this MAC address:

```
?serviceRelationship.relationshipType=DependentOn
&serviceRelationship.service.serviceCharacteristic.name=mac
&serviceRelationship.service.serviceCharacteristic.value=00:11:22:33:44:55
# equivalent:
?filter=$.serviceRelationship[?(@.service.serviceCharacteristic[?(@.name=='mac' && @.value=='00:11:22:33:44:55')])]
```

* A matches if B matches **by reference** (`service.id`) or **embedded by value**.
* `relationshipType` and the condition on B apply to the **same** relationship.
* Filters on the reference's `id`, `href` and `@referredType` need no join.
* One reference level per condition is supported (A → B, not A → B → C).

SQL: `service.id IN (embedded value matches UNION A JOIN B ON A references B.id WHERE B matches)`, on PostgreSQL as
`= ANY(ARRAY(…))`. B is found via the index, A via the index on the reference id
(PostgreSQL: containment `@> {"serviceRelationship":[{"service":{"id":…}}]}` in the GIN index; Oracle: multivalue index
`ix_svc_rel_id`). Code: `openapi_server/services/query/references.py`.

**Security:** attribute names are checked against `^[A-Za-z_@][A-Za-z0-9_@-]*$`; values never enter the query as SQL text
(PostgreSQL: the whole jsonpath is a bind parameter, values JSON-escaped; Oracle: values as `PASSING` bind variables).
Invalid filters → `400` in the TMF `Error` format.

Code: `openapi_server/services/query/` (`parser.py` → AST → `references.py` → `render.py`), statement construction in `openapi_server/services/service.py`.

## Tests

```bash
pip install -r requirements-dev.txt
pytest tests/pytest/test_query.py                          # parser/renderer, no database
TMF_BASE_URL=http://127.0.0.1:8080 pytest tests/pytest     # + integration tests against the running API
```

The integration tests are backend-neutral and run unchanged against both databases.

**Results:** [docs/test-report.md](docs/test-report.md): all test cases with their result per backend, the test environment
(system, versions, data volume) as well as benchmark and execution plans. Generated by `scripts/test_report.py`
(see section *Reproduce* in the report for the invocation).
The Bruno collection is in `tests/TMFC008` (env `dev`).

## Performance

```bash
DATABASE_URL=postgresql://app:secret@localhost:5432/app_db python scripts/seed.py --count 1000000 --truncate
DATABASE_URL=postgresql+asyncpg://app:secret@localhost:5432/app_db python scripts/bench.py --base-url http://127.0.0.1:8080 --plans
```

`seed.py` loads deterministic, realistic services (~1.3 KB, 5 characteristics including a unique `mac`) via COPY or `executemany`;
`bench.py` measures the latency via the HTTP API and shows the execution plan of the SQL generated by the API.
Current measurements including plans are in the [test report](docs/test-report.md#performance).

Measured with 50,000 services per database (every second one with a `DependentOn` relationship to the previous one) (arm64 devcontainer, both databases local, end-to-end HTTP latency including `X-Total-Count`, 30 runs):

| Query | Matches | PostgreSQL p50 | Oracle p50 | Plan |
|---|---:|---:|---:|---|
| mac via JSONPath (`name && value`) | 1 | 1.9 ms | 1.7 ms | PG: Bitmap Index Scan GIN · Oracle: INDEX RANGE SCAN (MULTI VALUE) |
| mac via attribute filter | 1 | 2.5 ms | 1.5 ms | same |
| mac, no match | 0 | 1.9 ms | 1.6 ms | same |
| A with relationship to B with mac (join) | 1 | 3.4 ms | 2.0 ms | B, A and the embedded branch each via index |
| rare relatedParty name | 10 | 1.9 ms | 1.7 ms | same |
| serviceType + state (~3 %) | 1,713 | 8.4 ms | 20.8 ms | index (PG: both conditions in the GIN index, Oracle: one MVI + filter) |
| range `startDate.gte` | 529 | 118 ms | 48 ms | no index → full scan (mainly for `count(*)`) |
| no filter, page at offset 49,800 | 50,000 | 5.6 ms | 8.4 ms | deferred join via PK index |

Notes:
* Selective equality searches use the index and therefore scale logarithmically instead of linearly.
  A similar level is to be expected for 1 million records; this was not measured here
  because the devcontainer VM has only a 20 GB disk.
* PostgreSQL indexes **every** attribute with one GIN index. Oracle multivalue indexes are per path;
  they are defined in `alembic/versions/7c2e5b1a9f40_add_payload_indexes.py` and need to be added for new search attributes.
  With the full image `gvenzl/oracle-free:23` (including Oracle Text) the migration also creates a JSON search index for arbitrary paths.
* Range and not-equal filters use no JSON index. If needed, an expression index on the specific attribute helps;
  the most expensive part is then the exact `X-Total-Count`.
* Deep pagination: only the ids are sorted and paged first, then the documents are loaded
  (on Oracle with a join hint, because the optimizer doesn't know the page size).
* Relationship join: PostgreSQL estimates every JSON path condition at a flat 1 % of the rows and therefore chose
  parallel seq scans (36 ms). For queries with a join the API disables parallel query via `SET LOCAL` → 3.4 ms.
  On Oracle the multivalue indexes on embedded values (`ix_svc_rel_*`) brought 51 ms down to 2 ms.

## Remarks

* `cryptography` is pinned to 46.0.3: version 50.0.2 (a dependency of `oracledb`) aborted with *Illegal instruction* on the arm64 host.
* The Oracle image `23-slim` contains no Oracle Text (no `SEARCH INDEX`), but is considerably smaller than the full image.
