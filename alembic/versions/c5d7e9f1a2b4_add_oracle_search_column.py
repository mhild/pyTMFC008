"""add_oracle_search_column

Oracle multivalue indexes must be created with ERROR ON ERROR, so an index on
serviceCharacteristic.value rejects every service with an object-valued
characteristic (ObjectCharacteristic: ORA-40456 on insert).

The characteristic value indexes therefore move to a shadow column `search`:
a trigger fills it with the characteristic names and values of the service (and
of services embedded in its references), objects removed. The query renderer
checks a characteristic value condition on `search` (index) and on `payload`
(exact result). PostgreSQL needs none of this: its GIN index accepts any value.

Revision ID: c5d7e9f1a2b4
Revises: b8e2d4f6a1c3
Create Date: 2026-10-24 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool


# revision identifiers, used by Alembic.
revision: str = 'c5d7e9f1a2b4'
down_revision: Union[str, Sequence[str], None] = 'b8e2d4f6a1c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# characteristic arrays of the service and of services embedded by value in a reference:
# index name -> (path for the index, JSON path of the characteristics)
CHARACTERISTICS = {
    "ix_service_char_value": ("serviceCharacteristic", "$.serviceCharacteristic[*]"),
    "ix_svc_rel_char_value": (
        "serviceRelationship.service.serviceCharacteristic",
        "$.serviceRelationship[*].service.serviceCharacteristic[*]",
    ),
    "ix_svc_sup_char_value": ("supportingService.serviceCharacteristic", "$.supportingService[*].serviceCharacteristic[*]"),
}


BACKFILL_BATCH = 100000


def _search_document(column: str) -> str:
    """JSON_TRANSFORM of `column` into the search document."""
    paths = [json_path for _, json_path in CHARACTERISTICS.values()]
    keep = ", ".join(f"'{p}.{key}'" for p in paths for key in ("name", "value"))
    removes = []
    for p in paths:
        # objects and nested arrays inside an array value; the filter on the array type is needed,
        # in lax mode `value[*]` also addresses a scalar value itself
        removes.append(f"""REMOVE '{p}?(@.value.type() == "array").value[*]?(@.type() == "object" || @.type() == "array")' IGNORE ON MISSING""")
        removes.append(f"""REMOVE '{p}?(@.value.type() == "object").value' IGNORE ON MISSING""")
    return f"JSON_TRANSFORM({column}, KEEP {keep}, {', '.join(removes)} RETURNING JSON)"


def _backfill(bind) -> None:
    """Fill `search` of the existing services, BACKFILL_BATCH rows per connection.

    One UPDATE of 1M rows exceeds PGA_AGGREGATE_LIMIT on Oracle Free (ORA-04036), and so does a PL/SQL loop in one
    session: the PGA grows per session and COMMIT does not release it. A new connection per batch does.
    Resumable: only rows with `search IS NULL` are touched.
    """
    rows = bind.exec_driver_sql("SELECT COUNT(*) FROM service WHERE search IS NULL").scalar()
    # synchronous driver for the same database (the migration itself runs on the async one)
    url = bind.engine.url.set(drivername="oracle+oracledb")
    engine = create_engine(url, poolclass=NullPool)
    try:
        for _ in range(rows // BACKFILL_BATCH + 1):  # bounded: a NULL result would never leave the filter
            with engine.begin() as conn:
                updated = conn.exec_driver_sql(
                    f"UPDATE service SET search = {_search_document('payload')} "
                    f"WHERE search IS NULL AND ROWNUM <= {BACKFILL_BATCH}"
                ).rowcount
            if updated == 0:
                break
    finally:
        engine.dispose()


def upgrade() -> None:
    """Upgrade schema."""
    if op.get_bind().dialect.name != "oracle":
        return
    op.execute("ALTER TABLE service ADD (search JSON)")
    # JSON_TRANSFORM is not available in PL/SQL expressions, hence SELECT ... INTO;
    # sent to the driver as is, SQLAlchemy would take :new for a bind parameter
    op.get_bind().exec_driver_sql(
        "CREATE OR REPLACE TRIGGER service_search BEFORE INSERT OR UPDATE OF payload ON service FOR EACH ROW\n"
        f"BEGIN\n  SELECT {_search_document(':new.payload')} INTO :new.search FROM dual;\nEND;"
    )
    _backfill(op.get_bind())
    for name, (path, _) in CHARACTERISTICS.items():
        op.execute(f"DROP INDEX {name}")
        op.execute(f"CREATE MULTIVALUE INDEX {name} ON service s (s.search.{path}.value.string())")
    # without statistics on the new column the optimizer misjudges the reference joins (~100x slower)
    op.execute("BEGIN DBMS_STATS.GATHER_TABLE_STATS(USER, 'SERVICE', cascade => TRUE); END;")


def downgrade() -> None:
    """Downgrade schema (fails if services with object-valued characteristics exist)."""
    if op.get_bind().dialect.name != "oracle":
        return
    for name, (path, _) in CHARACTERISTICS.items():
        op.execute(f"DROP INDEX {name}")
        op.execute(f"CREATE MULTIVALUE INDEX {name} ON service s (s.payload.{path}.value.string())")
    op.execute("DROP TRIGGER service_search")
    op.execute("ALTER TABLE service DROP COLUMN search")
