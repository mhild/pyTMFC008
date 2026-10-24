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

The API works with any PostgreSQL 16 or Oracle 23ai database; the backend is chosen solely by `DATABASE_URL`.
The databases in `docker-compose.yml` are a convenience for when none is at hand – each one belongs to a compose
profile and only starts when asked for.

**With a database of the stack** (hostnames are the compose service names):

```bash
docker compose --profile postgres up -d --build        # app + PostgreSQL (DATABASE_URL from .env, the default)
```
```bash
DATABASE_URL='oracle+oracledb_async://app:secret@oracle:1521/?service_name=FREEPDB1' \
  docker compose --profile oracle up -d --build         # app + Oracle (needs 1–2 min on first start)
```

**With an external database** – no database container is started:

```bash
DATABASE_URL='oracle+oracledb_async://app:secret@dbhost:1521/?service_name=FREEPDB1' docker compose up -d --build app
DATABASE_URL='postgresql+asyncpg://app:secret@dbhost:5432/app_db'                    docker compose up -d --build app
```

Docker Compose takes a variable set in the shell over the value in `.env`; alternatively edit the `DATABASE_URL`
line there. The host must be reachable from the container. There is only one `app` container: starting it with a
different `DATABASE_URL` recreates it against the other database. From the host, the databases of the stack are
reached at `localhost` (see below). Starting the services by name (`docker compose up -d db oracle`) works too and
ignores the profiles.

Requirements for an external database:

* The user owns the schema and may create tables, indexes and (Oracle) triggers; on Oracle also
  `EXECUTE ON DBMS_STATS` for the statistics the migrations gather. The app runs `alembic upgrade head` on start.
* Oracle: 23ai or later (native `JSON` type, multivalue indexes). On a large table (1M rows) the migrations
  that fill the shadow column `search` run in batches on separate connections, because the PGA of a single session
  would exceed `PGA_AGGREGATE_LIMIT` on Oracle Free.
* The Oracle index and column migrations are not transactional; after a failed one, clean up by hand before retrying.

The entrypoint waits for the database (`scripts/wait_for_db.py`) and runs `alembic upgrade head`.
API: http://127.0.0.1:8080/service, OpenAPI UI: http://127.0.0.1:8080/docs

Locally without a container (databases from compose on ports 5432/1521, or any other host in the URL):

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
| Sorting | `?sort=-startDate,name` (`-` descending, `+` or nothing ascending; dotted paths allowed) |
| Pagination | `?offset=200&limit=100` (default 100, max. 1000); headers `X-Total-Count`, `X-Result-Count`; `206` for partial results |

JSONPath supports `.a`, `['a']`, `[*]`, `[?( … )]` with `== != < <= > >=`, `&&`, `||`, `!`,
existence (`[?(@.endDate)]`) and string/number/boolean/`null`.
Filters inside an array are evaluated **per element** (`name` and `value` must belong to the same characteristic).
The same applies to attribute filters: parameters sharing a path prefix are combined into one per-element filter
(`$.serviceCharacteristic[*] ? (@.name == "mac" && @.value == "…")`). Repeating the *same* parameter
(`serviceCharacteristic.name=mac&serviceCharacteristic.name=vlan`) is a separate condition: both elements must exist.

### Sorting

Each sort attribute orders JSON numbers numerically first, then all scalar values as text in byte order
(ISO dates therefore sort chronologically). Missing and non-scalar values come last in both directions; the
service id breaks ties, so pagination is stable. Both backends return the same order. Sorting through arrays
(`sort=serviceCharacteristic.value`) is undefined. Sorting is not index-backed: all matches are sorted
(unfiltered over 50,000 services: ~35 ms on PostgreSQL, ~120 ms on Oracle) – fine for filtered queries, slow on
large unfiltered sets.

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

## Validation

`POST` validates the body against `Service_FVO`, `PATCH` validates the *patched document* against `Service`, both
taken from the OpenAPI spec in `api_specs/` (`openapi_server/services/validation.py`). Invalid documents are rejected
with `400`, e.g. `Invalid Service_FVO: $.state: 'running' is not one of [...]`. This covers required attributes
(`state` and `serviceSpecification` on create, `@type` always), enums, types and `date-time` formats. If `@type` is
missing on create it defaults to `Service`. The spec's `oneOf` + `discriminator` constructs are checked by `@type`
(e.g. `partyOrPartyRole` must be a `PartyRef` or `PartyRoleRef` with the attributes required for it).

PATCH supports `application/merge-patch+json` (also `application/json`) and `application/json-patch+json`;
`application/json-patch-query+json` is not supported (`415`). Invalid or unknown ids return `404`.

## Events

Clients subscribe with `POST /hub` (`{"callback": "http://client/api", "query": "..."}`, `GET`/`DELETE /hub/{id}`).
After a change is committed, the API sends the events to `<callback>/listener/<eventType>`, e.g.
`http://client/api/listener/serviceStateChangeEvent`:

