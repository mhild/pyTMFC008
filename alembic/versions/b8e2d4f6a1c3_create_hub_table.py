"""create_hub_table

Event subscriptions (TMF630 hubs) for the TMF638 notifications.

Revision ID: b8e2d4f6a1c3
Revises: a4f1c3d2e8b7
Create Date: 2026-10-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from openapi_server.database.models import JsonDocument

# revision identifiers, used by Alembic.
revision: str = 'b8e2d4f6a1c3'
down_revision: Union[str, Sequence[str], None] = 'a4f1c3d2e8b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('hub',
    sa.Column('id', sa.Uuid(), nullable=False),  # uuid (PostgreSQL) / CHAR(32) (Oracle)
    sa.Column('payload', JsonDocument(), nullable=False),  # JSONB (PostgreSQL) / JSON (Oracle)
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('hub')
