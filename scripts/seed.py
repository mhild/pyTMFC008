"""Bulk-load generated services into the database given by DATABASE_URL.

    DATABASE_URL=... python scripts/seed.py --count 1000000 [--start 0] [--truncate]

Bypasses the API and uses the native bulk paths of the drivers
(PostgreSQL: COPY via asyncpg, Oracle: executemany via python-oracledb),
then refreshes optimizer statistics.
"""
import argparse
import asyncio
import json
import os
import sys
import time

from sqlalchemy.engine import make_url

sys.path.insert(0, os.path.dirname(__file__))
from datagen import make_service, service_id  # noqa: E402

BATCH = 5_000


def batches(start: int, count: int):
    for lo in range(start, start + count, BATCH):
        yield range(lo, min(lo + BATCH, start + count))


async def seed_postgres(url, start, count, truncate):
    import asyncpg

    conn = await asyncpg.connect(
        user=url.username, password=url.password, host=url.host, port=url.port or 5432, database=url.database
    )
    try:
        if truncate:
            await conn.execute("TRUNCATE service")
        for rng in batches(start, count):
            records = [(service_id(i), json.dumps(make_service(i))) for i in rng]
            await conn.copy_records_to_table("service", records=records, columns=["id", "payload"])
            print(f"  {rng.stop - start:>9} rows", end="\r")
        await conn.execute("ANALYZE service")
    finally:
        await conn.close()


def seed_oracle(url, start, count, truncate):
    import oracledb

    dsn = f"{url.host}:{url.port or 1521}/{url.query.get('service_name', url.database)}"
    with oracledb.connect(user=url.username, password=url.password, dsn=dsn) as conn:
        cur = conn.cursor()
        if truncate:
            cur.execute("TRUNCATE TABLE service")
        cur.setinputsizes(None, oracledb.DB_TYPE_JSON)  # bind dicts as native OSON
        for rng in batches(start, count):
            cur.executemany(
                "INSERT INTO service (id, payload) VALUES (:1, :2)",
                [(service_id(i).hex, make_service(i)) for i in rng],
            )
            conn.commit()
            print(f"  {rng.stop - start:>9} rows", end="\r")
        cur.execute("BEGIN DBMS_STATS.GATHER_TABLE_STATS(USER, 'SERVICE', cascade => TRUE); END;")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--count", type=int, default=1_000_000)
    parser.add_argument("--start", type=int, default=0, help="first service number (to append to existing data)")
    parser.add_argument("--truncate", action="store_true", help="delete all services first")
    args = parser.parse_args()

    url = make_url(os.environ["DATABASE_URL"])
    t0 = time.perf_counter()
    if url.get_backend_name() == "postgresql":
        asyncio.run(seed_postgres(url, args.start, args.count, args.truncate))
    elif url.get_backend_name() == "oracle":
        seed_oracle(url, args.start, args.count, args.truncate)
    else:
        sys.exit(f"Unsupported backend {url.get_backend_name()}")
    elapsed = time.perf_counter() - t0
    print(f"Inserted {args.count} services in {elapsed:.1f}s ({args.count / elapsed:,.0f} rows/s)")


if __name__ == "__main__":
    main()
