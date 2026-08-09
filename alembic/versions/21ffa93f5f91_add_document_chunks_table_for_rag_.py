"""Add document_chunks table for RAG embeddings

Revision ID: 21ffa93f5f91
Revises: 35f2f7b2f548
Create Date: 2026-08-08 17:38:47.835111

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '21ffa93f5f91'
down_revision: Union[str, Sequence[str], None] = '35f2f7b2f548'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('document_chunks',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('job_id', sa.Uuid(), nullable=False),
    sa.Column('batch_id', sa.Uuid(), nullable=True),
    sa.Column('project_id', sa.Uuid(), nullable=True),
    sa.Column('page_id', sa.Uuid(), nullable=False),
    sa.Column('url', sa.String(length=2048), nullable=False),
    sa.Column('page_title', sa.String(length=512), nullable=True),
    sa.Column('heading_path', sa.String(length=512), nullable=True),
    sa.Column('chunk_index', sa.Integer(), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('char_count', sa.Integer(), nullable=False),
    sa.Column('embedding', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['batch_id'], ['batch_jobs.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['job_id'], ['crawl_jobs.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['page_id'], ['extracted_pages.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('document_chunks', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_document_chunks_batch_id'), ['batch_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_document_chunks_job_id'), ['job_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_document_chunks_page_id'), ['page_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_document_chunks_project_id'), ['project_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('document_chunks', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_document_chunks_project_id'))
        batch_op.drop_index(batch_op.f('ix_document_chunks_page_id'))
        batch_op.drop_index(batch_op.f('ix_document_chunks_job_id'))
        batch_op.drop_index(batch_op.f('ix_document_chunks_batch_id'))

    op.drop_table('document_chunks')
