# Test report

Generated on 2026-10-24 19:08 UTC by `scripts/test_report.py`. To regenerate, see [Reproduce](#reproduce).

## Result

| Backend | API | Result |
|---|---|---|
| PostgreSQL | `http://127.0.0.1:8001` | 174 passed, 6 skipped in 4.37s |
| Oracle | `http://127.0.0.1:8002` | 174 passed, 6 skipped in 4.15s |

Bruno collection (`demo`):

| Backend | Result |
|---|---|
| PostgreSQL | 61 passed, 0 failed, 4 skipped (65 requests, 64 checks) |
| Oracle | 61 passed, 0 failed, 4 skipped (65 requests, 64 checks) |

## Test environment

| | |
|---|---|
| Code version | `main` @ `8ca3ae2` |
| Operating system | Debian GNU/Linux 13 (trixie) (Kernel 6.12.13-200.fc41.aarch64, aarch64) |
| CPU | Apple (aarch64, model name not exposed to the VM), 4 CPUs |
| Memory | 7.7 GiB |
| Python | 3.12.15 (CPython) |
| Bruno CLI | 4.3.0 |
| Database PostgreSQL | PostgreSQL 16.15 on aarch64-unknown-linux-musl, compiled by gcc (Alpine 15.2.0) 15.2.0, 64-bit – 50,003 services in table |
| Database Oracle | Oracle AI Database 26ai Free Release 23.26.3.0.0 - Develop, Learn, and Run for Free Version 23.26.3.0.0 – 50,000 services in table |
| Container | `gvenzl/oracle-free:23-slim` (Up 9 hours (healthy)) |
| Container | `postgres:16-alpine` (Up 4 hours (healthy)) |
| Packages | fastapi 0.136.0, uvicorn 0.44.0, pydantic 2.13.3, SQLAlchemy 2.0.49, alembic 1.18.4, asyncpg 0.31.0, oracledb 26.0.1, cryptography 46.0.3, httpx 0.28.1, pytest 9.1.1 |

For each test run the API ran as a separate uvicorn instance (one worker, `HISTORY_ENABLED=true`: the history tests are skipped without it) on the same host as the tests.

## Test cases

| Level | Tests | What runs |
|---|---:|---|
| API | 81 | HTTP request via httpx → FastAPI → SQLAlchemy → database (end-to-end against the running API) |
| Unit | 99 | parser and SQL renderers only – no API, no database (run once per backend nevertheless) |

### `test_api.py`

```text
Integration tests against a running TMF638 API (TMF_BASE_URL); backend-agnostic.

Every run uses a unique marker so the tests also work on a pre-filled database.
```

| Test | Level | Description | PostgreSQL | Oracle |
|---|---|---|---|---|
| `test_create_returns_resource` | API | create returns resource | ✅ passed (35 ms) | ✅ passed (69 ms) |
| `test_retrieve` | API | retrieve | ✅ passed (2 ms) | ✅ passed (3 ms) |
| `test_retrieve_with_fields` | API | retrieve with fields | ✅ passed (1 ms) | ✅ passed (1 ms) |
| `test_retrieve_unknown_and_invalid_id` | API | retrieve unknown and invalid id | ✅ passed (1 ms) | ✅ passed (2 ms) |
| `test_attribute_filter` | API | attribute filter | ✅ passed (7 ms) | ✅ passed (27 ms) |
| `test_attribute_filter_dotted_path` | API | attribute filter dotted path | ✅ passed (2 ms) | ✅ passed (10 ms) |
| `test_attribute_filter_number` | API | attribute filter number | ✅ passed (2 ms) | ✅ passed (9 ms) |
| `test_attribute_filter_operators` | API | attribute filter operators | ✅ passed (5 ms) | ✅ passed (22 ms) |
| `test_jsonpath_filter_characteristic` | API | The search the PoC is about: characteristic name AND value in the same array element. | ✅ passed (2 ms) | ✅ passed (8 ms) |
| `test_jsonpath_filter_does_not_mix_array_elements` | API | jsonpath filter does not mix array elements | ✅ passed (2 ms) | ✅ passed (2 ms) |
| `test_jsonpath_filter_related_party` | API | jsonpath filter related party | ✅ passed (2 ms) | ✅ passed (8 ms) |
| `test_quotes_in_values_are_data_not_syntax` | API | quotes in values are data not syntax | ✅ passed (3 ms) | ✅ passed (14 ms) |
| `test_invalid_filter_is_bad_request` | API | invalid filter is bad request | ✅ passed (1 ms) | ✅ passed (1 ms) |
| `test_list_fields` | API | list fields | ✅ passed (2 ms) | ✅ passed (2 ms) |
| `test_pagination` | API | pagination | ✅ passed (3 ms) | ✅ passed (10 ms) |
| `test_merge_patch` | API | merge patch | ✅ passed (6 ms) | ✅ passed (15 ms) |
| `test_json_patch` | API | json patch | ✅ passed (3 ms) | ✅ passed (5 ms) |
| `test_patch_cannot_change_id` | API | patch cannot change id | ✅ passed (2 ms) | ✅ passed (2 ms) |
| `test_patch_errors` | API | patch errors | ✅ passed (2 ms) | ✅ passed (4 ms) |
| `test_delete` | API | delete | ✅ passed (6 ms) | ✅ passed (11 ms) |
| `test_create_rejects_invalid_service[change0-$.state]` | API | create rejects invalid service | ✅ passed (1 ms) | ✅ passed (1 ms) |
| `test_create_rejects_invalid_service[change1-$.startDate]` | API | create rejects invalid service | ✅ passed (1 ms) | ✅ passed (1 ms) |
| `test_create_rejects_invalid_service[change2-$.isStateful]` | API | create rejects invalid service | ✅ passed (1 ms) | ✅ passed (1 ms) |
| `test_create_rejects_invalid_service[change3-'serviceSpecification' is a required property]` | API | create rejects invalid service | ✅ passed (4 ms) | ✅ passed (1 ms) |
| `test_create_rejects_invalid_service[change4-$.relatedParty[0].partyOrPartyRole]` | API | create rejects invalid service | ✅ passed (4 ms) | ✅ passed (1 ms) |
| `test_create_accepts_spec_example` | API | create accepts spec example | ✅ passed (203 ms) | ✅ passed (205 ms) |
| `test_patch_must_keep_the_service_valid` | API | patch must keep the service valid | ✅ passed (5 ms) | ✅ passed (5 ms) |
| `test_scalar_value_next_to_an_object_value` | API | scalar value next to an object value | ✅ passed (9 ms) | ✅ passed (9 ms) |
| `test_scalar_in_an_array_with_objects` | API | scalar in an array with objects | ✅ passed (1 ms) | ✅ passed (9 ms) |
| `test_filter_inside_an_object_value` | API | filter inside an object value | ✅ passed (3 ms) | ✅ passed (17 ms) |
| `test_patch_scalar_value_to_object` | API | patch scalar value to object | ✅ passed (11 ms) | ✅ passed (20 ms) |
| `test_sort_numbers_numerically_missing_values_last` | API | sort numbers numerically missing values last | ✅ passed (14 ms) | ✅ passed (23 ms) |
| `test_sort_by_several_attributes` | API | sort by several attributes | ✅ passed (4 ms) | ✅ passed (14 ms) |
| `test_sort_with_pagination` | API | sort with pagination | ✅ passed (3 ms) | ✅ passed (8 ms) |
| `test_invalid_sort_is_bad_request[na'me]` | API | invalid sort is bad request | ✅ passed (1 ms) | ✅ passed (1 ms) |
| `test_invalid_sort_is_bad_request[a..b]` | API | invalid sort is bad request | ✅ passed (1 ms) | ✅ passed (1 ms) |
| `test_invalid_sort_is_bad_request[-]` | API | invalid sort is bad request | ✅ passed (1 ms) | ✅ passed (1 ms) |
| `test_invalid_sort_is_bad_request[]` | API | invalid sort is bad request | ✅ passed (20 ms) | ✅ passed (31 ms) |

### `test_auth.py`

Authentication / authorization (AUTH_MODE) against a running API; skipped when the API runs without it.

| Test | Level | Description | PostgreSQL | Oracle |
|---|---|---|---|---|
| `test_probes_stay_open` | Unit | probes stay open | ✅ passed (5 ms) | ✅ passed (5 ms) |
| `test_anonymous_is_rejected_with_a_challenge` | Unit | anonymous is rejected with a challenge | ⏭️ skipped (3 ms)<br>API runs without AUTH_MODE | ⏭️ skipped (3 ms)<br>API runs without AUTH_MODE |
| `test_garbage_credentials_are_rejected` | Unit | garbage credentials are rejected | ⏭️ skipped (< 1 ms)<br>API runs without AUTH_MODE | ⏭️ skipped (< 1 ms)<br>API runs without AUTH_MODE |
| `test_writer_may_everything` | API | writer may everything | ⏭️ skipped (< 1 ms)<br>API runs without AUTH_MODE | ⏭️ skipped (< 1 ms)<br>API runs without AUTH_MODE |
| `test_reader_reads_but_does_not_write` | API | reader reads but does not write | ⏭️ skipped (< 1 ms)<br>API runs without AUTH_MODE | ⏭️ skipped (< 1 ms)<br>API runs without AUTH_MODE |
| `test_reader_may_subscribe_to_events` | Unit | reader may subscribe to events | ⏭️ skipped (< 1 ms)<br>API runs without AUTH_MODE | ⏭️ skipped (< 1 ms)<br>API runs without AUTH_MODE |

### `test_events.py`

```text
Event subscriptions (hub) and notifications against a running TMF638 API.

The test starts an HTTP listener; the API must be able to reach it under
TMF_CALLBACK_HOST (default 127.0.0.1 - set e.g. host.docker.internal when the
API runs in a container).
```

| Test | Level | Description | PostgreSQL | Oracle |
|---|---|---|---|---|
| `test_hub_lifecycle` | API | hub lifecycle | ✅ passed (8 ms) | ✅ passed (10 ms) |
| `test_invalid_hub_is_bad_request[body0]` | API | invalid hub is bad request | ✅ passed (1 ms) | ✅ passed (1 ms) |
| `test_invalid_hub_is_bad_request[body1]` | API | invalid hub is bad request | ✅ passed (1 ms) | ✅ passed (1 ms) |
| `test_invalid_hub_is_bad_request[body2]` | API | invalid hub is bad request | ✅ passed (1 ms) | ✅ passed (1 ms) |
| `test_service_lifecycle_events` | API | service lifecycle events | ✅ passed (112 ms) | ✅ passed (120 ms) |
| `test_hub_query_selects_event_types` | API | hub query selects event types | ✅ passed (600 ms) | ✅ passed (596 ms) |
| `test_no_events_after_hub_deletion` | API | no events after hub deletion | ✅ passed (1417 ms) | ✅ passed (1436 ms) |

### `test_health.py`

Liveness and readiness endpoints (operational, not part of TMF638).

| Test | Level | Description | PostgreSQL | Oracle |
|---|---|---|---|---|
| `test_livez` | API | livez | ✅ passed (2 ms) | ✅ passed (4 ms) |
| `test_readyz` | API | readyz | ✅ passed (4 ms) | ✅ passed (4 ms) |
| `test_not_in_the_openapi_document` | API | not in the openapi document | ✅ passed (261 ms) | ✅ passed (260 ms) |

### `test_history.py`

```text
Revision history (HISTORY_ENABLED) against a running API; backend-agnostic.

The tests that need history skip when the API runs without it (the disabled behaviour is tested separately).
```

| Test | Level | Description | PostgreSQL | Oracle |
|---|---|---|---|---|
| `test_disabled_rejects_include_history` | API | disabled rejects include history | ⏭️ skipped (8 ms)<br>API runs with HISTORY_ENABLED | ⏭️ skipped (139 ms)<br>API runs with HISTORY_ENABLED |
| `test_current_version_is_clean` | API | current version is clean | ✅ passed (12 ms) | ✅ passed (18 ms) |
| `test_list_with_history` | API | list with history | ✅ passed (12 ms) | ✅ passed (24 ms) |
| `test_list_without_include_history_is_current_only` | API | list without include history is current only | ✅ passed (12 ms) | ✅ passed (20 ms) |
| `test_filters_apply_to_each_revision` | API | filters apply to each revision | ✅ passed (29 ms) | ✅ passed (41 ms) |
| `test_count_paging_and_sort_include_revisions` | API | count paging and sort include revisions | ✅ passed (89 ms) | ✅ passed (27 ms) |
| `test_fields_keep_the_revision` | API | fields keep the revision | ✅ passed (14 ms) | ✅ passed (16 ms) |
| `test_timestamp_range` | API | timestamp range | ✅ passed (24 ms) | ✅ passed (37 ms) |
| `test_unchanged_patch_creates_no_revision` | API | unchanged patch creates no revision | ✅ passed (15 ms) | ✅ passed (19 ms) |
| `test_retrieve_a_revision` | API | retrieve a revision | ✅ passed (14 ms) | ✅ passed (24 ms) |
| `test_retrieve_a_revision_needs_a_valid_combination[params0-400]` | API | retrieve a revision needs a valid combination | ✅ passed (9 ms) | ✅ passed (16 ms) |
| `test_retrieve_a_revision_needs_a_valid_combination[params1-400]` | API | retrieve a revision needs a valid combination | ✅ passed (9 ms) | ✅ passed (14 ms) |
| `test_retrieve_a_revision_needs_a_valid_combination[params2-400]` | API | retrieve a revision needs a valid combination | ✅ passed (10 ms) | ✅ passed (14 ms) |
| `test_retrieve_a_revision_needs_a_valid_combination[params3-400]` | API | retrieve a revision needs a valid combination | ✅ passed (9 ms) | ✅ passed (13 ms) |
| `test_retrieve_a_revision_needs_a_valid_combination[params4-400]` | API | retrieve a revision needs a valid combination | ✅ passed (9 ms) | ✅ passed (14 ms) |
| `test_retrieve_a_revision_needs_a_valid_combination[params5-400]` | API | retrieve a revision needs a valid combination | ✅ passed (9 ms) | ✅ passed (16 ms) |
| `test_retrieve_a_revision_needs_a_valid_combination[params6-404]` | API | retrieve a revision needs a valid combination | ✅ passed (9 ms) | ✅ passed (17 ms) |
| `test_invalid_list_parameters` | API | invalid list parameters | ✅ passed (2 ms) | ✅ passed (2 ms) |
| `test_delete_keeps_the_revisions` | API | delete keeps the revisions | ✅ passed (11 ms) | ✅ passed (15 ms) |
| `test_new_service_has_no_history_yet` | API | new service has no history yet | ✅ passed (7 ms) | ✅ passed (9 ms) |

### `test_history_unit.py`

Revision history: parameter checks and bookkeeping, no API and no database.

| Test | Level | Description | PostgreSQL | Oracle |
|---|---|---|---|---|
| `test_list_range_without_history_is_none` | Unit | list range without history is none | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_list_range_parses_the_period` | Unit | list range parses the period | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_list_range_rejects[params0]` | Unit | list range rejects | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_list_range_rejects[params1]` | Unit | list range rejects | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_list_range_rejects[params2]` | Unit | list range rejects | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_list_range_rejects[params3]` | Unit | list range rejects | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_include_history_needs_the_setting` | Unit | include history needs the setting | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_by_id_revision` | Unit | by id revision | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_filters_through_references_are_not_supported_on_history` | Unit | filters through references are not supported on history | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_history_statements_cover_both_tables[postgresql]` | Unit | history statements cover both tables | ✅ passed (3 ms) | ✅ passed (3 ms) |
| `test_history_statements_cover_both_tables[oracle]` | Unit | history statements cover both tables | ✅ passed (1 ms) | ✅ passed (1 ms) |
| `test_archive_advances_the_revision` | Unit | archive advances the revision | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_archive_of_a_service_untouched_since_activation` | Unit | No revision yet: its version becomes revision 1 with an unknown start. | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_archive_is_a_no_op_when_disabled` | Unit | archive is a no op when disabled | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_with_revision_separates_the_revision_data` | Unit | with revision separates the revision data | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |

### `test_query.py`

Unit tests for the TMF630 filter parser and SQL/JSON path renderers (no DB needed).

| Test | Level | Description | PostgreSQL | Oracle |
|---|---|---|---|---|
| `test_attribute_filter_pg[params0-$ ? (@."serviceType" == "Cloud")]` | Unit | attribute filter pg | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_attribute_filter_pg[params1-$ ? ((@."state" == "active") \|\| (@."state" == "inactive"))]` | Unit | attribute filter pg | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_attribute_filter_pg[params2-$ ? (@."relatedParty"."partyOrPartyRole"."name" == "Peter Meyer")]` | Unit | attribute filter pg | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_attribute_filter_pg[params3-$ ? (@."startDate" >= "2024-01-01")]` | Unit | attribute filter pg | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_attribute_filter_pg[params4-$ ? (@."startDate" >= "2024-01-01")]` | Unit | attribute filter pg | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_attribute_filter_pg[params5-$ ? (@."state" != "active")]` | Unit | attribute filter pg | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_attribute_filter_pg[params6-$ ? ((@."value" == "300") \|\| (@."value" == 300))]` | Unit | attribute filter pg | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_attribute_filter_pg[params7-$ ? ((@."isEnabled" == "true") \|\| (@."isEnabled" == true))]` | Unit | attribute filter pg | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_attribute_filter_pg[params8-$ ? (@."@type" == "Service")]` | Unit | attribute filter pg | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_jsonpath_filter_pg[$.serviceCharacteristic[?(@.name=='mac' && @.value=='00:11:22:33:44:55')]-$."serviceCharacteristic"[*] ? ((@."name" == "mac") && (@."value" == "00:11:22:33:44:55"))]` | Unit | jsonpath filter pg | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_jsonpath_filter_pg[$.relatedParty[?(@.partyOrPartyRole.name=='Peter Meyer')]-$."relatedParty"[*] ? (@."partyOrPartyRole"."name" == "Peter Meyer")]` | Unit | jsonpath filter pg | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_jsonpath_filter_pg[$.feature[*].featureCharacteristic[?(@.value==true)]-$."feature"[*]."featureCharacteristic"[*] ? (@."value" == true)]` | Unit | jsonpath filter pg | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_jsonpath_filter_pg[$[?(@.state=='a' \|\| !(@.x > 3.5))]-$ ? ((@."state" == "a") \|\| (!(@."x" > 3.5)))]` | Unit | jsonpath filter pg | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_jsonpath_filter_pg[$['@type']-$."@type"]` | Unit | jsonpath filter pg | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_jsonpath_filter_pg[$[?(@.@type=='Service')]-$ ? (@."@type" == "Service")]` | Unit | jsonpath filter pg | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_jsonpath_filter_pg[$[?(@.endDate)]-$ ? (exists(@."endDate"))]` | Unit | jsonpath filter pg | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_jsonpath_filter_pg[$[?(@.name=="a\\"b")]-$ ? (@."name" == "a\\"b")]` | Unit | jsonpath filter pg | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_oracle_uses_bind_variables_for_strings` | Unit | oracle uses bind variables for strings | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_oracle_sql_contains_no_user_strings` | Unit | oracle sql contains no user strings | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_pg_sql_binds_the_whole_path` | Unit | pg sql binds the whole path | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_reserved_params_are_not_filters` | Unit | reserved params are not filters | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_invalid_filters_are_rejected[params0]` | Unit | invalid filters are rejected | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_invalid_filters_are_rejected[params1]` | Unit | invalid filters are rejected | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_invalid_filters_are_rejected[params2]` | Unit | invalid filters are rejected | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_invalid_filters_are_rejected[params3]` | Unit | invalid filters are rejected | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_invalid_filters_are_rejected[params4]` | Unit | invalid filters are rejected | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_invalid_filters_are_rejected[params5]` | Unit | invalid filters are rejected | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_invalid_filters_are_rejected[params6]` | Unit | invalid filters are rejected | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_attribute_filters_grouped_by_prefix[params0-expected0]` | Unit | attribute filters grouped by prefix | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_attribute_filters_grouped_by_prefix[params1-expected1]` | Unit | attribute filters grouped by prefix | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_attribute_filters_grouped_by_prefix[params2-expected2]` | Unit | attribute filters grouped by prefix | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_attribute_filters_grouped_by_prefix[params3-expected3]` | Unit | attribute filters grouped by prefix | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_reference_is_resolved` | Unit | reference is resolved | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_jsonpath_and_attribute_syntax_resolve_alike` | Unit | jsonpath and attribute syntax resolve alike | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_reference_sql_joins_by_id[postgresql]` | Unit | reference sql joins by id | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_reference_sql_joins_by_id[oracle]` | Unit | reference sql joins by id | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_oracle_reference_hash_semi_join_only_with_other_conditions` | Unit | oracle reference hash semi join only with other conditions | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_join_only_when_dereferencing[params0-False]` | Unit | join only when dereferencing | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_join_only_when_dereferencing[params1-False]` | Unit | join only when dereferencing | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_join_only_when_dereferencing[params2-True]` | Unit | join only when dereferencing | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_join_only_when_dereferencing[params3-True]` | Unit | join only when dereferencing | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_join_only_when_dereferencing[params4-False]` | Unit | join only when dereferencing | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_nested_references_are_rejected` | Unit | nested references are rejected | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_parse_sort[values0-expected0]` | Unit | parse sort | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_parse_sort[values1-expected1]` | Unit | parse sort | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_parse_sort[values2-expected2]` | Unit | parse sort | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_parse_sort[values3-expected3]` | Unit | parse sort | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_invalid_sort_is_rejected[]` | Unit | invalid sort is rejected | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_invalid_sort_is_rejected[-]` | Unit | invalid sort is rejected | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_invalid_sort_is_rejected[a..b]` | Unit | invalid sort is rejected | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_invalid_sort_is_rejected[na'me]` | Unit | invalid sort is rejected | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_invalid_sort_is_rejected[name,]` | Unit | invalid sort is rejected | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_invalid_sort_is_rejected[a[0]]` | Unit | invalid sort is rejected | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_render_sort[postgresql-expected0]` | Unit | render sort | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_render_sort[oracle-expected1]` | Unit | render sort | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_uses_search_column[params0-True]` | Unit | uses search column | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_uses_search_column[params1-True]` | Unit | uses search column | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_uses_search_column[params2-False]` | Unit | uses search column | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_uses_search_column[params3-False]` | Unit | uses search column | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_uses_search_column[params4-False]` | Unit | uses search column | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_uses_search_column[params5-False]` | Unit | uses search column | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_uses_search_column[params6-False]` | Unit | uses search column | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_uses_search_column[params7-True]` | Unit | uses search column | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_uses_search_column[params8-False]` | Unit | uses search column | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_oracle_checks_characteristic_values_on_search_and_payload` | Unit | oracle checks characteristic values on search and payload | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_embedded_and_referenced_branches_use_search` | Unit | embedded and referenced branches use search | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |

### `test_relationships.py`

```text
Filtering through service relationships: find service A by attributes of the service B it relates to.

Data model per test run (all scoped by serviceType "Rel-<run id>" of the referencing services):

    A  --DependentOn-->  B   (B: mac = 00:11:22:33:44:55)
    E  --ReliesOn----->  {B embedded by value, mac = 00:11:22:33:44:55}
    C  --DependentOn-->  D   (D: mac = 00:11:22:33:44:66)
    F  --DependentOn-->  G   (G: mac = aa:bb:..., but 00:11:22:33:44:55 as *serialNumber*)
    H  --supportingService--> B
```

| Test | Level | Description | PostgreSQL | Oracle |
|---|---|---|---|---|
| `test_attribute_filter_through_relationship` | API | attribute filter through relationship | ✅ passed (22 ms) | ✅ passed (41 ms) |
| `test_jsonpath_filter_through_relationship` | API | jsonpath filter through relationship | ✅ passed (4 ms) | ✅ passed (21 ms) |
| `test_relationship_type_applies_to_the_same_relationship` | API | relationship type applies to the same relationship | ✅ passed (7 ms) | ✅ passed (22 ms) |
| `test_characteristic_name_and_value_from_the_same_element` | API | G has a mac and the value 00:11:22:33:44:55, but not in the same characteristic -> F must not match. | ✅ passed (5 ms) | ✅ passed (27 ms) |
| `test_repeated_parameter_means_separate_elements` | API | repeated parameter means separate elements | ✅ passed (3 ms) | ✅ passed (8 ms) |
| `test_attribute_of_the_referenced_service` | API | attribute of the referenced service | ✅ passed (857 ms) | ✅ passed (138 ms) |
| `test_filter_on_reference_fields_needs_no_join` | API | filter on reference fields needs no join | ✅ passed (2 ms) | ✅ passed (7 ms) |
| `test_supporting_service` | API | supporting service | ✅ passed (4 ms) | ✅ passed (16 ms) |
| `test_no_match` | API | no match | ✅ passed (3 ms) | ✅ passed (2 ms) |
| `test_pagination_header_counts_joined_matches` | API | pagination header counts joined matches | ✅ passed (3 ms) | ✅ passed (12 ms) |
| `test_nested_references_are_rejected` | API | nested references are rejected | ✅ passed (17 ms) | ✅ passed (23 ms) |

### `test_security_unit.py`

AUTH configuration and the Basic user list (no API needed).

| Test | Level | Description | PostgreSQL | Oracle |
|---|---|---|---|---|
| `test_users_and_roles` | Unit | users and roles | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_sha256_secret` | Unit | sha256 secret | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_invalid_user_lists[]` | Unit | invalid user lists | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_invalid_user_lists[a:b]` | Unit | invalid user lists | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_invalid_user_lists[a::read]` | Unit | invalid user lists | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_invalid_user_lists[a:b:]` | Unit | invalid user lists | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_invalid_user_lists[a:b:admin]` | Unit | invalid user lists | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_invalid_user_lists[:b:read]` | Unit | invalid user lists | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_invalid_user_lists[a:b:c:d:read]` | Unit | invalid user lists | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_write_includes_read` | Unit | write includes read | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_misconfiguration_fails_at_start[env0]` | Unit | misconfiguration fails at start | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_misconfiguration_fails_at_start[env1]` | Unit | misconfiguration fails at start | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_misconfiguration_fails_at_start[env2]` | Unit | misconfiguration fails at start | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |
| `test_none_is_default` | Unit | none is default | ✅ passed (< 1 ms) | ✅ passed (< 1 ms) |

## Bruno collection

`tests/TMFC008`, folder `demo`: a walk-through of the features with checked results, run with the Bruno CLI (`bru run demo -r --env dev`) against the same API instances as the pytest suite. The requests create their own services (`serviceType` `Demo-<run>`) and delete them again. Skipped: the folder `0 auth` (the API runs without `AUTH_MODE`).

### 0 health

| Request | Checks | PostgreSQL | Oracle |
|---|---|---|---|
| GET /livez | alive | ✅ passed (223 ms) | ✅ passed (208 ms) |
| GET /readyz | ready: database reachable, schema migrated | ✅ passed (101 ms) | ✅ passed (96 ms) |

### 0 auth

| Request | Checks | PostgreSQL | Oracle |
|---|---|---|---|
| GET /service without credentials (401) |  | ⏭️ skipped | ⏭️ skipped |
| GET /service as reader (read is allowed) |  | ⏭️ skipped | ⏭️ skipped |
| POST /service as reader (403) |  | ⏭️ skipped | ⏭️ skipped |
| DELETE /service as reader (403) |  | ⏭️ skipped | ⏭️ skipped |

### 1 setup

| Request | Checks | PostgreSQL | Oracle |
|---|---|---|---|
| POST /service B (referenced) | created with id and href | ✅ passed (155 ms) | ✅ passed (144 ms) |
| POST /service A (depends on B) | created with id and href | ✅ passed (146 ms) | ✅ passed (140 ms) |
| POST /service C (inactive) | created with id and href | ✅ passed (146 ms) | ✅ passed (142 ms) |
| POST /service invalid (400) | rejected with a TMF Error | ✅ passed (99 ms) | ✅ passed (91 ms) |

### 2 search

| Request | Checks | PostgreSQL | Oracle |
|---|---|---|---|
| attribute filter state=active | finds A, B | ✅ passed (100 ms) | ✅ passed (95 ms) |
| OR with a comma | finds A, B, C | ✅ passed (99 ms) | ✅ passed (96 ms) |
| dotted path through an array | finds A, C | ✅ passed (100 ms) | ✅ passed (94 ms) |
| same array element name+value | finds A | ✅ passed (98 ms) | ✅ passed (92 ms) |
| name and value of different elements do not match | finds nothing | ✅ passed (97 ms) | ✅ passed (93 ms) |
| operators startDate.gte | finds A, B | ✅ passed (109 ms) | ✅ passed (92 ms) |
| operators startDate.lt | finds C | ✅ passed (96 ms) | ✅ passed (108 ms) |
| JSONPath filter | finds A | ✅ passed (97 ms) | ✅ passed (100 ms) |
| JSONPath with a comparison | finds A | ✅ passed (97 ms) | ✅ passed (94 ms) |
| path inside an object value | finds A | ✅ passed (95 ms) | ✅ passed (94 ms) |
| fields projection | only the selected attributes plus id, href and @type | ✅ passed (99 ms) | ✅ passed (92 ms) |
| sort -startDate | newest first | ✅ passed (99 ms) | ✅ passed (92 ms) |
| pagination limit/offset | first page: 206 Partial Content with the totals in headers | ✅ passed (101 ms) | ✅ passed (98 ms) |
| pagination last page | last page: 200 with the remaining service | ✅ passed (97 ms) | ✅ passed (97 ms) |
| invalid filter (400) | 400 in the TMF Error format | ✅ passed (96 ms) | ✅ passed (92 ms) |
| GET /service/{id} | the service | ✅ passed (97 ms) | ✅ passed (93 ms) |
| GET /service/{unknown id} (404) | 404 | ✅ passed (98 ms) | ✅ passed (95 ms) |

### 3 references

| Request | Checks | PostgreSQL | Oracle |
|---|---|---|---|
| referenced service state | finds A | ✅ passed (882 ms) | ✅ passed (236 ms) |
| referenced service inactive | finds nothing | ✅ passed (363 ms) | ✅ passed (148 ms) |
| referenced service name | finds A | ✅ passed (97 ms) | ✅ passed (109 ms) |
| referenced service characteristic | finds A | ✅ passed (97 ms) | ✅ passed (91 ms) |
| reference id (no join) | finds A | ✅ passed (98 ms) | ✅ passed (97 ms) |
| reference and own attribute | finds A | ✅ passed (915 ms) | ✅ passed (210 ms) |

### 4 history

| Request | Checks | PostgreSQL | Oracle |
|---|---|---|---|
| history enabled? | 200/206: history is enabled, 400: it is not (the other requests of this folder are skipped then) | ✅ passed (160 ms) | ✅ passed (185 ms) |
| PATCH merge-patch: state suspended | patched | ✅ passed (99 ms) | ✅ passed (99 ms) |
| PATCH json-patch: rename | patched | ✅ passed (101 ms) | ✅ passed (99 ms) |
| includeHistory: all revisions of A | two earlier revisions, then the clean current version; revisions follow each other without a gap | ✅ passed (141 ms) | ✅ passed (231 ms) |
| default: current versions only | one entry without revision | ✅ passed (93 ms) | ✅ passed (163 ms) |
| includeHistory: filter state=active | A as it was while active, and B | ✅ passed (98 ms) | ✅ passed (116 ms) |
| revisionStartTimestamp | revisions that were still valid at that time: 2 and the current one | ✅ passed (98 ms) | ✅ passed (165 ms) |
| revisionEndTimestamp | revisions that had started by then: 1 and 2 (it started the moment 1 ended) | ✅ passed (98 ms) | ✅ passed (165 ms) |
| GET by id: revision 1 | the first revision with its revision data | ✅ passed (98 ms) | ✅ passed (92 ms) |
| GET by id: current revision 3 | the current version, without revision data | ✅ passed (97 ms) | ✅ passed (94 ms) |
| GET by id: revision missing (400) | 400 | ✅ passed (94 ms) | ✅ passed (97 ms) |
| GET by id: unknown revision (404) | 404 | ✅ passed (97 ms) | ✅ passed (93 ms) |
| period without includeHistory (400) | 400 | ✅ passed (93 ms) | ✅ passed (91 ms) |
| history with a reference filter (400) | 400 | ✅ passed (94 ms) | ✅ passed (90 ms) |

### 5 events

| Request | Checks | PostgreSQL | Oracle |
|---|---|---|---|
| POST hub all events of the demo | hub registered | ✅ passed (144 ms) | ✅ passed (138 ms) |
| POST hub state changes only | hub registered | ✅ passed (143 ms) | ✅ passed (138 ms) |
| GET /hub/{id} | the subscription | ✅ passed (94 ms) | ✅ passed (93 ms) |
| POST /service D (create event) | created | ✅ passed (146 ms) | ✅ passed (141 ms) |
| PATCH state (state change event) | patched | ✅ passed (101 ms) | ✅ passed (103 ms) |
| PATCH description (attribute value change event) | patched | ✅ passed (102 ms) | ✅ passed (115 ms) |
| DELETE /service D (delete event) | deleted | ✅ passed (122 ms) | ✅ passed (100 ms) |
| events received by the listener | hub 'all' got the four events about D; hub 'state' got only the state change; the delete event carries the last state | ✅ passed (1132 ms) | ✅ passed (1125 ms) |
| DELETE /hub/{id} (all) | unsubscribed | ✅ passed (101 ms) | ✅ passed (106 ms) |
| DELETE /hub/{id} (state) | unsubscribed | ✅ passed (99 ms) | ✅ passed (104 ms) |
| POST /service E (nobody listens) | created | ✅ passed (146 ms) | ✅ passed (138 ms) |
| DELETE /service E | deleted | ✅ passed (100 ms) | ✅ passed (94 ms) |
| no more events after unsubscribing | still the 4 + 1 events from before; none for E | ✅ passed (1128 ms) | ✅ passed (1119 ms) |

### 6 cleanup

| Request | Checks | PostgreSQL | Oracle |
|---|---|---|---|
| DELETE /service A | deleted | ✅ passed (100 ms) | ✅ passed (99 ms) |
| DELETE /service B | deleted | ✅ passed (110 ms) | ✅ passed (93 ms) |
| DELETE /service C | deleted | ✅ passed (97 ms) | ✅ passed (95 ms) |
| GET deleted service (404) | gone | ✅ passed (96 ms) | ✅ passed (94 ms) |
| history of the deleted service | the last revision is kept (archived by the delete) | ✅ passed (101 ms) | ✅ passed (90 ms) |

## Performance

`scripts/bench.py`: 30 requests per query via the HTTP API (after a warm-up), end-to-end latency including `X-Total-Count`; data from `scripts/seed.py`, tables vacuumed / statistics gathered after the tests. The execution plans show the SQL the API generates for each query.

### PostgreSQL

```text
http://127.0.0.1:8001: 50003 services

query                                     matches   p50 ms   p95 ms
mac (JSONPath filter, name && value)            1      1.6      2.0
mac (attribute filter)                          1      1.5      1.8
mac, no match                                   0      1.6      2.1
A related to B with mac (join)                  1      2.6      3.0
related to B with mac, no match (join)          0      2.4      2.6
referenced service state (join, ~3%)          857     85.8     91.4
rare relatedParty name                         10      1.7      2.1
serviceType + state (~3%)                    1713      6.7      7.4
range startDate.gte (no index)                529    130.3    139.8
no filter, deep page                        50003      5.0      5.8
```

<details><summary>Execution plans</summary>

```text
=== mac (JSONPath filter, name && value)
    Nested Loop (actual rows=1 loops=1)
      ->  Limit (actual rows=1 loops=1)
            ->  Sort (actual rows=1 loops=1)
                  Sort Key: service_1.id
                  Sort Method: quicksort  Memory: 25kB
                  ->  Bitmap Heap Scan on service service_1 (actual rows=1 loops=1)
                        Recheck Cond: (payload @? '$."serviceCharacteristic"[*]?(@."name" == "mac" && @."value" == "02:00:00:00:61:b0")'::jsonpath)
                        Heap Blocks: exact=1
                        ->  Bitmap Index Scan on ix_service_payload_gin (actual rows=1 loops=1)
                              Index Cond: (payload @? '$."serviceCharacteristic"[*]?(@."name" == "mac" && @."value" == "02:00:00:00:61:b0")'::jsonpath)
      ->  Index Scan using service_pkey on service (actual rows=1 loops=1)
            Index Cond: (id = service_1.id)
    Planning Time: 0.328 ms
    Execution Time: 0.118 ms

=== mac (attribute filter)
    Nested Loop (actual rows=1 loops=1)
      ->  Limit (actual rows=1 loops=1)
            ->  Sort (actual rows=1 loops=1)
                  Sort Key: service_1.id
                  Sort Method: quicksort  Memory: 25kB
                  ->  Bitmap Heap Scan on service service_1 (actual rows=1 loops=1)
                        Recheck Cond: (payload @? '$?(@."serviceCharacteristic"."value" == "02:00:00:00:61:b0")'::jsonpath)
                        Heap Blocks: exact=1
                        ->  Bitmap Index Scan on ix_service_payload_gin (actual rows=1 loops=1)
                              Index Cond: (payload @? '$?(@."serviceCharacteristic"."value" == "02:00:00:00:61:b0")'::jsonpath)
      ->  Index Scan using service_pkey on service (actual rows=1 loops=1)
            Index Cond: (id = service_1.id)
    Planning Time: 0.065 ms
    Execution Time: 0.038 ms

=== mac, no match
    Nested Loop (actual rows=0 loops=1)
      ->  Limit (actual rows=0 loops=1)
            ->  Sort (actual rows=0 loops=1)
                  Sort Key: service_1.id
                  Sort Method: quicksort  Memory: 25kB
                  ->  Bitmap Heap Scan on service service_1 (actual rows=0 loops=1)
                        Recheck Cond: (payload @? '$."serviceCharacteristic"[*]?(@."name" == "mac" && @."value" == "ff:ff:ff:ff:ff:ff")'::jsonpath)
                        ->  Bitmap Index Scan on ix_service_payload_gin (actual rows=0 loops=1)
                              Index Cond: (payload @? '$."serviceCharacteristic"[*]?(@."name" == "mac" && @."value" == "ff:ff:ff:ff:ff:ff")'::jsonpath)
      ->  Index Scan using service_pkey on service (never executed)
            Index Cond: (id = service_1.id)
    Planning Time: 0.051 ms
    Execution Time: 0.059 ms

=== A related to B with mac (join)
    Nested Loop (actual rows=1 loops=1)
      ->  Limit (actual rows=1 loops=1)
            InitPlan 1 (returns $1)
              ->  HashAggregate (actual rows=1 loops=1)
                    Group Key: s1.id
                    Batches: 1  Memory Usage: 1561kB
                    ->  Append (actual rows=1 loops=1)
                          ->  Bitmap Heap Scan on service s1 (actual rows=0 loops=1)
                                Recheck Cond: (payload @? '$."serviceRelationship"."service"[*]?(exists (@."serviceCharacteristic"[*]?(@."name" == "mac" && @."value" == "02:00:00:00:61:b0")))'::jsonpath)
                                ->  Bitmap Index Scan on ix_service_payload_gin (actual rows=0 loops=1)
                                      Index Cond: (payload @? '$."serviceRelationship"."service"[*]?(exists (@."serviceCharacteristic"[*]?(@."name" == "mac" && @."value" == "02:00:00:00:61:b0")))'::jsonpath)
                          ->  Nested Loop (actual rows=1 loops=1)
                                ->  Bitmap Heap Scan on service t2 (actual rows=1 loops=1)
                                      Recheck Cond: (payload @? '$."serviceCharacteristic"[*]?(@."name" == "mac" && @."value" == "02:00:00:00:61:b0")'::jsonpath)
                                      Heap Blocks: exact=1
                                      ->  Bitmap Index Scan on ix_service_payload_gin (actual rows=1 loops=1)
                                            Index Cond: (payload @? '$."serviceCharacteristic"[*]?(@."name" == "mac" && @."value" == "02:00:00:00:61:b0")'::jsonpath)
                                ->  Bitmap Heap Scan on service s2 (actual rows=1 loops=1)
                                      Recheck Cond: (payload @> jsonb_build_object('serviceRelationship', jsonb_build_array(jsonb_build_object('service', jsonb_build_object('id', (t2.payload -> 'id'::text))))))
                                      Filter: jsonb_path_exists(payload, '$."serviceRelationship"."service"[*]?(@."id" == $"ref_id")'::jsonpath, jsonb_build_object('ref_id', (t2.payload -> 'id'::text)), false)
                                      Heap Blocks: exact=1
                                      ->  Bitmap Index Scan on ix_service_payload_gin (actual rows=1 loops=1)
                                            Index Cond: (payload @> jsonb_build_object('serviceRelationship', jsonb_build_array(jsonb_build_object('service', jsonb_build_object('id', (t2.payload -> 'id'::text))))))
            ->  Index Only Scan using service_pkey on service service_1 (actual rows=1 loops=1)
                  Index Cond: (id = ANY ($1))
                  Heap Fetches: 0
      ->  Index Scan using service_pkey on service (actual rows=1 loops=1)
            Index Cond: (id = service_1.id)
    Planning Time: 0.207 ms
    Execution Time: 0.443 ms

=== related to B with mac, no match (join)
    Nested Loop (actual rows=0 loops=1)
      ->  Limit (actual rows=0 loops=1)
            InitPlan 1 (returns $1)
              ->  HashAggregate (actual rows=0 loops=1)
                    Group Key: s1.id
                    Batches: 1  Memory Usage: 1561kB
                    ->  Append (actual rows=0 loops=1)
                          ->  Bitmap Heap Scan on service s1 (actual rows=0 loops=1)
                                Recheck Cond: (payload @? '$."serviceRelationship"."service"[*]?(exists (@."serviceCharacteristic"[*]?(@."name" == "mac" && @."value" == "ff:ff:ff:ff:ff:ff")))'::jsonpath)
                                ->  Bitmap Index Scan on ix_service_payload_gin (actual rows=0 loops=1)
                                      Index Cond: (payload @? '$."serviceRelationship"."service"[*]?(exists (@."serviceCharacteristic"[*]?(@."name" == "mac" && @."value" == "ff:ff:ff:ff:ff:ff")))'::jsonpath)
                          ->  Nested Loop (actual rows=0 loops=1)
                                ->  Bitmap Heap Scan on service t2 (actual rows=0 loops=1)
                                      Recheck Cond: (payload @? '$."serviceCharacteristic"[*]?(@."name" == "mac" && @."value" == "ff:ff:ff:ff:ff:ff")'::jsonpath)
                                      ->  Bitmap Index Scan on ix_service_payload_gin (actual rows=0 loops=1)
                                            Index Cond: (payload @? '$."serviceCharacteristic"[*]?(@."name" == "mac" && @."value" == "ff:ff:ff:ff:ff:ff")'::jsonpath)
                                ->  Bitmap Heap Scan on service s2 (never executed)
                                      Recheck Cond: (payload @> jsonb_build_object('serviceRelationship', jsonb_build_array(jsonb_build_object('service', jsonb_build_object('id', (t2.payload -> 'id'::text))))))
                                      Filter: jsonb_path_exists(payload, '$."serviceRelationship"."service"[*]?(@."id" == $"ref_id")'::jsonpath, jsonb_build_object('ref_id', (t2.payload -> 'id'::text)), false)
                                      ->  Bitmap Index Scan on ix_service_payload_gin (never executed)
                                            Index Cond: (payload @> jsonb_build_object('serviceRelationship', jsonb_build_array(jsonb_build_object('service', jsonb_build_object('id', (t2.payload -> 'id'::text))))))
            ->  Index Only Scan using service_pkey on service service_1 (actual rows=0 loops=1)
                  Index Cond: (id = ANY ($1))
                  Heap Fetches: 0
      ->  Index Scan using service_pkey on service (never executed)
            Index Cond: (id = service_1.id)
    Planning Time: 0.073 ms
    Execution Time: 0.357 ms

=== referenced service state (join, ~3%)
    Nested Loop (actual rows=100 loops=1)
      ->  Limit (actual rows=100 loops=1)
            InitPlan 1 (returns $1)
              ->  HashAggregate (actual rows=4222 loops=1)
                    Group Key: s1.id
                    Batches: 1  Memory Usage: 1809kB
                    ->  Append (actual rows=4222 loops=1)
                          ->  Bitmap Heap Scan on service s1 (actual rows=0 loops=1)
                                Recheck Cond: (payload @? '$?(exists (@."serviceRelationship"."service"[*]?(@."state" == "suspended")))'::jsonpath)
                                ->  Bitmap Index Scan on ix_service_payload_gin (actual rows=0 loops=1)
                                      Index Cond: (payload @? '$?(exists (@."serviceRelationship"."service"[*]?(@."state" == "suspended")))'::jsonpath)
                          ->  Nested Loop (actual rows=4222 loops=1)
                                ->  Bitmap Heap Scan on service t2 (actual rows=8421 loops=1)
                                      Recheck Cond: (payload @? '$?(@."state" == "suspended")'::jsonpath)
                                      Heap Blocks: exact=6521
                                      ->  Bitmap Index Scan on ix_service_payload_gin (actual rows=8455 loops=1)
                                            Index Cond: (payload @? '$?(@."state" == "suspended")'::jsonpath)
                                ->  Bitmap Heap Scan on service s2 (actual rows=1 loops=8421)
                                      Recheck Cond: (payload @> jsonb_build_object('serviceRelationship', jsonb_build_array(jsonb_build_object('service', jsonb_build_object('id', (t2.payload -> 'id'::text))))))
                                      Filter: jsonb_path_exists(payload, '$?(@."serviceRelationship"."service"."id" == $"ref_id")'::jsonpath, jsonb_build_object('ref_id', (t2.payload -> 'id'::text)), false)
                                      Heap Blocks: exact=4222
                                      ->  Bitmap Index Scan on ix_service_payload_gin (actual rows=1 loops=8421)
                                            Index Cond: (payload @> jsonb_build_object('serviceRelationship', jsonb_build_array(jsonb_build_object('service', jsonb_build_object('id', (t2.payload -> 'id'::text))))))
            ->  Sort (actual rows=100 loops=1)
                  Sort Key: service_1.id
                  Sort Method: top-N heapsort  Memory: 28kB
                  ->  Bitmap Heap Scan on service service_1 (actual rows=857 loops=1)
                        Recheck Cond: ((payload @? '$?(@."serviceType" == "Cloud")'::jsonpath) AND (id = ANY ($1)))
                        Heap Blocks: exact=842
                        ->  BitmapAnd (actual rows=0 loops=1)
                              ->  Bitmap Index Scan on ix_service_payload_gin (actual rows=10046 loops=1)
                                    Index Cond: (payload @? '$?(@."serviceType" == "Cloud")'::jsonpath)
                              ->  Bitmap Index Scan on service_pkey (actual rows=4222 loops=1)
                                    Index Cond: (id = ANY ($1))
      ->  Index Scan using service_pkey on service (actual rows=1 loops=100)
            Index Cond: (id = service_1.id)
    Planning Time: 0.070 ms
    Execution Time: 41.388 ms

=== rare relatedParty name
    Nested Loop (actual rows=10 loops=1)
      ->  Limit (actual rows=10 loops=1)
            ->  Sort (actual rows=10 loops=1)
                  Sort Key: service_1.id
                  Sort Method: quicksort  Memory: 25kB
                  ->  Bitmap Heap Scan on service service_1 (actual rows=10 loops=1)
                        Recheck Cond: (payload @? '$?(@."relatedParty"."partyOrPartyRole"."name" == "Customer 00001")'::jsonpath)
                        Heap Blocks: exact=10
                        ->  Bitmap Index Scan on ix_service_payload_gin (actual rows=10 loops=1)
                              Index Cond: (payload @? '$?(@."relatedParty"."partyOrPartyRole"."name" == "Customer 00001")'::jsonpath)
      ->  Index Scan using service_pkey on service (actual rows=1 loops=10)
            Index Cond: (id = service_1.id)
    Planning Time: 0.109 ms
    Execution Time: 0.065 ms

=== serviceType + state (~3%)
    Nested Loop (actual rows=100 loops=1)
      ->  Limit (actual rows=100 loops=1)
            ->  Sort (actual rows=100 loops=1)
                  Sort Key: service_1.id
                  Sort Method: top-N heapsort  Memory: 28kB
                  ->  Bitmap Heap Scan on service service_1 (actual rows=1713 loops=1)
                        Recheck Cond: ((payload @? '$?(@."serviceType" == "Cloud")'::jsonpath) AND (payload @? '$?(@."state" == "suspended")'::jsonpath))
                        Heap Blocks: exact=1622
                        ->  Bitmap Index Scan on ix_service_payload_gin (actual rows=1713 loops=1)
                              Index Cond: ((payload @? '$?(@."serviceType" == "Cloud")'::jsonpath) AND (payload @? '$?(@."state" == "suspended")'::jsonpath))
      ->  Index Scan using service_pkey on service (actual rows=1 loops=100)
            Index Cond: (id = service_1.id)
    Planning Time: 0.067 ms
    Execution Time: 1.845 ms

=== range startDate.gte (no index)
    Nested Loop (actual rows=100 loops=1)
      ->  Limit (actual rows=100 loops=1)
            ->  Index Scan using service_pkey on service service_1 (actual rows=100 loops=1)
                  Filter: (payload @? '$?(@."startDate" >= "2025-06-01")'::jsonpath)
                  Rows Removed by Filter: 8791
      ->  Index Scan using service_pkey on service (actual rows=1 loops=100)
            Index Cond: (id = service_1.id)
    Planning Time: 0.054 ms
    Execution Time: 4.031 ms

=== no filter, deep page
    Nested Loop (actual rows=100 loops=1)
      ->  Limit (actual rows=100 loops=1)
            ->  Index Only Scan using service_pkey on service service_1 (actual rows=49903 loops=1)
                  Heap Fetches: 952
      ->  Index Scan using service_pkey on service (actual rows=1 loops=100)
            Index Cond: (id = service_1.id)
    Planning Time: 0.064 ms
    Execution Time: 1.493 ms
```

</details>

### Oracle

```text
http://127.0.0.1:8002: 50000 services

query                                     matches   p50 ms   p95 ms
mac (JSONPath filter, name && value)            1      1.5      1.7
mac (attribute filter)                          1      1.4      1.9
mac, no match                                   0      1.3      1.7
A related to B with mac (join)                  1      1.5      1.7
related to B with mac, no match (join)          0      1.3      1.5
referenced service state (join, ~3%)          857     56.6     61.6
rare relatedParty name                         10      1.6      2.1
serviceType + state (~3%)                    1713     25.2     29.8
range startDate.gte (no index)                529     68.8     73.7
no filter, deep page                        50000      7.3      8.4
```

<details><summary>Execution plans</summary>

```text
=== mac (JSONPath filter, name && value)
    Plan hash value: 1496678595
     
    ----------------------------------------------------------------------
    | Id  | Operation                            | Name                  |
    ----------------------------------------------------------------------
    |   0 | SELECT STATEMENT                     |                       |
    |   1 |  NESTED LOOPS                        |                       |
    |   2 |   NESTED LOOPS                       |                       |
    |   3 |    VIEW                              |                       |
    |*  4 |     VIEW                             |                       |
    |*  5 |      WINDOW SORT PUSHED RANK         |                       |
    |*  6 |       TABLE ACCESS BY INDEX ROWID    | SERVICE               |
    |*  7 |        INDEX RANGE SCAN (MULTI VALUE)| IX_SERVICE_CHAR_VALUE |
    |*  8 |    INDEX UNIQUE SCAN                 | SYS_C008729           |
    |   9 |   TABLE ACCESS BY INDEX ROWID        | SERVICE               |
    ----------------------------------------------------------------------
     
    Predicate Information (identified by operation id):
    ---------------------------------------------------
     
       4 - filter("from$_subquery$_004"."rowlimit_$$_rownumber"<=100 AND 
                  "from$_subquery$_004"."rowlimit_$$_rownumber">0)
       5 - filter(ROW_NUMBER() OVER ( ORDER BY "SERVICE"."ID")<=100)
       6 - filter(JSON_EXISTS2("PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT OSON , 
                  '$."serviceCharacteristic"[*] ? ((@."name" == $v0) && (@."value" == 
                  $v1))' /* json_path_str  $.serviceCharacteristic[*]?((@.name.string() 
                  == $v0) && (@.value.string() == $v1))  */  PASSING :Q0_0 AS "v0" , 
                  :Q0_1 AS "v1" FALSE ON ERROR TYPE(LAX) )=1 AND JSON_EXISTS2("SEARCH" 
                  /*+ LOB_BY_VALUE */  FORMAT OSON , '$."serviceCharacteristic"[*] ? 
                  ((@."name" == $v0) && (@."value" == $v1))' /* json_path_str  
                  $.serviceCharacteristic[*]?((@.name.string() == $v0) && 
                  (@.value.string() == $v1))  */  PASSING :Q0_0 AS "v0" , :Q0_1 AS "v1" 
                  FALSE ON ERROR TYPE(LAX) )=1)
       7 - access(JSON_QUERY("SEARCH" /*+ LOB_BY_VALUE */  FORMAT OSON , 
                  '$.serviceCharacteristic.value.string()' RETURNING VARCHAR2(4000) ASIS  
                  WITHOUT ARRAY WRAPPER ERROR ON ERROR NULL ON EMPTY NULL ON MISMATCH 
                  TYPE(LAX)  MULTIVALUE)=:Q0_1)
       8 - access("SERVICE"."ID"="PAGE"."ID")

