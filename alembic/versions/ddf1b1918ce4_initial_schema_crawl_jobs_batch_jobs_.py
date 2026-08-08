"""Initial schema: crawl_jobs, batch_jobs, extracted_pages, links, images, statistics

Revision ID: ddf1b1918ce4
Revises: 
Create Date: 2026-08-08 15:22:03.078706

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ddf1b1918ce4'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Future pgvector Preparation for PostgreSQL (Version 4 RAG Readiness)
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 1. Table: batch_jobs
    op.create_table(
        'batch_jobs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'PARTIALLY_COMPLETED', 'FAILED', name='crawlstatus', native_enum=False), nullable=False),
        sa.Column('total_urls', sa.Integer(), nullable=False, server_default="0"),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True,
    )
    op.create_index('ix_batch_jobs_id', 'batch_jobs', ['id'], unique=False, if_not_exists=True)
    op.create_index('ix_batch_jobs_status', 'batch_jobs', ['status'], unique=False, if_not_exists=True)

    # 2. Table: crawl_jobs
    op.create_table(
        'crawl_jobs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('seed_url', sa.String(length=2048), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'COMPLETED', 'PARTIALLY_COMPLETED', 'FAILED', name='crawlstatus', native_enum=False), nullable=False),
        sa.Column('crawl_mode', sa.Enum('SINGLE', 'BATCH', name='crawlmode', native_enum=False), nullable=False, server_default="SINGLE"),
        sa.Column('batch_id', sa.Uuid(), nullable=True),
        sa.Column('max_depth', sa.Integer(), nullable=False, server_default="2"),
        sa.Column('max_pages', sa.Integer(), nullable=False, server_default="50"),
        sa.Column('render_js', sa.Boolean(), nullable=False, server_default="0"),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['batch_id'], ['batch_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True,
    )
    op.create_index('ix_crawl_jobs_id', 'crawl_jobs', ['id'], unique=False, if_not_exists=True)
    op.create_index('ix_crawl_jobs_seed_url', 'crawl_jobs', ['seed_url'], unique=False, if_not_exists=True)
    op.create_index('ix_crawl_jobs_status', 'crawl_jobs', ['status'], unique=False, if_not_exists=True)
    op.create_index('ix_crawl_jobs_crawl_mode', 'crawl_jobs', ['crawl_mode'], unique=False, if_not_exists=True)
    op.create_index('ix_crawl_jobs_batch_id', 'crawl_jobs', ['batch_id'], unique=False, if_not_exists=True)

    # 3. Table: extracted_pages
    op.create_table(
        'extracted_pages',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('job_id', sa.Uuid(), nullable=False),
        sa.Column('url', sa.String(length=2048), nullable=False),
        sa.Column('normalized_url', sa.String(length=2048), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=False, server_default="200"),
        sa.Column('depth', sa.Integer(), nullable=False, server_default="0"),
        sa.Column('title', sa.String(length=1024), nullable=True),
        sa.Column('meta_description', sa.Text(), nullable=True),
        sa.Column('headings', sa.JSON(), nullable=False),
        sa.Column('paragraphs', sa.JSON(), nullable=False),
        sa.Column('lists', sa.JSON(), nullable=False),
        sa.Column('tables', sa.JSON(), nullable=False),
        sa.Column('response_time_ms', sa.Float(), nullable=False, server_default="0.0"),
        sa.ForeignKeyConstraint(['job_id'], ['crawl_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True,
    )
    op.create_index('ix_extracted_pages_id', 'extracted_pages', ['id'], unique=False, if_not_exists=True)
    op.create_index('ix_extracted_pages_job_id', 'extracted_pages', ['job_id'], unique=False, if_not_exists=True)
    op.create_index('ix_extracted_pages_normalized_url', 'extracted_pages', ['normalized_url'], unique=False, if_not_exists=True)

    # 4. Table: page_links
    op.create_table(
        'page_links',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('page_id', sa.Uuid(), nullable=False),
        sa.Column('target_url', sa.String(length=2048), nullable=False),
        sa.Column('anchor_text', sa.String(length=1024), nullable=True),
        sa.Column('is_external', sa.Boolean(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(['page_id'], ['extracted_pages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True,
    )
    op.create_index('ix_page_links_id', 'page_links', ['id'], unique=False, if_not_exists=True)
    op.create_index('ix_page_links_page_id', 'page_links', ['page_id'], unique=False, if_not_exists=True)

    # 5. Table: page_images
    op.create_table(
        'page_images',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('page_id', sa.Uuid(), nullable=False),
        sa.Column('src', sa.String(length=2048), nullable=False),
        sa.Column('alt', sa.String(length=1024), nullable=True),
        sa.ForeignKeyConstraint(['page_id'], ['extracted_pages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True,
    )
    op.create_index('ix_page_images_id', 'page_images', ['id'], unique=False, if_not_exists=True)
    op.create_index('ix_page_images_page_id', 'page_images', ['page_id'], unique=False, if_not_exists=True)

    # 6. Table: crawl_statistics
    op.create_table(
        'crawl_statistics',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('job_id', sa.Uuid(), nullable=False),
        sa.Column('pages_crawled', sa.Integer(), nullable=False, server_default="0"),
        sa.Column('failed_pages', sa.Integer(), nullable=False, server_default="0"),
        sa.Column('total_images', sa.Integer(), nullable=False, server_default="0"),
        sa.Column('total_links', sa.Integer(), nullable=False, server_default="0"),
        sa.Column('total_duration_sec', sa.Float(), nullable=False, server_default="0.0"),
        sa.ForeignKeyConstraint(['job_id'], ['crawl_jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        if_not_exists=True,
    )
    op.create_index('ix_crawl_statistics_id', 'crawl_statistics', ['id'], unique=False, if_not_exists=True)
    op.create_index('ix_crawl_statistics_job_id', 'crawl_statistics', ['job_id'], unique=False, if_not_exists=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('crawl_statistics', if_exists=True)
    op.drop_table('page_images', if_exists=True)
    op.drop_table('page_links', if_exists=True)
    op.drop_table('extracted_pages', if_exists=True)
    op.drop_table('crawl_jobs', if_exists=True)
    op.drop_table('batch_jobs', if_exists=True)
