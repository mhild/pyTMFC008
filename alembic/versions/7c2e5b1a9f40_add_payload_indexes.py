"""add_payload_indexes

PostgreSQL: one GIN index (jsonb_path_ops) serves every `payload @? jsonpath`
            equality filter, whatever attribute it addresses.
Oracle:     multivalue indexes (23ai) on the attributes typically searched;
            JSON_EXISTS filters on these paths can use them. If Oracle Text
            is installed (not in the -slim images) a JSON search index is
            added as well, which covers arbitrary paths like the GIN index.

Revision ID: 7c2e5b1a9f40
Revises: d31a2afdf41d
Create Date: 2026-10-23 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c2e5b1a9f40'
down_revision: Union[str, Sequence[str], None] = 'd31a2afdf41d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# index name -> JSON path (simple dot notation) of the indexed string values
ORACLE_MULTIVALUE_INDEXES = {
    "ix_service_type": "serviceType",
    "ix_service_state": "state",
    "ix_service_name": "name",
    "ix_service_char_name": "serviceCharacteristic.name",
    "ix_service_char_value": "serviceCharacteristic.value",
    "ix_service_party_name": "relatedParty.partyOrPartyRole.name",
}


def _oracle_text_installed() -> bool:
    return op.get_bind().execute(
        sa.text("SELECT COUNT(*) FROM all_users WHERE username = 'CTXSYS'")
    ).scalar() > 0


def upgrade() -> None:
    """Upgrade schema."""
    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        op.execute("CREATE INDEX ix_service_payload_gin ON service USING GIN (payload jsonb_path_ops)")
    elif dialect == "oracle":
        for name, path in ORACLE_MULTIVALUE_INDEXES.items():
            op.execute(f"CREATE MULTIVALUE INDEX {name} ON service s (s.payload.{path}.string())")
        if _oracle_text_installed():
            op.execute("CREATE SEARCH INDEX ix_service_payload_sidx ON service (payload) FOR JSON")


def downgrade() -> None:
    """Downgrade schema."""
    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        op.execute("DROP INDEX ix_service_payload_gin")
    elif dialect == "oracle":
        for name in ORACLE_MULTIVALUE_INDEXES:
            op.execute(f"DROP INDEX {name}")
        if op.get_bind().execute(
            sa.text("SELECT COUNT(*) FROM user_indexes WHERE index_name = 'IX_SERVICE_PAYLOAD_SIDX'")
        ).scalar():
            op.execute("DROP INDEX ix_service_payload_sidx")