=== mac (attribute filter)
    Plan hash value: 1496678595
     
    ----------------------------------------------------------------------
    | Id  | Operation                            | Name                  |
    ----------------------------------------------------------------------
    |   0 | SELECT STATEMENT                     |                       |
    |   1 |  NESTED LOOPS                        |                       |
    |   2 |   NESTED LOOPS                       |                       |
    |   3 |    VIEW                              |                       |
    |*  4 |     VIEW                             |                       |
    |*  5 |      WINDOW SORT PUSHED RANK         |                       |
    |*  6 |       TABLE ACCESS BY INDEX ROWID    | SERVICE               |
    |*  7 |        INDEX RANGE SCAN (MULTI VALUE)| IX_SERVICE_CHAR_VALUE |
    |*  8 |    INDEX UNIQUE SCAN                 | SYS_C008729           |
    |   9 |   TABLE ACCESS BY INDEX ROWID        | SERVICE               |
    ----------------------------------------------------------------------
     
    Predicate Information (identified by operation id):
    ---------------------------------------------------
     
       4 - filter("from$_subquery$_004"."rowlimit_$$_rownumber"<=100 AND 
                  "from$_subquery$_004"."rowlimit_$$_rownumber">0)
       5 - filter(ROW_NUMBER() OVER ( ORDER BY "SERVICE"."ID")<=100)
       6 - filter(JSON_EXISTS2("PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT OSON , 
                  '$ ? (@."serviceCharacteristic"."value" == $v0)' /* json_path_str  
                  $?(@.serviceCharacteristic.value.string() == $v0)  */  PASSING :Q0_0 AS 
                  "v0" FALSE ON ERROR TYPE(LAX) )=1)
       7 - access(JSON_QUERY("SEARCH" /*+ LOB_BY_VALUE */  FORMAT OSON , 
                  '$.serviceCharacteristic.value.string()' RETURNING VARCHAR2(4000) ASIS  
                  WITHOUT ARRAY WRAPPER ERROR ON ERROR NULL ON EMPTY NULL ON MISMATCH 
                  TYPE(LAX)  MULTIVALUE)=:Q0_0)
       8 - access("SERVICE"."ID"="PAGE"."ID")

