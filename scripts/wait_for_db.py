"""Block until DATABASE_URL accepts connections (Oracle needs a while on first start)."""
import asyncio
import os
import sys
import time

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def main(timeout: float) -> int:
    engine = create_async_engine(os.environ["DATABASE_URL"])
    probe = "SELECT 1 FROM dual" if engine.dialect.name == "oracle" else "SELECT 1"
    deadline = time.monotonic() + timeout
    try:
        while True:
            try:
                async with engine.connect() as conn:
                    await conn.execute(text(probe))
                print(f"Database ({engine.dialect.name}) is ready.")
                return 0
            except Exception as exc:  # noqa: BLE001 - any connect error means "not yet"
                if time.monotonic() > deadline:
                    print(f"Database not reachable: {exc}", file=sys.stderr)
                    return 1
                print(f"Waiting for database... ({type(exc).__name__})")
                await asyncio.sleep(3)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    sys.exit(asyncio.run(main(float(os.environ.get("DB_WAIT_TIMEOUT", "300")))))
