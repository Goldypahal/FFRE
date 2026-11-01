"""add_token_hash_to_tenant_invitations

Revision ID: d5f6a7b8c9d0
Revises: 89a1b2c3d4e5
Create Date: 2026-10-31 12:00:00.000000

"""
import hashlib
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = '89a1b2c3d4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Add token_hash to tenant_invitations, backfill legacy tokens, and scrub plaintext."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()

    if 'tenant_invitations' not in tables:
        op.create_table(
            'tenant_invitations',
            sa.Column('invitation_id', sa.String(length=64), primary_key=True),
            sa.Column('token', sa.String(length=128), nullable=True),
            sa.Column('token_hash', sa.String(length=64), nullable=False),
            sa.Column('tenant_id', sa.String(length=50), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=True),
            sa.Column('role', sa.String(length=50), nullable=False, server_default='investigator'),
            sa.Column('created_by', sa.String(length=100), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('is_used', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('used_at', sa.DateTime(), nullable=True),
            sa.Column('used_by', sa.String(length=255), nullable=True),
        )
        op.create_index('ix_tenant_invitations_token_hash', 'tenant_invitations', ['token_hash'], unique=True)
        op.create_index('ix_tenant_invitations_tenant_id', 'tenant_invitations', ['tenant_id'], unique=False)
        op.create_index('ix_tenant_invitations_is_used', 'tenant_invitations', ['is_used'], unique=False)
    else:
        existing_cols = [c['name'] for c in insp.get_columns('tenant_invitations')]
        if 'token_hash' not in existing_cols:
            with op.batch_alter_table('tenant_invitations') as batch_op:
                batch_op.add_column(sa.Column('token_hash', sa.String(length=64), nullable=True))

        # Backfill existing legacy plaintext tokens into SHA-256 token_hash
        try:
            inv_table = sa.table(
                'tenant_invitations',
                sa.column('invitation_id', sa.String),
                sa.column('token', sa.String),
                sa.column('token_hash', sa.String)
            )
            rows = bind.execute(
                sa.select(inv_table.c.invitation_id, inv_table.c.token)
                .where(sa.or_(inv_table.c.token_hash.is_(None), inv_table.c.token_hash == ''))
            ).fetchall()
            for r in rows:
                inv_id, raw_tok = r[0], r[1]
                if raw_tok:
                    h = hashlib.sha256(raw_tok.encode('utf-8')).hexdigest()
                    bind.execute(
                        inv_table.update()
                        .where(inv_table.c.invitation_id == inv_id)
                        .values(token_hash=h, token=None)
                    )
            # Scrub all remaining plaintext tokens completely
            bind.execute(
                inv_table.update()
                .where(inv_table.c.token.isnot(None))
                .values(token=None)
            )
        except Exception:
            pass

        with op.batch_alter_table('tenant_invitations') as batch_op:
            try:
                batch_op.create_index('ix_tenant_invitations_token_hash', ['token_hash'], unique=True)
            except Exception:
                pass


def downgrade() -> None:
    """Downgrade schema: Remove token_hash from tenant_invitations."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()

    if 'tenant_invitations' in tables:
        with op.batch_alter_table('tenant_invitations') as batch_op:
            try:
                batch_op.drop_index('ix_tenant_invitations_token_hash')
            except Exception:
                pass
            try:
                batch_op.drop_column('token_hash')
            except Exception:
                pass