=== mac, no match
    Plan hash value: 1496678595
     
    ----------------------------------------------------------------------
    | Id  | Operation                            | Name                  |
    ----------------------------------------------------------------------
    |   0 | SELECT STATEMENT                     |                       |
    |   1 |  NESTED LOOPS                        |                       |
    |   2 |   NESTED LOOPS                       |                       |
    |   3 |    VIEW                              |                       |
    |*  4 |     VIEW                             |                       |
    |*  5 |      WINDOW SORT PUSHED RANK         |                       |
    |*  6 |       TABLE ACCESS BY INDEX ROWID    | SERVICE               |
    |*  7 |        INDEX RANGE SCAN (MULTI VALUE)| IX_SERVICE_CHAR_VALUE |
    |*  8 |    INDEX UNIQUE SCAN                 | SYS_C008729           |
    |   9 |   TABLE ACCESS BY INDEX ROWID        | SERVICE               |
    ----------------------------------------------------------------------
     
    Predicate Information (identified by operation id):
    ---------------------------------------------------
     
       4 - filter("from$_subquery$_004"."rowlimit_$$_rownumber"<=100 AND 
                  "from$_subquery$_004"."rowlimit_$$_rownumber">0)
       5 - filter(ROW_NUMBER() OVER ( ORDER BY "SERVICE"."ID")<=100)
       6 - filter(JSON_EXISTS2("PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT OSON , 
                  '$."serviceCharacteristic"[*] ? ((@."name" == $v0) && (@."value" == 
                  $v1))' /* json_path_str  $.serviceCharacteristic[*]?((@.name.string() 
                  == $v0) && (@.value.string() == $v1))  */  PASSING :Q0_0 AS "v0" , 
                  :Q0_1 AS "v1" FALSE ON ERROR TYPE(LAX) )=1 AND JSON_EXISTS2("SEARCH" 
                  /*+ LOB_BY_VALUE */  FORMAT OSON , '$."serviceCharacteristic"[*] ? 
                  ((@."name" == $v0) && (@."value" == $v1))' /* json_path_str  
                  $.serviceCharacteristic[*]?((@.name.string() == $v0) && 
                  (@.value.string() == $v1))  */  PASSING :Q0_0 AS "v0" , :Q0_1 AS "v1" 
                  FALSE ON ERROR TYPE(LAX) )=1)
       7 - access(JSON_QUERY("SEARCH" /*+ LOB_BY_VALUE */  FORMAT OSON , 
                  '$.serviceCharacteristic.value.string()' RETURNING VARCHAR2(4000) ASIS  
                  WITHOUT ARRAY WRAPPER ERROR ON ERROR NULL ON EMPTY NULL ON MISMATCH 
                  TYPE(LAX)  MULTIVALUE)=:Q0_1)
       8 - access("SERVICE"."ID"="PAGE"."ID")