| Operation | Events |
|---|---|
| `POST /service` | `ServiceCreateEvent` |
| `PATCH /service/{id}` | `ServiceStateChangeEvent` if `state` changed, `ServiceOperatingStatusChangeEvent` if `operatingStatus` changed, `ServiceAttributeValueChangeEvent` if any other attribute changed |
| `DELETE /service/{id}` | `ServiceDeleteEvent` with the last state of the service |

The optional `query` selects events: `eventType=ServiceStateChangeEvent,ServiceDeleteEvent&event.service.state=active`
(all terms must match, comma = OR, dotted paths into the event, arrays are searched element-wise).
Delivery is best effort: one attempt per hub after the response, failures are logged (code: `openapi_server/services/events.py`).
A production setup would need a transactional outbox with retries so no event is lost on a crash or an unreachable listener.

## Revision history

With `HISTORY_ENABLED=true` (`.env`, default `false`) every write on the inventory keeps the version that was current
until then: `PATCH` archives the old document and makes the patched one the next revision (a patch that changes
nothing creates none), `DELETE` archives the last document, `POST` starts at revision 1. The earlier revisions live in
the table `service_history` (the same indexes as `service` on the service's own attributes; on Oracle also the `search`
column and trigger); `service` itself, and with it every query of current versions, is untouched. The current
version never carries revision attributes; a historised revision is returned with a separate `revision` object:

```json
{ "id": "…", "name": "vCPE", "state": "active", "revision": { "id": 2, "startTimestamp": "2026-10-24T10:54:00.123456Z", "endTimestamp": "2026-10-24T11:20:31.004211Z" } }
```

| Request | Result |
|---|---|
| `GET /service?includeHistory=true&…` | all filters, sorting, paging and `fields` apply to the current **and** the historised revisions; every revision is one entry (`X-Total-Count` counts revisions), ordered by `id`, oldest revision first, the current one last. Default `includeHistory=false`: current versions only |
| `…&revisionStartTimestamp=T1&revisionEndTimestamp=T2` | only revisions that were valid at some time within `[T1, T2]` (ISO 8601, UTC without offset); either bound may be omitted. Without `includeHistory=true`: `400` |
| `GET /service/{id}?includeHistory=true&revision=N` | exactly this revision (the current one without `revision` object); `revision` is required then (`400`), a revision that doesn't exist: `404`; also for deleted services |
| `includeHistory=true` with `HISTORY_ENABLED=false` | `400` |

Limits: filters through references (`serviceRelationship.service.…`) are not supported together with
`includeHistory=true` (`400`); a reference always resolves to the *current* version of the referenced service.
History should be enabled from the start: services that have not been changed since the activation have no revision
number yet, so their first change archives the old version as revision 1 *without* `startTimestamp` (start unknown)
and the new one becomes revision 2. Changes made while history was off are not recorded. Services written directly into
the database (`scripts/seed.py`) bypass the history. Hub subscriptions are not historised. Code: `openapi_server/services/history.py`.

## Tests

```bash
python -m venv .venv && . .venv/bin/activate      # recommended outside the devcontainer
pip install -r requirements-dev.txt                 # app requirements + pytest
pytest tests/pytest/test_query.py                          # parser/renderer, no database
TMF_BASE_URL=http://127.0.0.1:8080 pytest tests/pytest     # + integration tests against the running API
```

`tests/pytest/test_events.py` starts an HTTP listener the API has to call back. It registers its callback under
`TMF_CALLBACK_HOST` (default `127.0.0.1`, i.e. the API runs on the host); for the API in the Docker container use
`TMF_CALLBACK_HOST=host.docker.internal` (Linux: add `extra_hosts: ["host.docker.internal:host-gateway"]` to the `app` service).

The integration tests are backend-neutral and run unchanged against both databases. The history tests
(`test_history.py`) need an API started with `HISTORY_ENABLED=true` and are skipped otherwise.

**Results:** [docs/test-report.md](docs/test-report.md): all test cases with their result per backend, the test environment
(system, versions, data volume) as well as benchmark and execution plans. Generated by `scripts/test_report.py`
(see section *Reproduce* in the report for the invocation).
The Bruno collection is in `tests/TMFC008` (env `dev`). The official TM Forum conformance test kit runs with `ctk/run-api-ctk.sh` (see [ctk/README.md](ctk/README.md)); the API passes all 37 of its tests.

## Performance

A benchmark run has two steps per backend: load test data directly into the database (`seed.py`), then send the
query suite to an API **running against that same database** (`bench.py`). Both scripts are run from the host,
so the database URLs use `localhost`.

