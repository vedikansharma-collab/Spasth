"""create_policy_chunks_pgvector

Revision ID: b69ddad20737
Revises: 735338f5328a
Create Date: 2026-10-11 07:16:23.313858

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy


# revision identifiers, used by Alembic.
revision: str = 'b69ddad20737'
down_revision: Union[str, Sequence[str], None] = '735338f5328a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Ensure pgvector extension exists
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    op.create_table(
        'policy_chunks',
        sa.Column('chunk_id', sa.String(length=64), nullable=False),
        sa.Column('policy_id', sa.String(length=64), nullable=False),
        sa.Column('document_id', sa.String(length=64), nullable=False),
        sa.Column('section', sa.String(length=255), nullable=True),
        sa.Column('clause', sa.String(length=255), nullable=True),
        sa.Column('rule_type', sa.String(length=64), nullable=True),
        sa.Column('subtype', sa.String(length=64), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('source_page', sa.Integer(), nullable=False),
        sa.Column('source_text', sa.Text(), nullable=False),
        sa.Column('bbox', sa.Text(), nullable=True),
        sa.Column('embedding', pgvector.sqlalchemy.Vector(768), nullable=True),
        sa.Column('created_at', sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('chunk_id')
    )
    op.create_index(op.f('ix_policy_chunks_policy_id'), 'policy_chunks', ['policy_id'], unique=False)
    op.create_index('idx_policy_chunks_policy_page', 'policy_chunks', ['policy_id', 'source_page'], unique=False)
    op.create_index(
        'idx_policy_chunks_embedding',
        'policy_chunks',
        ['embedding'],
        unique=False,
        postgresql_using='hnsw',
        postgresql_ops={'embedding': 'vector_cosine_ops'}
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_policy_chunks_embedding', table_name='policy_chunks')
    op.drop_index('idx_policy_chunks_policy_page', table_name='policy_chunks')
    op.drop_index(op.f('ix_policy_chunks_policy_id'), table_name='policy_chunks')
    op.drop_table('policy_chunks')