=== A related to B with mac (join)
    Plan hash value: 4009380616
     
    ------------------------------------------------------------------------------
    | Id  | Operation                                    | Name                  |
    ------------------------------------------------------------------------------
    |   0 | SELECT STATEMENT                             |                       |
    |   1 |  NESTED LOOPS                                |                       |
    |   2 |   NESTED LOOPS                               |                       |
    |   3 |    VIEW                                      |                       |
    |*  4 |     VIEW                                     |                       |
    |*  5 |      WINDOW SORT PUSHED RANK                 |                       |
    |   6 |       NESTED LOOPS                           |                       |
    |   7 |        VIEW                                  | VW_NSO_1              |
    |   8 |         COUNT                                |                       |
    |*  9 |          FILTER                              |                       |
    |  10 |           VIEW                               |                       |
    |  11 |            HASH UNIQUE                       |                       |
    |  12 |             UNION-ALL                        |                       |
    |* 13 |              TABLE ACCESS BY INDEX ROWID     | SERVICE               |
    |* 14 |               INDEX RANGE SCAN (MULTI VALUE) | IX_SVC_REL_CHAR_NAME  |
    |  15 |              NESTED LOOPS                    |                       |
    |* 16 |               TABLE ACCESS BY INDEX ROWID    | SERVICE               |
    |* 17 |                INDEX RANGE SCAN (MULTI VALUE)| IX_SERVICE_CHAR_VALUE |
    |  18 |               TABLE ACCESS BY INDEX ROWID    | SERVICE               |
    |* 19 |                INDEX RANGE SCAN (MULTI VALUE)| IX_SVC_REL_ID         |
    |* 20 |        INDEX UNIQUE SCAN                     | SYS_C008729           |
    |* 21 |    INDEX UNIQUE SCAN                         | SYS_C008729           |
    |  22 |   TABLE ACCESS BY INDEX ROWID                | SERVICE               |
    ------------------------------------------------------------------------------
     
    Predicate Information (identified by operation id):
    ---------------------------------------------------
     
       4 - filter("from$_subquery$_009"."rowlimit_$$_rownumber"<=100 AND 
                  "from$_subquery$_009"."rowlimit_$$_rownumber">0)
       5 - filter(ROW_NUMBER() OVER ( ORDER BY "SERVICE"."ID")<=100)
       9 - filter(ROWNUM>0)
      13 - filter(JSON_EXISTS2("S1"."PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT 
                  OSON , '$."serviceRelationship"."service"[*] ? 
                  (exists(@."serviceCharacteristic"[*] ? ((@."name" == $v0) && (@."value" 
                  == $v1))))' /* json_path_str  $.serviceRelationship.service[*]?(exists(@
                  .serviceCharacteristic[*]?((@.name.string() == $v0) && 
                  (@.value.string() == $v1))))  */  PASSING :Q0E_0 AS "v0" , :Q0E_1 AS 
                  "v1" FALSE ON ERROR TYPE(LAX) )=1 AND JSON_EXISTS2("S1"."SEARCH" /*+ 
                  LOB_BY_VALUE */  FORMAT OSON , '$."serviceRelationship"."service"[*] ? 
                  (exists(@."serviceCharacteristic"[*] ? ((@."name" == $v0) && (@."value" 
                  == $v1))))' /* json_path_str  $.serviceRelationship.service[*]?(exists(@
                  .serviceCharacteristic[*]?((@.name.string() == $v0) && 
                  (@.value.string() == $v1))))  */  PASSING :Q0E_0 AS "v0" , :Q0E_1 AS 
                  "v1" FALSE ON ERROR TYPE(LAX) )=1)
      14 - access(JSON_QUERY("PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT OSON , 
                  '$.serviceRelationship.service.serviceCharacteristic.name.string()' 
                  RETURNING VARCHAR2(4000) ASIS  WITHOUT ARRAY WRAPPER ERROR ON ERROR 
                  NULL ON EMPTY NULL ON MISMATCH TYPE(LAX)  MULTIVALUE)=:Q0E_0)
      16 - filter(JSON_EXISTS2("T2"."PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT 
                  OSON , '$."serviceCharacteristic"[*] ? ((@."name" == $v0) && (@."value" 
                  == $v1))' /* json_path_str  $.serviceCharacteristic[*]?((@.name.string()
                   == $v0) && (@.value.string() == $v1))  */  PASSING :Q0T_0 AS "v0" , 
                  :Q0T_1 AS "v1" FALSE ON ERROR TYPE(LAX) )=1 AND 
                  JSON_EXISTS2("T2"."SEARCH" /*+ LOB_BY_VALUE */  FORMAT OSON , 
                  '$."serviceCharacteristic"[*] ? ((@."name" == $v0) && (@."value" == 
                  $v1))' /* json_path_str  $.serviceCharacteristic[*]?((@.name.string() 
                  == $v0) && (@.value.string() == $v1))  */  PASSING :Q0T_0 AS "v0" , 
                  :Q0T_1 AS "v1" FALSE ON ERROR TYPE(LAX) )=1)
      17 - access(JSON_QUERY("SEARCH" /*+ LOB_BY_VALUE */  FORMAT OSON , 
                  '$.serviceCharacteristic.value.string()' RETURNING VARCHAR2(4000) ASIS  
                  WITHOUT ARRAY WRAPPER ERROR ON ERROR NULL ON EMPTY NULL ON MISMATCH 
                  TYPE(LAX)  MULTIVALUE)=:Q0T_1)
      19 - access(JSON_QUERY("PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT OSON , 
                  '$.serviceRelationship.service.id.string()' RETURNING VARCHAR2(4000) 
                  ASIS  WITHOUT ARRAY WRAPPER ERROR ON ERROR NULL ON EMPTY NULL ON 
                  MISMATCH TYPE(LAX)  MULTIVALUE)=JSON_VALUE("T2"."PAYLOAD" /*+ 
                  LOB_BY_VALUE */  FORMAT OSON , '$.id' RETURNING VARCHAR2(4000) NULL ON 
                  ERROR TYPE(LAX) ))
      20 - access("SERVICE"."ID"="ID")
      21 - access("SERVICE"."ID"="PAGE"."ID")

