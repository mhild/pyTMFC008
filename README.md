# pyTMFC008 – TMF638 Service Inventory auf JSON-Spalten (PostgreSQL & Oracle)

PoC der TM Forum Komponente *Service Inventory* (TMFC008) mit TMF638-v5-API (FastAPI).
Jeder Service wird als **ein JSON-Dokument in einer Spalte** gespeichert; CRUD und
TMF630-Query-Parameter werden direkt auf die JSON-Operatoren der Datenbank abgebildet:

| | PostgreSQL 16 | Oracle 23ai Free |
|---|---|---|
| Spaltentyp | `JSONB` | `JSON` (nativ, OSON-Binärformat) |
| Filter | `payload @? CAST(:p AS jsonpath)` | `JSON_EXISTS(payload, '<path>' PASSING :v0 AS "v0")` |
| Index | 1 × GIN `jsonb_path_ops` (deckt jedes Attribut ab) | Multivalue-Indizes je Suchpfad (+ JSON Search Index, falls Oracle Text installiert) |

## Starten

```bash
docker compose up -d db oracle            # Oracle braucht beim ersten Start 1–2 min
docker compose up -d --build app          # Backend gemäß DATABASE_URL in .env (Default: PostgreSQL)
DATABASE_URL='oracle+oracledb_async://app:secret@oracle:1521/?service_name=FREEPDB1' \
  docker compose up -d --build app        # dieselbe App gegen Oracle
```

Der Entrypoint wartet auf die DB (`scripts/wait_for_db.py`) und führt `alembic upgrade head` aus.
API: http://127.0.0.1:8080/service, OpenAPI-UI: http://127.0.0.1:8080/docs

Lokal ohne Container (DBs aus compose, Ports 5432/1521):

```bash
DATABASE_URL=postgresql+asyncpg://app:secret@localhost:5432/app_db alembic upgrade head
DATABASE_URL=postgresql+asyncpg://app:secret@localhost:5432/app_db uvicorn openapi_server.main:app --port 8080
```

## Abfragen (TMF630)

| Art | Beispiel |
|---|---|
| Attributfilter (beliebiges Attribut) | `?serviceType=Cloud&state=active` |
| ODER per Komma | `?state=active,suspended` |
| Punkt-Pfad (auch durch Arrays) | `?relatedParty.partyOrPartyRole.name=Peter Meyer` |
| mehrere Attribute desselben Array-Elements | `?serviceCharacteristic.name=mac&serviceCharacteristic.value=00:11:22:33:44:55` |
| über eine Referenz auf einen anderen Service | `?serviceRelationship.service.serviceCharacteristic.name=mac&serviceRelationship.service.serviceCharacteristic.value=00:11:22:33:44:55` |
| Operatoren | `?startDate.gte=2024-01-01`, `?startDate>=2024-01-01`, `.gt .lt .lte .ne` |
| JSONPath | `?filter=$.serviceCharacteristic[?(@.name=='mac' && @.value=='00:11:22:33:44:55')]` |
| Projektion | `?fields=name,state` (`id`, `href`, `@type` immer enthalten) |
| Pagination | `?offset=200&limit=100` (Default 100, max. 1000); Header `X-Total-Count`, `X-Result-Count`; `206` bei Teilergebnis |

JSONPath unterstützt `.a`, `['a']`, `[*]`, `[?( … )]` mit `== != < <= > >=`, `&&`, `||`, `!`,
Existenz (`[?(@.endDate)]`) sowie String/Zahl/Boolean/`null`.
Filter innerhalb eines Arrays werden **pro Element** ausgewertet (`name` und `value` müssen zum selben Characteristic gehören).
Für Attributfilter gilt dasselbe: Parameter mit gemeinsamem Pfad-Präfix werden zu einem Filter pro Element zusammengefasst
(`$.serviceCharacteristic[*] ? (@.name == "mac" && @.value == "…")`). Wird *derselbe* Parameter wiederholt
(`serviceCharacteristic.name=mac&serviceCharacteristic.name=vlan`), ist das eine eigene Bedingung: Beide Elemente müssen existieren.

### Suche über Relationships

Ein Pfad, der durch `serviceRelationship[].service` oder `supportingService[]` hindurch weitergeht, adressiert den
**referenzierten Service** (TMF638 `ServiceRefOrValue`). Beispiel: Finde alle Services A, die von einem Service B mit
dieser MAC-Adresse abhängen:

```
?serviceRelationship.relationshipType=DependentOn
&serviceRelationship.service.serviceCharacteristic.name=mac
&serviceRelationship.service.serviceCharacteristic.value=00:11:22:33:44:55
# gleichwertig:
?filter=$.serviceRelationship[?(@.service.serviceCharacteristic[?(@.name=='mac' && @.value=='00:11:22:33:44:55')])]
```

* Gefunden wird A, wenn B **per Referenz** (`service.id`) oder **eingebettet als Wert** passt.
* `relationshipType` und die B-Bedingung gelten für **dieselbe** Relationship.
* Filter auf `id`, `href` und `@referredType` der Referenz brauchen keinen Join.
* Unterstützt wird eine Referenzebene pro Bedingung (A → B, nicht A → B → C).

SQL: `service.id IN (eingebettet passt UNION A JOIN B ON A referenziert B.id WHERE B passt)`, bei PostgreSQL als
`= ANY(ARRAY(…))`. B wird über den Index gefunden, A über den Index auf der Referenz-ID
(PostgreSQL: Containment `@> {"serviceRelationship":[{"service":{"id":…}}]}` im GIN-Index; Oracle: Multivalue-Index
`ix_svc_rel_id`). Code: `openapi_server/services/query/references.py`.

