"""backfill_and_enforce_invitation_token_hash

Revision ID: e7f8a9b0c1d2
Revises: d5f6a7b8c9d0
Create Date: 2026-11-01 15:30:00.000000

"""
import hashlib
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7f8a9b0c1d2'
down_revision: Union[str, Sequence[str], None] = 'e6f7a8b9c0d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Backfill legacy invitation hashes, verify zero unhashed records, scrub plaintext, and enforce NOT NULL."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()

    if 'tenant_invitations' in tables:
        inv_table = sa.table(
            'tenant_invitations',
            sa.column('invitation_id', sa.String),
            sa.column('token', sa.String),
            sa.column('token_hash', sa.String)
        )

        # 1. Backfill token_hash for all existing rows with plaintext token
        unhashed = bind.execute(
            sa.select(inv_table.c.invitation_id, inv_table.c.token)
            .where(sa.or_(inv_table.c.token_hash.is_(None), inv_table.c.token_hash == ''))
        ).fetchall()
        for row in unhashed:
            inv_id, raw_token = row[0], row[1]
            if raw_token:
                th = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
                bind.execute(
                    inv_table.update()
                    .where(inv_table.c.invitation_id == inv_id)
                    .values(token_hash=th, token=None)
                )

        # 2. Strict Verification: ensure no un-hashed records remain
        remaining_unhashed = bind.execute(
            sa.select(sa.func.count())
            .select_from(inv_table)
            .where(sa.or_(inv_table.c.token_hash.is_(None), inv_table.c.token_hash == ''))
        ).scalar()
        if remaining_unhashed > 0:
            raise RuntimeError(f"Migration failure: {remaining_unhashed} invitation records remain unhashed!")

        # 3. Scrub all remaining plaintext tokens at rest
        bind.execute(
            inv_table.update()
            .where(inv_table.c.token.isnot(None))
            .values(token=None)
        )

        # 4. Enforce NOT NULL on token_hash. Batch operations are deferred to the
        #    context exit, so errors surface there and abort the revision.
        with op.batch_alter_table('tenant_invitations') as batch_op:
            batch_op.alter_column('token_hash', existing_type=sa.String(length=64), nullable=False)

        # 5. Ensure a unique index on token_hash. Revision d5f6a7b8c9d0 normally
        #    creates it already; only create it when no unique index/constraint
        #    covers the column, and never swallow a creation failure.
        insp = sa.inspect(bind)
        has_unique = any(
            ix.get('unique') and list(ix.get('column_names') or []) == ['token_hash']
            for ix in insp.get_indexes('tenant_invitations')
        ) or any(
            list(uc.get('column_names') or []) == ['token_hash']
            for uc in insp.get_unique_constraints('tenant_invitations')
        )
        if not has_unique:
            existing_names = {ix['name'] for ix in insp.get_indexes('tenant_invitations')}
            if 'ix_tenant_invitations_token_hash' in existing_names:
                # A non-unique index holds the canonical name; replace it.
                op.drop_index('ix_tenant_invitations_token_hash', table_name='tenant_invitations')
            op.create_index('ix_tenant_invitations_token_hash', 'tenant_invitations', ['token_hash'], unique=True)

        # 6. Verify the guarantees with the same check the internal engine uses.
        from migrations import verify_invitation_token_hash_constraints
        verify_invitation_token_hash_constraints(bind)


def downgrade() -> None:
    """Downgrade schema: allow nullable token_hash."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()

    if 'tenant_invitations' in tables:
        with op.batch_alter_table('tenant_invitations') as batch_op:
            batch_op.alter_column('token_hash', nullable=True)

