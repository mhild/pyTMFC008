"""Query benchmark: latency over the HTTP API + execution plan of the generated SQL.

    DATABASE_URL=... python scripts/bench.py --base-url http://127.0.0.1:8080 [--runs 20] [--plans]

Expects data loaded with scripts/seed.py (uses its deterministic MAC addresses/names).
DATABASE_URL is only needed for --plans (EXPLAIN against the database).
"""
import argparse
import asyncio
import os
import statistics
import sys
import time

import httpx

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from datagen import mac_for  # noqa: E402

from openapi_server.services.service import list_statements  # noqa: E402


def queries(n: int):
    i = n // 2 + 7
    mac = mac_for(i)
    return [
        ("mac (JSONPath filter, name && value)",
         {"filter": f"$.serviceCharacteristic[?(@.name=='mac' && @.value=='{mac}')]"}),
        ("mac (attribute filter)", {"serviceCharacteristic.value": mac}),
        ("mac, no match", {"filter": "$.serviceCharacteristic[?(@.name=='mac' && @.value=='ff:ff:ff:ff:ff:ff')]"}),
        ("A related to B with mac (join)",
         {"serviceRelationship.service.serviceCharacteristic.name": "mac",
          "serviceRelationship.service.serviceCharacteristic.value": mac_for(i - i % 2)}),
        ("related to B with mac, no match (join)",
         {"serviceRelationship.service.serviceCharacteristic.name": "mac",
          "serviceRelationship.service.serviceCharacteristic.value": "ff:ff:ff:ff:ff:ff"}),
        ("referenced service state (join, ~3%)",
         {"serviceType": "Cloud", "serviceRelationship.service.state": "suspended"}),
        ("rare relatedParty name", {"relatedParty.partyOrPartyRole.name": "Customer 00001"}),
        ("serviceType + state (~3%)", {"serviceType": "Cloud", "state": "suspended"}),
        ("range startDate.gte (no index)", {"startDate.gte": "2025-06-01"}),
        ("no filter, deep page", {"offset": str(max(n - 200, 0))}),
    ]


def bench_http(base_url: str, n: int, runs: int):
    rows = []
    with httpx.Client(base_url=base_url, timeout=120) as client:
        for label, params in queries(n):
            params = {"limit": "100", **params}
            client.get("/service", params=params)  # warm-up
            times, total = [], None
            for _ in range(runs):
                t0 = time.perf_counter()
                r = client.get("/service", params=params)
                times.append((time.perf_counter() - t0) * 1000)
                r.raise_for_status()
                total = r.headers.get("X-Total-Count")
            times.sort()
            p95 = times[min(len(times) - 1, int(round(0.95 * len(times))) - 1)]
            rows.append((label, total, statistics.median(times), p95))
    print(f"\n{'query':40} {'matches':>8} {'p50 ms':>8} {'p95 ms':>8}")
    for label, total, p50, p95 in rows:
        print(f"{label:40} {total:>8} {p50:8.1f} {p95:8.1f}")


async def explain(n: int):
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(os.environ["DATABASE_URL"])
    dialect = engine.dialect
    async with engine.connect() as conn:
        for label, params in queries(n):
            offset = int(params.pop("offset", 0))
            _, stmt, joins = list_statements(params.items(), dialect.name, offset, 100)
            compiled = stmt.compile(dialect=dialect, compile_kwargs={"render_postcompile": True})
            print(f"\n=== {label}")
            if dialect.name == "postgresql":
                parallel = "0" if joins else "DEFAULT"  # as the API does (service.disable_parallel_query)
                await conn.exec_driver_sql(f"SET max_parallel_workers_per_gather = {parallel}")
                args = tuple(compiled.params[name] for name in compiled.positiontup)
                result = await conn.exec_driver_sql("EXPLAIN (ANALYZE, COSTS OFF, TIMING OFF) " + compiled.string, args)
            else:
                await conn.exec_driver_sql("EXPLAIN PLAN FOR " + compiled.string, dict(compiled.params))
                result = await conn.execute(
                    text("SELECT plan_table_output FROM TABLE(DBMS_XPLAN.DISPLAY(NULL, NULL, 'BASIC +PREDICATE'))")
                )
            for (line,) in result:
                print("   ", line)
    await engine.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--count", type=int, help="number of seeded services (default: X-Total-Count of the API)")
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--plans", action="store_true", help="also print execution plans (needs DATABASE_URL)")
    args = parser.parse_args()

    n = args.count or int(httpx.get(f"{args.base_url}/service", params={"limit": 1}).headers["X-Total-Count"])
    print(f"{args.base_url}: {n} services")
    bench_http(args.base_url, n, args.runs)
    if args.plans:
        asyncio.run(explain(n))


if __name__ == "__main__":
    main()
