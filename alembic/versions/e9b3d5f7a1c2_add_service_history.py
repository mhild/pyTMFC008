"""add_service_history

Revision history (HISTORY_ENABLED, see openapi_server/services/history.py):
* service.revision / service.rev_start: revision of the current document and when it became current;
  only maintained while history is enabled.
* service_history: the earlier revisions of a service, same document, plus the period of validity.
  Searched with includeHistory=true, so it gets the indexes on the service's own attributes (not on
  the ones below references: filters through references are not supported on history).
  PostgreSQL: GIN index. Oracle: multivalue indexes and the `search` shadow column + trigger as on `service`.

The tables and columns are always created; the setting only decides whether they are written.

Revision ID: e9b3d5f7a1c2
Revises: c5d7e9f1a2b4
Create Date: 2026-10-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from openapi_server.database.models import JsonDocument
from openapi_server.database.oracle_search import search_document


# revision identifiers, used by Alembic.
revision: str = 'e9b3d5f7a1c2'
down_revision: Union[str, Sequence[str], None] = 'c5d7e9f1a2b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# index name -> (column, JSON path); same attributes as on `service` (revision 7c2e5b1a9f40)
ORACLE_INDEXES = {
    "ix_hist_type": ("payload", "serviceType"),
    "ix_hist_state": ("payload", "state"),
    "ix_hist_name": ("payload", "name"),
    "ix_hist_char_name": ("payload", "serviceCharacteristic.name"),
    "ix_hist_char_value": ("search", "serviceCharacteristic.value"),
    "ix_hist_party_name": ("payload", "relatedParty.partyOrPartyRole.name"),
}


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('service', sa.Column('revision', sa.Integer(), nullable=True))
    op.add_column('service', sa.Column('rev_start', sa.TIMESTAMP(), nullable=True))
    op.create_table('service_history',
    sa.Column('id', sa.Uuid(), nullable=False),  # uuid (PostgreSQL) / CHAR(32) (Oracle)
    sa.Column('revision', sa.Integer(), nullable=False),
    sa.Column('payload', JsonDocument(), nullable=False),  # JSONB (PostgreSQL) / JSON (Oracle)
    sa.Column('rev_start', sa.TIMESTAMP(), nullable=True),
    sa.Column('rev_end', sa.TIMESTAMP(), nullable=False),
    sa.Column('operation', sa.String(length=10), nullable=False),
    sa.PrimaryKeyConstraint('id', 'revision')
    )
    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        op.execute("CREATE INDEX ix_hist_payload_gin ON service_history USING GIN (payload jsonb_path_ops)")
    elif dialect == "oracle":
        op.execute("ALTER TABLE service_history ADD (search JSON)")
        op.get_bind().exec_driver_sql(
            "CREATE OR REPLACE TRIGGER service_history_search BEFORE INSERT OR UPDATE OF payload ON service_history\n"
            f"FOR EACH ROW\nBEGIN\n  SELECT {search_document(':new.payload')} INTO :new.search FROM dual;\nEND;"
        )
        for name, (column, path) in ORACLE_INDEXES.items():
            op.execute(f"CREATE MULTIVALUE INDEX {name} ON service_history h (h.{column}.{path}.string())")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('service_history')  # drops its indexes and trigger
    op.drop_column('service', 'rev_start')
    op.drop_column('service', 'revision')