=== related to B with mac, no match (join)
    Plan hash value: 4009380616
     
    ------------------------------------------------------------------------------
    | Id  | Operation                                    | Name                  |
    ------------------------------------------------------------------------------
    |   0 | SELECT STATEMENT                             |                       |
    |   1 |  NESTED LOOPS                                |                       |
    |   2 |   NESTED LOOPS                               |                       |
    |   3 |    VIEW                                      |                       |
    |*  4 |     VIEW                                     |                       |
    |*  5 |      WINDOW SORT PUSHED RANK                 |                       |
    |   6 |       NESTED LOOPS                           |                       |
    |   7 |        VIEW                                  | VW_NSO_1              |
    |   8 |         COUNT                                |                       |
    |*  9 |          FILTER                              |                       |
    |  10 |           VIEW                               |                       |
    |  11 |            HASH UNIQUE                       |                       |
    |  12 |             UNION-ALL                        |                       |
    |* 13 |              TABLE ACCESS BY INDEX ROWID     | SERVICE               |
    |* 14 |               INDEX RANGE SCAN (MULTI VALUE) | IX_SVC_REL_CHAR_NAME  |
    |  15 |              NESTED LOOPS                    |                       |
    |* 16 |               TABLE ACCESS BY INDEX ROWID    | SERVICE               |
    |* 17 |                INDEX RANGE SCAN (MULTI VALUE)| IX_SERVICE_CHAR_VALUE |
    |  18 |               TABLE ACCESS BY INDEX ROWID    | SERVICE               |
    |* 19 |                INDEX RANGE SCAN (MULTI VALUE)| IX_SVC_REL_ID         |
    |* 20 |        INDEX UNIQUE SCAN                     | SYS_C008729           |
    |* 21 |    INDEX UNIQUE SCAN                         | SYS_C008729           |
    |  22 |   TABLE ACCESS BY INDEX ROWID                | SERVICE               |
    ------------------------------------------------------------------------------
     
    Predicate Information (identified by operation id):
    ---------------------------------------------------
     
       4 - filter("from$_subquery$_009"."rowlimit_$$_rownumber"<=100 AND 
                  "from$_subquery$_009"."rowlimit_$$_rownumber">0)
       5 - filter(ROW_NUMBER() OVER ( ORDER BY "SERVICE"."ID")<=100)
       9 - filter(ROWNUM>0)
      13 - filter(JSON_EXISTS2("S1"."PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT 
                  OSON , '$."serviceRelationship"."service"[*] ? 
                  (exists(@."serviceCharacteristic"[*] ? ((@."name" == $v0) && (@."value" 
                  == $v1))))' /* json_path_str  $.serviceRelationship.service[*]?(exists(@
                  .serviceCharacteristic[*]?((@.name.string() == $v0) && 
                  (@.value.string() == $v1))))  */  PASSING :Q0E_0 AS "v0" , :Q0E_1 AS 
                  "v1" FALSE ON ERROR TYPE(LAX) )=1 AND JSON_EXISTS2("S1"."SEARCH" /*+ 
                  LOB_BY_VALUE */  FORMAT OSON , '$."serviceRelationship"."service"[*] ? 
                  (exists(@."serviceCharacteristic"[*] ? ((@."name" == $v0) && (@."value" 
                  == $v1))))' /* json_path_str  $.serviceRelationship.service[*]?(exists(@
                  .serviceCharacteristic[*]?((@.name.string() == $v0) && 
                  (@.value.string() == $v1))))  */  PASSING :Q0E_0 AS "v0" , :Q0E_1 AS 
                  "v1" FALSE ON ERROR TYPE(LAX) )=1)
      14 - access(JSON_QUERY("PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT OSON , 
                  '$.serviceRelationship.service.serviceCharacteristic.name.string()' 
                  RETURNING VARCHAR2(4000) ASIS  WITHOUT ARRAY WRAPPER ERROR ON ERROR 
                  NULL ON EMPTY NULL ON MISMATCH TYPE(LAX)  MULTIVALUE)=:Q0E_0)
      16 - filter(JSON_EXISTS2("T2"."PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT 
                  OSON , '$."serviceCharacteristic"[*] ? ((@."name" == $v0) && (@."value" 
                  == $v1))' /* json_path_str  $.serviceCharacteristic[*]?((@.name.string()
                   == $v0) && (@.value.string() == $v1))  */  PASSING :Q0T_0 AS "v0" , 
                  :Q0T_1 AS "v1" FALSE ON ERROR TYPE(LAX) )=1 AND 
                  JSON_EXISTS2("T2"."SEARCH" /*+ LOB_BY_VALUE */  FORMAT OSON , 
                  '$."serviceCharacteristic"[*] ? ((@."name" == $v0) && (@."value" == 
                  $v1))' /* json_path_str  $.serviceCharacteristic[*]?((@.name.string() 
                  == $v0) && (@.value.string() == $v1))  */  PASSING :Q0T_0 AS "v0" , 
                  :Q0T_1 AS "v1" FALSE ON ERROR TYPE(LAX) )=1)
      17 - access(JSON_QUERY("SEARCH" /*+ LOB_BY_VALUE */  FORMAT OSON , 
                  '$.serviceCharacteristic.value.string()' RETURNING VARCHAR2(4000) ASIS  
                  WITHOUT ARRAY WRAPPER ERROR ON ERROR NULL ON EMPTY NULL ON MISMATCH 
                  TYPE(LAX)  MULTIVALUE)=:Q0T_1)
      19 - access(JSON_QUERY("PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT OSON , 
                  '$.serviceRelationship.service.id.string()' RETURNING VARCHAR2(4000) 
                  ASIS  WITHOUT ARRAY WRAPPER ERROR ON ERROR NULL ON EMPTY NULL ON 
                  MISMATCH TYPE(LAX)  MULTIVALUE)=JSON_VALUE("T2"."PAYLOAD" /*+ 
                  LOB_BY_VALUE */  FORMAT OSON , '$.id' RETURNING VARCHAR2(4000) NULL ON 
                  ERROR TYPE(LAX) ))
      20 - access("SERVICE"."ID"="ID")
      21 - access("SERVICE"."ID"="PAGE"."ID")

