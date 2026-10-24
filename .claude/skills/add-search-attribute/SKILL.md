---
name: add-search-attribute
description: Make a new service attribute (JSON path) efficiently searchable on both backends – Oracle multivalue index migration, tests, benchmark query and plan check. Use when a filter on a new attribute is needed or a filter turns out to scan the whole table.
---

# Add an index-backed search attribute

Filtering already works on **any** attribute (TMF630 attribute filters and `filter=` JSONPath); this is about
making it **fast**.

* **PostgreSQL:** nothing to do for equality filters – the GIN index (`jsonb_path_ops`) covers every path.
  Range filters (`.gte`, `.lt`, …) and `.ne` use no JSON index on either backend; they need an expression index
  on the specific attribute, which the generated `@?`/`JSON_EXISTS` SQL can't use as is – discuss with the user
  before going down that road.
* **Oracle:** multivalue indexes are per path. Without one, `JSON_EXISTS` on the new path is a full table scan.

## Steps

1. **Path:** dot notation without array markers, e.g. `feature.featureCharacteristic.value` (arrays on the way
   are handled by the multivalue index). Check the TMF638 model in `openapi_server/models/` for the exact name.
2. **New Alembic revision** – never edit a migration that has already been applied:
   ```bash
   alembic heads                        # current head = down_revision of the new one
   alembic revision -m "add_<attribute>_index"
   ```
   Follow `alembic/versions/a4f1c3d2e8b7_add_reference_indexes.py`: Oracle only (`op.get_bind().dialect.name`),
   `CREATE MULTIVALUE INDEX ix_service_<short> ON service s (s.payload.<path>.string())`, and a matching `DROP INDEX`
   in `downgrade()`.
   * If the attribute should also be searchable **through references** (`serviceRelationship.service.<path>`,
     `supportingService.<path>`), add the same index for those prefixes (`ix_svc_rel_<short>`, `ix_svc_sup_<short>`) –
     otherwise the "embedded by value" branch of a reference filter scans the table.
   * With revision history (`service_history`, `includeHistory=true`) the attribute is searched there too: add the
     same index on `service_history h (h.payload.<path>.string())` (`ix_hist_<short>`, see
     `alembic/versions/e9b3d5f7a1c2_add_service_history.py`; not needed for the reference prefixes, history search
     doesn't support filters through references) and check the plan with `includeHistory=true`.
   * Every value on the path must be scalar (or an array of scalars): Oracle requires `ERROR ON ERROR` for multivalue
     indexes, so a single object value makes the insert fail (`ORA-40456`). For paths that can hold objects (like
     characteristic values) copy them without objects into the `search` shadow column instead – see
     `alembic/versions/c5d7e9f1a2b4_add_oracle_search_column.py` (trigger + backfill) and `uses_search_column()` in
     `openapi_server/services/query/render.py`, which decides which conditions are also checked on `search`.
   * `.string()` indexes string values. For numeric attributes the parser also compares against the number
     (`_value_alternatives`), so check in the plan whether a `.number()` index is needed as well.
3. **Integration test** in `tests/pytest/test_api.py` (or `test_relationships.py` for reference paths): create services
   with the attribute using the module's `run_id` marker, filter on it, assert exactly the expected ids. Also assert a
   non-match from a different array element if the path goes through an array.
4. **Benchmark query:** add an entry to `queries()` in `scripts/bench.py`; if the seeded data lacks the attribute,
   extend `scripts/datagen.py` (keep it deterministic) and reseed.
5. **Verify** with the `dual-backend-check` skill, then the plan:
   ```bash
   DATABASE_URL=$ORA python scripts/bench.py --base-url http://127.0.0.1:8002 --plans
   ```
   Oracle must show `INDEX RANGE SCAN (MULTI VALUE)` on the new index; PostgreSQL `Bitmap Index Scan` on
   `ix_service_payload_gin`.
6. **Docs:** add the attribute to the index list in `README.md` if relevant and regenerate the report
   (`test-report` skill).
