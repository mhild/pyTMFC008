# Test report

Generated on 2026-10-23 15:20 UTC by `scripts/test_report.py`. To regenerate, see [Reproduce](#reproduce).

## Result

| Backend | API | Result |
|---|---|---|
| PostgreSQL | `http://127.0.0.1:8001` | 73 passed in 0.96s |
| Oracle | `http://127.0.0.1:8002` | 73 passed in 1.12s |

## Test environment

| | |
|---|---|
| Code version | `main` @ `9feb74d` |
| Operating system | Debian GNU/Linux 13 (trixie) (Kernel 6.12.13-200.fc41.aarch64, aarch64) |
| CPU | Apple (aarch64, model name not exposed to the VM), 4 CPUs |
| Memory | 7.7 GiB |
| Python | 3.12.15 (CPython) |
| Database PostgreSQL | PostgreSQL 16.15 on aarch64-unknown-linux-musl, compiled by gcc (Alpine 15.2.0) 15.2.0, 64-bit – 50,000 services in table |
| Database Oracle | Oracle AI Database 26ai Free Release 23.26.3.0.0 - Develop, Learn, and Run for Free Version 23.26.3.0.0 – 50,000 services in table |
| Container | `gvenzl/oracle-free:23-slim` (Up 7 hours (healthy)) |
| Container | `postgres:16-alpine` (Up 7 hours (healthy)) |
| Packages | fastapi 0.136.0, uvicorn 0.44.0, pydantic 2.13.3, SQLAlchemy 2.0.49, alembic 1.18.4, asyncpg 0.31.0, oracledb 26.0.1, cryptography 46.0.3, httpx 0.28.1, pytest 9.1.1 |

For each test run the API ran as a separate uvicorn instance (one worker) on the same host as the databases (Docker).

## Test cases

### `test_api.py`

```text
Integration tests against a running TMF638 API (TMF_BASE_URL); backend-agnostic.

Every run uses a unique marker so the tests also work on a pre-filled database.
```

| Test | Description | PostgreSQL | Oracle |
|---|---|---|---|
| `test_create_returns_resource` | create returns resource | ✅ passed (32 ms) | ✅ passed (43 ms) |
| `test_retrieve` | retrieve | ✅ passed (3 ms) | ✅ passed (4 ms) |
| `test_retrieve_with_fields` | retrieve with fields | ✅ passed (2 ms) | ✅ passed (1 ms) |
| `test_retrieve_unknown_and_invalid_id` | retrieve unknown and invalid id | ✅ passed (2 ms) | ✅ passed (2 ms) |
| `test_attribute_filter` | attribute filter | ✅ passed (9 ms) | ✅ passed (41 ms) |
| `test_attribute_filter_dotted_path` | attribute filter dotted path | ✅ passed (3 ms) | ✅ passed (20 ms) |
| `test_attribute_filter_number` | attribute filter number | ✅ passed (2 ms) | ✅ passed (11 ms) |
| `test_attribute_filter_operators` | attribute filter operators | ✅ passed (6 ms) | ✅ passed (58 ms) |
| `test_jsonpath_filter_characteristic` | The search the PoC is about: characteristic name AND value in the same array element. | ✅ passed (2 ms) | ✅ passed (10 ms) |
| `test_jsonpath_filter_does_not_mix_array_elements` | jsonpath filter does not mix array elements | ✅ passed (2 ms) | ✅ passed (3 ms) |
| `test_jsonpath_filter_related_party` | jsonpath filter related party | ✅ passed (2 ms) | ✅ passed (10 ms) |
| `test_quotes_in_values_are_data_not_syntax` | quotes in values are data not syntax | ✅ passed (6 ms) | ✅ passed (18 ms) |
| `test_invalid_filter_is_bad_request` | invalid filter is bad request | ✅ passed (1 ms) | ✅ passed (2 ms) |
| `test_list_fields` | list fields | ✅ passed (3 ms) | ✅ passed (4 ms) |
| `test_pagination` | pagination | ✅ passed (4 ms) | ✅ passed (14 ms) |
| `test_merge_patch` | merge patch | ✅ passed (6 ms) | ✅ passed (18 ms) |
| `test_json_patch` | json patch | ✅ passed (3 ms) | ✅ passed (5 ms) |
| `test_patch_cannot_change_id` | patch cannot change id | ✅ passed (2 ms) | ✅ passed (3 ms) |
| `test_patch_errors` | patch errors | ✅ passed (3 ms) | ✅ passed (4 ms) |
| `test_delete` | delete | ✅ passed (12 ms) | ✅ passed (22 ms) |

### `test_query.py`

Unit tests for the TMF630 filter parser and SQL/JSON path renderers (no DB needed).

| Test | Description | PostgreSQL | Oracle |
|---|---|---|---|
| `test_attribute_filter_pg[params0-$ ? (@."serviceType" == "Cloud")]` | attribute filter pg | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_attribute_filter_pg[params1-$ ? ((@."state" == "active") \|\| (@."state" == "inactive"))]` | attribute filter pg | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_attribute_filter_pg[params2-$ ? (@."relatedParty"."partyOrPartyRole"."name" == "Peter Meyer")]` | attribute filter pg | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_attribute_filter_pg[params3-$ ? (@."startDate" >= "2024-01-01")]` | attribute filter pg | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_attribute_filter_pg[params4-$ ? (@."startDate" >= "2024-01-01")]` | attribute filter pg | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_attribute_filter_pg[params5-$ ? (@."state" != "active")]` | attribute filter pg | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_attribute_filter_pg[params6-$ ? ((@."value" == "300") \|\| (@."value" == 300))]` | attribute filter pg | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_attribute_filter_pg[params7-$ ? ((@."isEnabled" == "true") \|\| (@."isEnabled" == true))]` | attribute filter pg | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_attribute_filter_pg[params8-$ ? (@."@type" == "Service")]` | attribute filter pg | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_jsonpath_filter_pg[$.serviceCharacteristic[?(@.name=='mac' && @.value=='00:11:22:33:44:55')]-$."serviceCharacteristic"[*] ? ((@."name" == "mac") && (@."value" == "00:11:22:33:44:55"))]` | jsonpath filter pg | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_jsonpath_filter_pg[$.relatedParty[?(@.partyOrPartyRole.name=='Peter Meyer')]-$."relatedParty"[*] ? (@."partyOrPartyRole"."name" == "Peter Meyer")]` | jsonpath filter pg | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_jsonpath_filter_pg[$.feature[*].featureCharacteristic[?(@.value==true)]-$."feature"[*]."featureCharacteristic"[*] ? (@."value" == true)]` | jsonpath filter pg | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_jsonpath_filter_pg[$[?(@.state=='a' \|\| !(@.x > 3.5))]-$ ? ((@."state" == "a") \|\| (!(@."x" > 3.5)))]` | jsonpath filter pg | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_jsonpath_filter_pg[$['@type']-$."@type"]` | jsonpath filter pg | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_jsonpath_filter_pg[$[?(@.@type=='Service')]-$ ? (@."@type" == "Service")]` | jsonpath filter pg | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_jsonpath_filter_pg[$[?(@.endDate)]-$ ? (exists(@."endDate"))]` | jsonpath filter pg | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_jsonpath_filter_pg[$[?(@.name=="a\\"b")]-$ ? (@."name" == "a\\"b")]` | jsonpath filter pg | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_oracle_uses_bind_variables_for_strings` | oracle uses bind variables for strings | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_oracle_sql_contains_no_user_strings` | oracle sql contains no user strings | ✅ passed (0 ms) | ✅ passed (1 ms) |
| `test_pg_sql_binds_the_whole_path` | pg sql binds the whole path | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_reserved_params_are_not_filters` | reserved params are not filters | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_invalid_filters_are_rejected[params0]` | invalid filters are rejected | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_invalid_filters_are_rejected[params1]` | invalid filters are rejected | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_invalid_filters_are_rejected[params2]` | invalid filters are rejected | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_invalid_filters_are_rejected[params3]` | invalid filters are rejected | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_invalid_filters_are_rejected[params4]` | invalid filters are rejected | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_invalid_filters_are_rejected[params5]` | invalid filters are rejected | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_invalid_filters_are_rejected[params6]` | invalid filters are rejected | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_attribute_filters_grouped_by_prefix[params0-expected0]` | attribute filters grouped by prefix | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_attribute_filters_grouped_by_prefix[params1-expected1]` | attribute filters grouped by prefix | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_attribute_filters_grouped_by_prefix[params2-expected2]` | attribute filters grouped by prefix | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_attribute_filters_grouped_by_prefix[params3-expected3]` | attribute filters grouped by prefix | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_reference_is_resolved` | reference is resolved | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_jsonpath_and_attribute_syntax_resolve_alike` | jsonpath and attribute syntax resolve alike | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_reference_sql_joins_by_id[postgresql]` | reference sql joins by id | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_reference_sql_joins_by_id[oracle]` | reference sql joins by id | ✅ passed (0 ms) | ✅ passed (1 ms) |
| `test_join_only_when_dereferencing[params0-False]` | join only when dereferencing | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_join_only_when_dereferencing[params1-False]` | join only when dereferencing | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_join_only_when_dereferencing[params2-True]` | join only when dereferencing | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_join_only_when_dereferencing[params3-True]` | join only when dereferencing | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_join_only_when_dereferencing[params4-False]` | join only when dereferencing | ✅ passed (0 ms) | ✅ passed (0 ms) |
| `test_nested_references_are_rejected` | nested references are rejected | ✅ passed (0 ms) | ✅ passed (0 ms) |

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

| Test | Description | PostgreSQL | Oracle |
|---|---|---|---|
| `test_attribute_filter_through_relationship` | attribute filter through relationship | ✅ passed (26 ms) | ✅ passed (50 ms) |
| `test_jsonpath_filter_through_relationship` | jsonpath filter through relationship | ✅ passed (4 ms) | ✅ passed (25 ms) |
| `test_relationship_type_applies_to_the_same_relationship` | relationship type applies to the same relationship | ✅ passed (7 ms) | ✅ passed (29 ms) |
| `test_characteristic_name_and_value_from_the_same_element` | G has a mac and the value 00:11:22:33:44:55, but not in the same characteristic -> F must not match. | ✅ passed (6 ms) | ✅ passed (39 ms) |
| `test_repeated_parameter_means_separate_elements` | repeated parameter means separate elements | ✅ passed (3 ms) | ✅ passed (11 ms) |
| `test_attribute_of_the_referenced_service` | attribute of the referenced service | ✅ passed (651 ms) | ✅ passed (433 ms) |
| `test_filter_on_reference_fields_needs_no_join` | filter on reference fields needs no join | ✅ passed (3 ms) | ✅ passed (74 ms) |
| `test_supporting_service` | supporting service | ✅ passed (5 ms) | ✅ passed (25 ms) |
| `test_no_match` | no match | ✅ passed (3 ms) | ✅ passed (5 ms) |
| `test_pagination_header_counts_joined_matches` | pagination header counts joined matches | ✅ passed (3 ms) | ✅ passed (15 ms) |
| `test_nested_references_are_rejected` | nested references are rejected | ✅ passed (15 ms) | ✅ passed (22 ms) |

## Performance

`scripts/bench.py`: 30 requests per query via the HTTP API (after a warm-up), end-to-end latency including `X-Total-Count`; data from `scripts/seed.py`. The execution plans show the SQL the API generates for each query.

### PostgreSQL

```text
http://127.0.0.1:8001: 50000 services

query                                     matches   p50 ms   p95 ms
mac (JSONPath filter, name && value)            1      1.9      2.2
mac (attribute filter)                          1      1.7      2.1
mac, no match                                   0      1.7      2.1
A related to B with mac (join)                  1      3.3      4.0
related to B with mac, no match (join)          0      3.0      3.9
rare relatedParty name                         10      1.9      2.3
serviceType + state (~3%)                    1713      8.4      9.7
range startDate.gte (no index)                529    135.4    140.4
no filter, deep page                        50000      5.7      6.3
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
                        Recheck Cond: (payload @? '$."serviceCharacteristic"[*]?(@."name" == "mac" && @."value" == "02:00:00:00:61:af")'::jsonpath)
                        Heap Blocks: exact=1
                        ->  Bitmap Index Scan on ix_service_payload_gin (actual rows=1 loops=1)
                              Index Cond: (payload @? '$."serviceCharacteristic"[*]?(@."name" == "mac" && @."value" == "02:00:00:00:61:af")'::jsonpath)
      ->  Index Scan using service_pkey on service (actual rows=1 loops=1)
            Index Cond: (id = service_1.id)
    Planning Time: 0.453 ms
    Execution Time: 0.243 ms

=== mac (attribute filter)
    Nested Loop (actual rows=1 loops=1)
      ->  Limit (actual rows=1 loops=1)
            ->  Sort (actual rows=1 loops=1)
                  Sort Key: service_1.id
                  Sort Method: quicksort  Memory: 25kB
                  ->  Bitmap Heap Scan on service service_1 (actual rows=1 loops=1)
                        Recheck Cond: (payload @? '$?(@."serviceCharacteristic"."value" == "02:00:00:00:61:af")'::jsonpath)
                        Heap Blocks: exact=1
                        ->  Bitmap Index Scan on ix_service_payload_gin (actual rows=1 loops=1)
                              Index Cond: (payload @? '$?(@."serviceCharacteristic"."value" == "02:00:00:00:61:af")'::jsonpath)
      ->  Index Scan using service_pkey on service (actual rows=1 loops=1)
            Index Cond: (id = service_1.id)
    Planning Time: 0.067 ms
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
    Planning Time: 0.060 ms
    Execution Time: 0.076 ms

=== A related to B with mac (join)
    Nested Loop (actual rows=1 loops=1)
      ->  Limit (actual rows=1 loops=1)
            InitPlan 1 (returns $1)
              ->  HashAggregate (actual rows=1 loops=1)
                    Group Key: s1.id
                    Batches: 1  Memory Usage: 1561kB
                    ->  Append (actual rows=1 loops=1)
                          ->  Bitmap Heap Scan on service s1 (actual rows=0 loops=1)
                                Recheck Cond: (payload @? '$."serviceRelationship"."service"[*]?(exists (@."serviceCharacteristic"[*]?(@."name" == "mac" && @."value" == "02:00:00:00:61:ae")))'::jsonpath)
                                ->  Bitmap Index Scan on ix_service_payload_gin (actual rows=0 loops=1)
                                      Index Cond: (payload @? '$."serviceRelationship"."service"[*]?(exists (@."serviceCharacteristic"[*]?(@."name" == "mac" && @."value" == "02:00:00:00:61:ae")))'::jsonpath)
                          ->  Nested Loop (actual rows=1 loops=1)
                                ->  Bitmap Heap Scan on service t2 (actual rows=1 loops=1)
                                      Recheck Cond: (payload @? '$."serviceCharacteristic"[*]?(@."name" == "mac" && @."value" == "02:00:00:00:61:ae")'::jsonpath)
                                      Heap Blocks: exact=1
                                      ->  Bitmap Index Scan on ix_service_payload_gin (actual rows=1 loops=1)
                                            Index Cond: (payload @? '$."serviceCharacteristic"[*]?(@."name" == "mac" && @."value" == "02:00:00:00:61:ae")'::jsonpath)
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
    Planning Time: 0.298 ms
    Execution Time: 0.737 ms

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
    Planning Time: 0.110 ms
    Execution Time: 0.560 ms

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
    Planning Time: 0.085 ms
    Execution Time: 0.191 ms

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
    Planning Time: 0.064 ms
    Execution Time: 4.486 ms

=== range startDate.gte (no index)
    Nested Loop (actual rows=100 loops=1)
      ->  Limit (actual rows=100 loops=1)
            ->  Index Scan using service_pkey on service service_1 (actual rows=100 loops=1)
                  Filter: (payload @? '$?(@."startDate" >= "2025-06-01")'::jsonpath)
                  Rows Removed by Filter: 8791
      ->  Index Scan using service_pkey on service (actual rows=1 loops=100)
            Index Cond: (id = service_1.id)
    Planning Time: 0.109 ms
    Execution Time: 6.895 ms

=== no filter, deep page
    Nested Loop (actual rows=100 loops=1)
      ->  Limit (actual rows=100 loops=1)
            ->  Index Only Scan using service_pkey on service service_1 (actual rows=49900 loops=1)
                  Heap Fetches: 127
      ->  Index Scan using service_pkey on service (actual rows=1 loops=100)
            Index Cond: (id = service_1.id)
    Planning Time: 0.084 ms
    Execution Time: 1.480 ms
```

</details>

### Oracle

```text
http://127.0.0.1:8002: 50000 services

query                                     matches   p50 ms   p95 ms
mac (JSONPath filter, name && value)            1      2.0      2.7
mac (attribute filter)                          1      1.6      2.3
mac, no match                                   0      1.6      2.0
A related to B with mac (join)                  1      1.7      2.4
related to B with mac, no match (join)          0      1.5      1.8
rare relatedParty name                         10      1.7      2.1
serviceType + state (~3%)                    1713     21.6     29.5
range startDate.gte (no index)                529     52.9     55.5
no filter, deep page                        50000      8.7      9.1
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
                  :Q0_1 AS "v1" FALSE ON ERROR TYPE(LAX) )=1)
       7 - access(JSON_QUERY("PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT OSON , 
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
    |   6 |       TABLE ACCESS BY INDEX ROWID    | SERVICE               |
    |*  7 |        INDEX RANGE SCAN (MULTI VALUE)| IX_SERVICE_CHAR_VALUE |
    |*  8 |    INDEX UNIQUE SCAN                 | SYS_C008729           |
    |   9 |   TABLE ACCESS BY INDEX ROWID        | SERVICE               |
    ----------------------------------------------------------------------
     
    Predicate Information (identified by operation id):
    ---------------------------------------------------
     
       4 - filter("from$_subquery$_004"."rowlimit_$$_rownumber"<=100 AND 
                  "from$_subquery$_004"."rowlimit_$$_rownumber">0)
       5 - filter(ROW_NUMBER() OVER ( ORDER BY "SERVICE"."ID")<=100)
       7 - access(JSON_QUERY("PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT OSON , 
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
                  :Q0_1 AS "v1" FALSE ON ERROR TYPE(LAX) )=1)
       7 - access(JSON_QUERY("PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT OSON , 
                  '$.serviceCharacteristic.value.string()' RETURNING VARCHAR2(4000) ASIS  
                  WITHOUT ARRAY WRAPPER ERROR ON ERROR NULL ON EMPTY NULL ON MISMATCH 
                  TYPE(LAX)  MULTIVALUE)=:Q0_1)
       8 - access("SERVICE"."ID"="PAGE"."ID")

=== A related to B with mac (join)
    Plan hash value: 995588135
     
    ---------------------------------------------------------------------------
    | Id  | Operation                                 | Name                  |
    ---------------------------------------------------------------------------
    |   0 | SELECT STATEMENT                          |                       |
    |   1 |  NESTED LOOPS                             |                       |
    |   2 |   NESTED LOOPS                            |                       |
    |   3 |    VIEW                                   |                       |
    |*  4 |     VIEW                                  |                       |
    |*  5 |      WINDOW SORT PUSHED RANK              |                       |
    |   6 |       NESTED LOOPS                        |                       |
    |   7 |        VIEW                               | VW_NSO_1              |
    |   8 |         HASH UNIQUE                       |                       |
    |   9 |          UNION-ALL                        |                       |
    |* 10 |           TABLE ACCESS BY INDEX ROWID     | SERVICE               |
    |* 11 |            INDEX RANGE SCAN (MULTI VALUE) | IX_SVC_REL_CHAR_NAME  |
    |  12 |           NESTED LOOPS                    |                       |
    |* 13 |            TABLE ACCESS BY INDEX ROWID    | SERVICE               |
    |* 14 |             INDEX RANGE SCAN (MULTI VALUE)| IX_SERVICE_CHAR_VALUE |
    |  15 |            TABLE ACCESS BY INDEX ROWID    | SERVICE               |
    |* 16 |             INDEX RANGE SCAN (MULTI VALUE)| IX_SVC_REL_ID         |
    |* 17 |        INDEX UNIQUE SCAN                  | SYS_C008729           |
    |* 18 |    INDEX UNIQUE SCAN                      | SYS_C008729           |
    |  19 |   TABLE ACCESS BY INDEX ROWID             | SERVICE               |
    ---------------------------------------------------------------------------
     
    Predicate Information (identified by operation id):
    ---------------------------------------------------
     
       4 - filter("from$_subquery$_008"."rowlimit_$$_rownumber"<=100 AND 
                  "from$_subquery$_008"."rowlimit_$$_rownumber">0)
       5 - filter(ROW_NUMBER() OVER ( ORDER BY "SERVICE"."ID")<=100)
      10 - filter(JSON_EXISTS2("S1"."PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT 
                  OSON , '$."serviceRelationship"."service"[*] ? 
                  (exists(@."serviceCharacteristic"[*] ? ((@."name" == $v0) && (@."value" 
                  == $v1))))' /* json_path_str  $.serviceRelationship.service[*]?(exists(@
                  .serviceCharacteristic[*]?((@.name.string() == $v0) && 
                  (@.value.string() == $v1))))  */  PASSING :Q0E_0 AS "v0" , :Q0E_1 AS 
                  "v1" FALSE ON ERROR TYPE(LAX) )=1)
      11 - access(JSON_QUERY("PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT OSON , 
                  '$.serviceRelationship.service.serviceCharacteristic.name.string()' 
                  RETURNING VARCHAR2(4000) ASIS  WITHOUT ARRAY WRAPPER ERROR ON ERROR 
                  NULL ON EMPTY NULL ON MISMATCH TYPE(LAX)  MULTIVALUE)=:Q0E_0)
      13 - filter(JSON_EXISTS2("T2"."PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT 
                  OSON , '$."serviceCharacteristic"[*] ? ((@."name" == $v0) && (@."value" 
                  == $v1))' /* json_path_str  $.serviceCharacteristic[*]?((@.name.string()
                   == $v0) && (@.value.string() == $v1))  */  PASSING :Q0T_0 AS "v0" , 
                  :Q0T_1 AS "v1" FALSE ON ERROR TYPE(LAX) )=1)
      14 - access(JSON_QUERY("PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT OSON , 
                  '$.serviceCharacteristic.value.string()' RETURNING VARCHAR2(4000) ASIS  
                  WITHOUT ARRAY WRAPPER ERROR ON ERROR NULL ON EMPTY NULL ON MISMATCH 
                  TYPE(LAX)  MULTIVALUE)=:Q0T_1)
      16 - access(JSON_QUERY("PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT OSON , 
                  '$.serviceRelationship.service.id.string()' RETURNING VARCHAR2(4000) 
                  ASIS  WITHOUT ARRAY WRAPPER ERROR ON ERROR NULL ON EMPTY NULL ON 
                  MISMATCH TYPE(LAX)  MULTIVALUE)=JSON_VALUE("T2"."PAYLOAD" /*+ 
                  LOB_BY_VALUE */  FORMAT OSON , '$.id' RETURNING VARCHAR2(4000) NULL ON 
                  ERROR TYPE(LAX) ))
      17 - access("SERVICE"."ID"="ID")
      18 - access("SERVICE"."ID"="PAGE"."ID")

=== related to B with mac, no match (join)
    Plan hash value: 995588135
     
    ---------------------------------------------------------------------------
    | Id  | Operation                                 | Name                  |
    ---------------------------------------------------------------------------
    |   0 | SELECT STATEMENT                          |                       |
    |   1 |  NESTED LOOPS                             |                       |
    |   2 |   NESTED LOOPS                            |                       |
    |   3 |    VIEW                                   |                       |
    |*  4 |     VIEW                                  |                       |
    |*  5 |      WINDOW SORT PUSHED RANK              |                       |
    |   6 |       NESTED LOOPS                        |                       |
    |   7 |        VIEW                               | VW_NSO_1              |
    |   8 |         HASH UNIQUE                       |                       |
    |   9 |          UNION-ALL                        |                       |
    |* 10 |           TABLE ACCESS BY INDEX ROWID     | SERVICE               |
    |* 11 |            INDEX RANGE SCAN (MULTI VALUE) | IX_SVC_REL_CHAR_NAME  |
    |  12 |           NESTED LOOPS                    |                       |
    |* 13 |            TABLE ACCESS BY INDEX ROWID    | SERVICE               |
    |* 14 |             INDEX RANGE SCAN (MULTI VALUE)| IX_SERVICE_CHAR_VALUE |
    |  15 |            TABLE ACCESS BY INDEX ROWID    | SERVICE               |
    |* 16 |             INDEX RANGE SCAN (MULTI VALUE)| IX_SVC_REL_ID         |
    |* 17 |        INDEX UNIQUE SCAN                  | SYS_C008729           |
    |* 18 |    INDEX UNIQUE SCAN                      | SYS_C008729           |
    |  19 |   TABLE ACCESS BY INDEX ROWID             | SERVICE               |
    ---------------------------------------------------------------------------
     
    Predicate Information (identified by operation id):
    ---------------------------------------------------
     
       4 - filter("from$_subquery$_008"."rowlimit_$$_rownumber"<=100 AND 
                  "from$_subquery$_008"."rowlimit_$$_rownumber">0)
       5 - filter(ROW_NUMBER() OVER ( ORDER BY "SERVICE"."ID")<=100)
      10 - filter(JSON_EXISTS2("S1"."PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT 
                  OSON , '$."serviceRelationship"."service"[*] ? 
                  (exists(@."serviceCharacteristic"[*] ? ((@."name" == $v0) && (@."value" 
                  == $v1))))' /* json_path_str  $.serviceRelationship.service[*]?(exists(@
                  .serviceCharacteristic[*]?((@.name.string() == $v0) && 
                  (@.value.string() == $v1))))  */  PASSING :Q0E_0 AS "v0" , :Q0E_1 AS 
                  "v1" FALSE ON ERROR TYPE(LAX) )=1)
      11 - access(JSON_QUERY("PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT OSON , 
                  '$.serviceRelationship.service.serviceCharacteristic.name.string()' 
                  RETURNING VARCHAR2(4000) ASIS  WITHOUT ARRAY WRAPPER ERROR ON ERROR 
                  NULL ON EMPTY NULL ON MISMATCH TYPE(LAX)  MULTIVALUE)=:Q0E_0)
      13 - filter(JSON_EXISTS2("T2"."PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT 
                  OSON , '$."serviceCharacteristic"[*] ? ((@."name" == $v0) && (@."value" 
                  == $v1))' /* json_path_str  $.serviceCharacteristic[*]?((@.name.string()
                   == $v0) && (@.value.string() == $v1))  */  PASSING :Q0T_0 AS "v0" , 
                  :Q0T_1 AS "v1" FALSE ON ERROR TYPE(LAX) )=1)
      14 - access(JSON_QUERY("PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT OSON , 
                  '$.serviceCharacteristic.value.string()' RETURNING VARCHAR2(4000) ASIS  
                  WITHOUT ARRAY WRAPPER ERROR ON ERROR NULL ON EMPTY NULL ON MISMATCH 
                  TYPE(LAX)  MULTIVALUE)=:Q0T_1)
      16 - access(JSON_QUERY("PAYLOAD" /*+ LOB_BY_VALUE */  FORMAT OSON , 
                  '$.serviceRelationship.service.id.string()' RETURNING VARCHAR2(4000) 
                  ASIS  WITHOUT ARRAY WRAPPER ERROR ON ERROR NULL ON EMPTY NULL ON 
                  MISMATCH TYPE(LAX)  MULTIVALUE)=JSON_VALUE("T2"."PAYLOAD" /*+ 
                  LOB_BY_VALUE */  FORMAT OSON , '$.id' RETURNING VARCHAR2(4000) NULL ON 
                  ERROR TYPE(LAX) ))
      17 - access("SERVICE"."ID"="ID")
      18 - access("SERVICE"."ID"="PAGE"."ID")

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

* The Bruno collection (`tests/TMFC008`) is not part of this report (Bruno CLI not installed in the devcontainer).

## Reproduce

```bash
docker compose up -d db oracle
export PG=postgresql+asyncpg://app:secret@localhost:5432/app_db
export ORA='oracle+oracledb_async://app:secret@localhost:1521/?service_name=FREEPDB1'
DATABASE_URL=$PG alembic upgrade head && DATABASE_URL=$ORA alembic upgrade head
DATABASE_URL=$PG  uvicorn openapi_server.main:app --port 8001 &
DATABASE_URL=$ORA uvicorn openapi_server.main:app --port 8002 &
DATABASE_URL=${PG/+asyncpg/} python scripts/seed.py --count 50000 --truncate   # data for the performance measurement
DATABASE_URL=${ORA/_async/} python scripts/seed.py --count 50000 --truncate
python scripts/test_report.py --target "PostgreSQL|http://127.0.0.1:8001|$PG" --target "Oracle|http://127.0.0.1:8002|$ORA"
```
