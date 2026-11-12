"""widen_encrypted_columns_and_home_country

Revision ID: f8a9b0c1d2e3
Revises: e7f8a9b0c1d2
Create Date: 2026-11-12 10:00:00.000000

Mirrors internal migrations 012 and 013:
  * encrypted columns outgrow VARCHAR(255), so they become TEXT;
  * customer.home_country is added for the geolocation rule;
  * evidence and audit rows written by the pipeline are re-labelled with their investigation's tenant.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8a9b0c1d2e3'
down_revision: Union[str, Sequence[str], None] = 'e7f8a9b0c1d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ENCRYPTED = (
    ("users", "name"), ("users", "email"), ("users", "phone_number"),
    ("customer", "name"), ("device", "fingerprint"),
)


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()

    if "customer" in tables and "home_country" not in [c["name"] for c in insp.get_columns("customer")]:
        op.add_column("customer", sa.Column("home_country", sa.String(length=64), nullable=True))

    if bind.dialect.name != "sqlite":  # SQLite does not enforce VARCHAR lengths
        for table, column in _ENCRYPTED:
            if table in tables and column in [c["name"] for c in insp.get_columns(table)]:
                op.alter_column(table, column, type_=sa.Text(), existing_nullable=True)

    if "investigation" in tables:
        for table in ("evidence", "audit_log"):
            if table in tables and "tenant_id" in [c["name"] for c in insp.get_columns(table)]:
                op.execute(sa.text(
                    f"UPDATE {table} SET tenant_id = ("
                    f"SELECT i.tenant_id FROM investigation i WHERE i.investigation_id = {table}.investigation_id) "
                    f"WHERE investigation_id IS NOT NULL AND EXISTS ("
                    f"SELECT 1 FROM investigation i WHERE i.investigation_id = {table}.investigation_id "
                    f"AND i.tenant_id IS NOT NULL AND i.tenant_id <> {table}.tenant_id)"
                ))


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if "customer" in insp.get_table_names() and "home_country" in [c["name"] for c in insp.get_columns("customer")]:
        with op.batch_alter_table("customer") as batch:
            batch.drop_column("home_country")
    # Columns are left as TEXT: narrowing them could truncate encrypted values.
