"""add_transaction_ingestion_columns

Revision ID: 89a1b2c3d4e5
Revises: 338f66162493
Create Date: 2026-10-22 16:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '89a1b2c3d4e5'
down_revision: Union[str, Sequence[str], None] = '338f66162493'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Add counterparty, channel, ip_address, device_ref to transaction."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing_cols = [c["name"] for c in insp.get_columns("transaction")]

    with op.batch_alter_table("transaction") as batch_op:
        if "counterparty" not in existing_cols:
            batch_op.add_column(sa.Column("counterparty", sa.String(length=255), nullable=True))
        if "channel" not in existing_cols:
            batch_op.add_column(sa.Column("channel", sa.String(length=50), nullable=True))
        if "ip_address" not in existing_cols:
            batch_op.add_column(sa.Column("ip_address", sa.String(length=45), nullable=True))
        if "device_ref" not in existing_cols:
            batch_op.add_column(sa.Column("device_ref", sa.String(length=100), nullable=True))


def downgrade() -> None:
    """Downgrade schema: Remove counterparty, channel, ip_address, device_ref from transaction."""
    with op.batch_alter_table("transaction") as batch_op:
        for col in ["counterparty", "channel", "ip_address", "device_ref"]:
            try:
                batch_op.drop_column(col)
            except Exception:
                pass
