"""add_reference_indexes

Oracle: multivalue indexes
* on the ids of service references, to find the services referencing a given
  service (filters through serviceRelationship.service and supportingService);
* on the searchable attributes of services embedded *by value* in a reference
  (ServiceRefOrValue). They stay nearly empty as long as references are used,
  but keep the "embedded value" branch of a reference filter from scanning the table.
PostgreSQL needs none: the GIN index covers all of it.

Revision ID: a4f1c3d2e8b7
Revises: 7c2e5b1a9f40
Create Date: 2026-10-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a4f1c3d2e8b7'
down_revision: Union[str, Sequence[str], None] = '7c2e5b1a9f40'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# reference -> index name prefix
REFERENCES = {"serviceRelationship.service": "ix_svc_rel", "supportingService": "ix_svc_sup"}
# same attributes as indexed on the service itself (revision 7c2e5b1a9f40)
EMBEDDED_ATTRIBUTES = {
    "type": "serviceType",
    "state": "state",
    "name": "name",
    "char_name": "serviceCharacteristic.name",
    "char_value": "serviceCharacteristic.value",
    "party_name": "relatedParty.partyOrPartyRole.name",
}


def _oracle_indexes():
    for ref, prefix in REFERENCES.items():
        yield f"{prefix}_id", f"{ref}.id"
        for suffix, path in EMBEDDED_ATTRIBUTES.items():
            yield f"{prefix}_{suffix}", f"{ref}.{path}"


def upgrade() -> None:
    """Upgrade schema."""
    if op.get_bind().dialect.name == "oracle":
        for name, path in _oracle_indexes():
            op.execute(f"CREATE MULTIVALUE INDEX {name} ON service s (s.payload.{path}.string())")


def downgrade() -> None:
    """Downgrade schema."""
    if op.get_bind().dialect.name == "oracle":
        for name, _ in _oracle_indexes():
            op.execute(f"DROP INDEX {name}")