=== referenced service state (join, ~3%)
    Plan hash value: 351466721
     
    -------------------------------------------------------------------------
    | Id  | Operation                                    | Name             |
    -------------------------------------------------------------------------
    |   0 | SELECT STATEMENT                             |                  |
    |   1 |  NESTED LOOPS                                |                  |
    |   2 |   NESTED LOOPS                               |                  |
    |   3 |    VIEW                                      |                  |
    |*  4 |     VIEW                                     |                  |
    |*  5 |      WINDOW SORT PUSHED RANK                 |                  |
    |*  6 |       HASH JOIN SEMI                         |                  |
    |   7 |        TABLE ACCESS BY INDEX ROWID           | SERVICE          |
    |*  8 |         INDEX RANGE SCAN (MULTI VALUE)       | IX_SERVICE_TYPE  |
    |   9 |        VIEW                                  | VW_NSO_1         |
    |  10 |         COUNT                                |                  |
    |* 11 |          FILTER                              |                  |
    |  12 |           VIEW                               |                  |
    |  13 |            HASH UNIQUE                       |                  |
    |  14 |             UNION-ALL                        |                  |
    |  15 |              TABLE ACCESS BY INDEX ROWID     | SERVICE          |
    |* 16 |               INDEX RANGE SCAN (MULTI VALUE) | IX_SVC_REL_STATE |
    |  17 |              NESTED LOOPS                    |                  |
    |  18 |               TABLE ACCESS BY INDEX ROWID    | SERVICE          |
    |* 19 |                INDEX RANGE SCAN (MULTI VALUE)| IX_SERVICE_STATE |
    |  20 |               TABLE ACCESS BY INDEX ROWID    | SERVICE          |
    |* 21 |                INDEX RANGE SCAN (MULTI VALUE)| IX_SVC_REL_ID    |
    |* 22 |    INDEX UNIQUE SCAN                         | SYS_C008729      |
    |  23 |   TABLE ACCESS BY INDEX ROWID                | SERVICE          |
    -------------------------------------------------------------------------
     
    Predicate Information (identified by operation id):
    ---------------------------------------------------
     
       4 - filter("from$_subquery$_009"."rowlimit_$$_rownumber"<=100 AND 
                  "from$_subquery$_009"."rowlimit_$$_rownumber">0)
       5 - filter(ROW_NUMBER() OVER ( ORDER BY "SERVICE"."ID")<=100)
       6 - access("SERVICE"."ID"="ID")
       8 - access(JSON_QUERY("PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT OSON , 
                  '$.serviceType.string()' RETURNING VARCHAR2(4000) ASIS  WITHOUT ARRAY 
                  WRAPPER ERROR ON ERROR NULL ON EMPTY NULL ON MISMATCH TYPE(LAX)  
                  MULTIVALUE)=:Q0_0)
      11 - filter(ROWNUM>0)
      16 - access(JSON_QUERY("PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT OSON , 
                  '$.serviceRelationship.service.state.string()' RETURNING VARCHAR2(4000) 
                  ASIS  WITHOUT ARRAY WRAPPER ERROR ON ERROR NULL ON EMPTY NULL ON 
                  MISMATCH TYPE(LAX)  MULTIVALUE)=:Q1E_0)
      19 - access(JSON_QUERY("PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT OSON , 
                  '$.state.string()' RETURNING VARCHAR2(4000) ASIS  WITHOUT ARRAY WRAPPER 
                  ERROR ON ERROR NULL ON EMPTY NULL ON MISMATCH TYPE(LAX)  
                  MULTIVALUE)=:Q1T_0)
      21 - access(JSON_QUERY("PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT OSON , 
                  '$.serviceRelationship.service.id.string()' RETURNING VARCHAR2(4000) 
                  ASIS  WITHOUT ARRAY WRAPPER ERROR ON ERROR NULL ON EMPTY NULL ON 
                  MISMATCH TYPE(LAX)  MULTIVALUE)=JSON_VALUE("T2"."PAYLOAD" /*+ 
                  LOB_BY_VALUE */  FORMAT OSON , '$.id' RETURNING VARCHAR2(4000) NULL ON 
                  ERROR TYPE(LAX) ))
      22 - access("SERVICE"."ID"="PAGE"."ID")