**Sicherheit:** Attributnamen werden gegen `^[A-Za-z_@][A-Za-z0-9_@-]*$` geprüft; Werte gehen nie als SQL-Text in die Abfrage
(PostgreSQL: gesamter jsonpath als Bind-Parameter, Werte JSON-escaped; Oracle: Werte als `PASSING`-Bind-Variablen).
Ungültige Filter → `400` im TMF-`Error`-Format.

Code: `openapi_server/services/query/` (`parser.py` → AST → `references.py` → `render.py`), Statement-Aufbau in `openapi_server/services/service.py`.

## Tests

```bash
pip install -r requirements-dev.txt
pytest tests/pytest/test_query.py                          # Parser/Renderer, ohne DB
TMF_BASE_URL=http://127.0.0.1:8080 pytest tests/pytest     # + Integrationstests gegen die laufende API
```

Die Integrationstests sind backend-neutral und laufen unverändert gegen beide Datenbanken.

**Ergebnisse:** [docs/test-report.md](docs/test-report.md): alle Testfälle mit Ergebnis je Backend, Testumgebung
(System, Versionen, Datenbestand) sowie Benchmark und Ausführungspläne. Erzeugt mit `scripts/test_report.py`
(Aufruf siehe Abschnitt *Reproduzieren* im Bericht).
Die Bruno-Collection liegt unter `tests/TMFC008` (Env `dev`).

## Performance

```bash
DATABASE_URL=postgresql://app:secret@localhost:5432/app_db python scripts/seed.py --count 1000000 --truncate
DATABASE_URL=postgresql+asyncpg://app:secret@localhost:5432/app_db python scripts/bench.py --base-url http://127.0.0.1:8080 --plans
```

`seed.py` lädt deterministische, realistische Services (~1,3 KB, 5 Characteristics inkl. eindeutiger `mac`) per COPY bzw. `executemany`;
`bench.py` misst die Latenz über die HTTP-API und zeigt den Ausführungsplan des von der API erzeugten SQL.
Die aktuellen Messwerte inkl. Plänen stehen im [Testbericht](docs/test-report.md#performance).

Messung mit 50 000 Services je DB (jeder zweite mit `DependentOn`-Relationship auf den vorherigen) (arm64-Devcontainer, beide DBs lokal, Latenz HTTP end-to-end inkl. `X-Total-Count`, 30 Läufe):

| Abfrage | Treffer | PostgreSQL p50 | Oracle p50 | Plan |
|---|---:|---:|---:|---|
| mac per JSONPath (`name && value`) | 1 | 1,9 ms | 1,7 ms | PG: Bitmap Index Scan GIN · Oracle: INDEX RANGE SCAN (MULTI VALUE) |
| mac per Attributfilter | 1 | 2,5 ms | 1,5 ms | dto. |
| mac, kein Treffer | 0 | 1,9 ms | 1,6 ms | dto. |
| A mit Relationship zu B mit mac (Join) | 1 | 3,4 ms | 2,0 ms | B, A und eingebetteter Zweig jeweils über Index |
| seltener relatedParty-Name | 10 | 1,9 ms | 1,7 ms | dto. |
| serviceType + state (~3 %) | 1 713 | 8,4 ms | 20,8 ms | Index (PG: beide Bedingungen im GIN, Oracle: ein MVI + Filter) |
| Bereich `startDate.gte` | 529 | 118 ms | 48 ms | kein Index → Full Scan (v. a. für `count(*)`) |
| ohne Filter, Seite bei Offset 49 800 | 50 000 | 5,6 ms | 8,4 ms | Deferred Join über PK-Index |

Einordnung:
* Selektive Gleichheitssuchen laufen über den Index und skalieren damit logarithmisch statt linear.
  Für 1 Mio. Datensätze ist ein ähnliches Niveau zu erwarten; nachgemessen wurde das hier nicht,
  weil die Devcontainer-VM nur 20 GB Platte hat.
* PostgreSQL indexiert mit einem GIN-Index **jedes** Attribut. Oracle-Multivalue-Indizes gelten pro Pfad;
  sie sind in `alembic/versions/7c2e5b1a9f40_add_payload_indexes.py` definiert und für neue Suchattribute zu ergänzen.
  Mit dem vollen Image `gvenzl/oracle-free:23` (inkl. Oracle Text) legt die Migration zusätzlich einen JSON Search Index für beliebige Pfade an.
* Bereichs- und Ungleich-Filter nutzen keinen JSON-Index. Bei Bedarf hilft ein Ausdrucksindex auf das konkrete Attribut;
  die teuerste Komponente ist dann der exakte `X-Total-Count`.
* Tiefe Pagination: Erst werden nur die IDs sortiert und geblättert, danach die Dokumente geladen
  (bei Oracle mit Join-Hint, weil der Optimizer die Seitengröße nicht kennt).
* Relationship-Join: PostgreSQL schätzt jede JSON-Pfad-Bedingung pauschal auf 1 % der Zeilen und wählte deshalb
  Parallel Seq Scans (36 ms). Für Abfragen mit Join schaltet die API Parallel Query per `SET LOCAL` ab → 3,4 ms.
  Bei Oracle machten die Multivalue-Indizes auf eingebettete Werte (`ix_svc_rel_*`) aus 51 ms → 2 ms.

## Hinweise

* `cryptography` ist auf 46.0.3 gepinnt: Version 50.0.2 (Abhängigkeit von `oracledb`) brach auf dem arm64-Host mit *Illegal instruction* ab.
* Das Oracle-Image `23-slim` enthält kein Oracle Text (kein `SEARCH INDEX`), ist dafür deutlich kleiner als das volle Image.
