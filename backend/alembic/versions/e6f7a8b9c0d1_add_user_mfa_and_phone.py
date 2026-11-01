"""add_user_mfa_and_phone

Revision ID: e6f7a8b9c0d1
Revises: d5f6a7b8c9d0
Create Date: 2026-11-01 11:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6f7a8b9c0d1'
down_revision: Union[str, Sequence[str], None] = 'd5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Add phone_number and mfa_enabled to users."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing_cols = [c["name"] for c in insp.get_columns("users")]

    with op.batch_alter_table("users") as batch_op:
        if "phone_number" not in existing_cols:
            batch_op.add_column(sa.Column("phone_number", sa.String(length=255), nullable=True))
        if "mfa_enabled" not in existing_cols:
            batch_op.add_column(sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")))


def downgrade() -> None:
    """Downgrade schema: Remove phone_number and mfa_enabled from users."""
    with op.batch_alter_table("users") as batch_op:
        for col in ["phone_number", "mfa_enabled"]:
            try:
                batch_op.drop_column(col)
            except Exception:
                pass