=== rare relatedParty name
    Plan hash value: 461321469
     
    ----------------------------------------------------------------------
    | Id  | Operation                            | Name                  |
    ----------------------------------------------------------------------
    |   0 | SELECT STATEMENT                     |                       |
    |   1 |  NESTED LOOPS                        |                       |
    |   2 |   NESTED LOOPS                       |                       |
    |   3 |    VIEW                              |                       |
    |*  4 |     VIEW                             |                       |
    |*  5 |      WINDOW SORT PUSHED RANK         |                       |
    |   6 |       TABLE ACCESS BY INDEX ROWID    | SERVICE               |
    |*  7 |        INDEX RANGE SCAN (MULTI VALUE)| IX_SERVICE_PARTY_NAME |
    |*  8 |    INDEX UNIQUE SCAN                 | SYS_C008729           |
    |   9 |   TABLE ACCESS BY INDEX ROWID        | SERVICE               |
    ----------------------------------------------------------------------
     
    Predicate Information (identified by operation id):
    ---------------------------------------------------
     
       4 - filter("from$_subquery$_004"."rowlimit_$$_rownumber"<=100 AND 
                  "from$_subquery$_004"."rowlimit_$$_rownumber">0)
       5 - filter(ROW_NUMBER() OVER ( ORDER BY "SERVICE"."ID")<=100)
       7 - access(JSON_QUERY("PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT OSON , 
                  '$.relatedParty.partyOrPartyRole.name.string()' RETURNING 
                  VARCHAR2(4000) ASIS  WITHOUT ARRAY WRAPPER ERROR ON ERROR NULL ON EMPTY 
                  NULL ON MISMATCH TYPE(LAX)  MULTIVALUE)=:Q0_0)
       8 - access("SERVICE"."ID"="PAGE"."ID")