**PostgreSQL** (app started with the default `.env`, see [Getting started](#getting-started)):

```bash
export PG=postgresql+asyncpg://app:secret@localhost:5432/app_db
DATABASE_URL=$PG alembic upgrade head     # creates table and indexes; already done if the app ran against PostgreSQL
DATABASE_URL=$PG python scripts/seed.py --count 1000000 --truncate
DATABASE_URL=$PG python scripts/bench.py --base-url http://127.0.0.1:8080 --plans
```

**Oracle** (app started with the Oracle `DATABASE_URL`, see [Getting started](#getting-started)):

```bash
export ORA='oracle+oracledb_async://app:secret@localhost:1521/?service_name=FREEPDB1'
DATABASE_URL=$ORA alembic upgrade head    # creates table and indexes; already done if the app ran against Oracle
DATABASE_URL=$ORA python scripts/seed.py --count 1000000 --truncate
DATABASE_URL=$ORA python scripts/bench.py --base-url http://127.0.0.1:8080 --plans
```

* The app container only migrates the database it is started against. Running `alembic upgrade head` again is
  harmless, so run it whenever in doubt – `seed.py` stops with a hint if the table is missing.
* `--truncate` deletes all services first; without it, `--start <n>` appends further services.
  1 million services need several GB per database (PostgreSQL including WAL) – check the free disk space first.
* `bench.py` takes the number of services from the API's `X-Total-Count` and derives the searched MAC addresses
  and names from it, so it needs data loaded by `seed.py`. `DATABASE_URL` is only used for `--plans` (`EXPLAIN` of the
  SQL the API generates); it must point to the database the API at `--base-url` uses, otherwise the plans belong to
  the other backend. Other options: `--runs` (requests per query, default 20), `--count`.
* Without Docker for the app, start it locally against Oracle with
  `DATABASE_URL=$ORA uvicorn openapi_server.main:app --port 8080`.
* Both backends at once, including all tests and a Markdown report: `scripts/test_report.py` (see the
  *Reproduce* section of the [test report](docs/test-report.md#reproduce)).

`seed.py` loads deterministic, realistic services (~1.3 KB, 5 characteristics including a unique `mac`) via COPY or `executemany`;
`bench.py` measures the latency via the HTTP API and shows the execution plan of the SQL generated by the API.
Current measurements including plans are in the [test report](docs/test-report.md#performance).

Measured with 50,000 services on PostgreSQL (local) and **1,000,000 services on Oracle** (external database; every second service has a `DependentOn` relationship to the previous one). arm64 devcontainer, end-to-end HTTP latency including `X-Total-Count`, 30 runs; details and execution plans in [docs/test-report.md](docs/test-report.md):

| Query | PostgreSQL p50 (50k) | Oracle p50 (1M) | Plan |
|---|---:|---:|---|
| mac via JSONPath (`name && value`) | 1.9 ms | 26 ms | PG: Bitmap Index Scan GIN · Oracle: INDEX RANGE SCAN (MULTI VALUE) |
| mac via attribute filter | 1.7 ms | 25 ms | same |
| mac, no match | 1.7 ms | 25 ms | same |
| A with relationship to B with mac (join) | 3.3 ms | 26 ms | B, A and the embedded branch each via index |
| rare relatedParty name | 1.7 ms | 28 ms | same |
| serviceType + state (~3 %) | 6.9 ms (1,713 matches) | 3.5 s (33,241 matches) | index (PG: both conditions in the GIN index, Oracle: one MVI + filter); the time is the page plus `count(*)` over all matches |
| serviceType + state of the referenced service (~3 %) | 1.5 s (857 matches) | 7.9 s (16,570 matches) | the referenced services are collected once (index), then joined to the candidates |
| range `startDate.gte` | 129 ms (529 matches) | 1.8 s (10,890 matches) | no index → full scan (mainly for `count(*)`) |
| no filter, page at the end | 6.2 ms | 294 ms | deferred join via PK index |

Notes:
* Selective equality searches use the index and therefore scale logarithmically instead of linearly.
  On Oracle with 1 million services they still answer in ~30 ms; PostgreSQL was measured with 50,000 services only
  (the devcontainer VM has a small disk).
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
* **Object-valued characteristics on Oracle:** multivalue indexes must be created with `ERROR ON ERROR`, so an index on
  `serviceCharacteristic.value` would reject every service with an `ObjectCharacteristic` (`ORA-40456`). The
  characteristic value indexes (`ix_service_char_value`, `ix_svc_rel_char_value`, `ix_svc_sup_char_value`) are therefore
  built on a shadow column `search` that a trigger fills with the characteristic names and values without objects
  (migration `c5d7e9f1a2b4`, ~15 % extra storage). A filter that only compares characteristic names/values with
  constants is checked on both columns – `search` for the index, `payload` for the exact result; filters into object
  values (`serviceCharacteristic.value.vCPE_IP=…`), `exists` and negations use `payload` only (no value index).
  PostgreSQL needs none of this: the GIN index accepts any value.
