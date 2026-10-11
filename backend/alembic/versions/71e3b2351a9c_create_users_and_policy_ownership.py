"""create users and policy ownership

Revision ID: 71e3b2351a9c
Revises: b69ddad20737
Create Date: 2026-10-11 07:48:53.950110

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '71e3b2351a9c'
down_revision: Union[str, Sequence[str], None] = 'b69ddad20737'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=32), nullable=False, server_default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_role', 'users', ['role'])

    # 2. Add owner_id and is_public to policies table
    op.add_column('policies', sa.Column('owner_id', sa.String(length=64), nullable=True))
    op.add_column('policies', sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'))

    op.create_foreign_key(
        'fk_policies_owner_id_users',
        'policies',
        'users',
        ['owner_id'],
        ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_policies_owner_id', 'policies', ['owner_id'])
    op.create_index('ix_policies_is_public', 'policies', ['is_public'])

    # 3. Mark canonical demo policy 945c5b0b-c71e-4e0b-abf0-ed0211b93052 as explicitly public
    op.execute("UPDATE policies SET is_public = TRUE WHERE id = '945c5b0b-c71e-4e0b-abf0-ed0211b93052'")


def downgrade() -> None:
    op.drop_index('ix_policies_is_public', table_name='policies')
    op.drop_index('ix_policies_owner_id', table_name='policies')
    op.drop_constraint('fk_policies_owner_id_users', 'policies', type_='foreignkey')
    op.drop_column('policies', 'is_public')
    op.drop_column('policies', 'owner_id')

    op.drop_index('ix_users_role', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