=== serviceType + state (~3%)
    Plan hash value: 3265019568
     
    ----------------------------------------------------------------
    | Id  | Operation                            | Name            |
    ----------------------------------------------------------------
    |   0 | SELECT STATEMENT                     |                 |
    |   1 |  NESTED LOOPS                        |                 |
    |   2 |   NESTED LOOPS                       |                 |
    |   3 |    VIEW                              |                 |
    |*  4 |     VIEW                             |                 |
    |*  5 |      WINDOW SORT PUSHED RANK         |                 |
    |*  6 |       TABLE ACCESS BY INDEX ROWID    | SERVICE         |
    |*  7 |        INDEX RANGE SCAN (MULTI VALUE)| IX_SERVICE_TYPE |
    |*  8 |    INDEX UNIQUE SCAN                 | SYS_C008729     |
    |   9 |   TABLE ACCESS BY INDEX ROWID        | SERVICE         |
    ----------------------------------------------------------------
     
    Predicate Information (identified by operation id):
    ---------------------------------------------------
     
       4 - filter("from$_subquery$_004"."rowlimit_$$_rownumber"<=100 AND 
                  "from$_subquery$_004"."rowlimit_$$_rownumber">0)
       5 - filter(ROW_NUMBER() OVER ( ORDER BY "SERVICE"."ID")<=100)
       6 - filter(JSON_EXISTS2("PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT OSON , 
                  '$ ? (@."state" == $v0)' /* json_path_str  $?(@.state.string() == $v0)  
                  */  PASSING :Q1_0 AS "v0" FALSE ON ERROR TYPE(LAX) )=1)
       7 - access(JSON_QUERY("PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT OSON , 
                  '$.serviceType.string()' RETURNING VARCHAR2(4000) ASIS  WITHOUT ARRAY 
                  WRAPPER ERROR ON ERROR NULL ON EMPTY NULL ON MISMATCH TYPE(LAX)  
                  MULTIVALUE)=:Q0_0)
       8 - access("SERVICE"."ID"="PAGE"."ID")

=== range startDate.gte (no index)
    Plan hash value: 1622994807
     
    ----------------------------------------------------
    | Id  | Operation                    | Name        |
    ----------------------------------------------------
    |   0 | SELECT STATEMENT             |             |
    |   1 |  NESTED LOOPS                |             |
    |   2 |   NESTED LOOPS               |             |
    |   3 |    VIEW                      |             |
    |*  4 |     VIEW                     |             |
    |*  5 |      WINDOW SORT PUSHED RANK |             |
    |*  6 |       TABLE ACCESS FULL      | SERVICE     |
    |*  7 |    INDEX UNIQUE SCAN         | SYS_C008729 |
    |   8 |   TABLE ACCESS BY INDEX ROWID| SERVICE     |
    ----------------------------------------------------
     
    Predicate Information (identified by operation id):
    ---------------------------------------------------
     
       4 - filter("from$_subquery$_004"."rowlimit_$$_rownumber"<=100 AND 
                  "from$_subquery$_004"."rowlimit_$$_rownumber">0)
       5 - filter(ROW_NUMBER() OVER ( ORDER BY "SERVICE"."ID")<=100)
       6 - filter(JSON_EXISTS2("PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT OSON , 
                  '$ ? (@."startDate" >= $v0)' /* json_path_str  $?(@.startDate.string() 
                  >= $v0)  */  PASSING :Q0_0 AS "v0" FALSE ON ERROR TYPE(LAX) )=1)
       7 - access("SERVICE"."ID"="PAGE"."ID")

=== no filter, deep page
    Plan hash value: 781428968
     
    ----------------------------------------------------
    | Id  | Operation                    | Name        |
    ----------------------------------------------------
    |   0 | SELECT STATEMENT             |             |
    |   1 |  NESTED LOOPS                |             |
    |   2 |   NESTED LOOPS               |             |
    |   3 |    VIEW                      |             |
    |*  4 |     VIEW                     |             |
    |*  5 |      WINDOW NOSORT STOPKEY   |             |
    |   6 |       INDEX FULL SCAN        | SYS_C008729 |
    |*  7 |    INDEX UNIQUE SCAN         | SYS_C008729 |
    |   8 |   TABLE ACCESS BY INDEX ROWID| SERVICE     |
    ----------------------------------------------------
     
    Predicate Information (identified by operation id):
    ---------------------------------------------------
     
       4 - filter("from$_subquery$_004"."rowlimit_$$_rownumber"<=49900 AND 
                  "from$_subquery$_004"."rowlimit_$$_rownumber">49800)
       5 - filter(ROW_NUMBER() OVER ( ORDER BY "SERVICE"."ID")<=49900)
       7 - access("SERVICE"."ID"="PAGE"."ID")
```

</details>

## Not included

* The authentication modes `basic` and `oauth2`: the APIs run with `AUTH_MODE=none`, so `test_auth.py` and the Bruno folder `0 auth` are skipped (see the README, *Authentication*, for running the tests in these modes).
* The TM Forum conformance test kit (`ctk/run-api-ctk.sh`), see `ctk/README.md`.

## Reproduce

```bash
docker compose up -d db oracle
export PG=postgresql+asyncpg://app:secret@localhost:5432/app_db
export ORA='oracle+oracledb_async://app:secret@localhost:1521/?service_name=FREEPDB1'
DATABASE_URL=$PG alembic upgrade head && DATABASE_URL=$ORA alembic upgrade head
HISTORY_ENABLED=true DATABASE_URL=$PG  uvicorn openapi_server.main:app --port 8001 &
HISTORY_ENABLED=true DATABASE_URL=$ORA uvicorn openapi_server.main:app --port 8002 &
DATABASE_URL=${PG/+asyncpg/} python scripts/seed.py --count 50000 --truncate   # data for the performance measurement
DATABASE_URL=${ORA/_async/} python scripts/seed.py --count 50000 --truncate
npm install -g @usebruno/cli@4.3.0   # once, for the Bruno collection (the devcontainer does it)
python scripts/test_report.py --target "PostgreSQL|http://127.0.0.1:8001|$PG" --target "Oracle|http://127.0.0.1:8002|$ORA"
```
