"""Add users, projects, and resource ownership

Revision ID: 35f2f7b2f548
Revises: ddf1b1918ce4
Create Date: 2026-08-08 15:51:44.189291

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '35f2f7b2f548'
down_revision: Union[str, Sequence[str], None] = 'ddf1b1918ce4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('users',
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    if_not_exists=True,
    )
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_users_email'), ['email'], unique=True, if_not_exists=True)
        batch_op.create_index(batch_op.f('ix_users_id'), ['id'], unique=False, if_not_exists=True)

    op.create_table('projects',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    if_not_exists=True,
    )
    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_projects_id'), ['id'], unique=False, if_not_exists=True)
        batch_op.create_index(batch_op.f('ix_projects_name'), ['name'], unique=False, if_not_exists=True)
        batch_op.create_index(batch_op.f('ix_projects_user_id'), ['user_id'], unique=False, if_not_exists=True)

    with op.batch_alter_table('batch_jobs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('project_id', sa.Uuid(), nullable=True))
        batch_op.create_index(batch_op.f('ix_batch_jobs_project_id'), ['project_id'], unique=False)
        batch_op.create_foreign_key('fk_batch_jobs_project_id_projects', 'projects', ['project_id'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('crawl_jobs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('project_id', sa.Uuid(), nullable=True))
        batch_op.create_index(batch_op.f('ix_crawl_jobs_project_id'), ['project_id'], unique=False)
        batch_op.create_foreign_key('fk_crawl_jobs_project_id_projects', 'projects', ['project_id'], ['id'], ondelete='CASCADE')

    with op.batch_alter_table('crawl_statistics', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_crawl_statistics_job_id'))
        batch_op.create_index(batch_op.f('ix_crawl_statistics_job_id'), ['job_id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('crawl_statistics', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_crawl_statistics_job_id'))
        batch_op.create_index(batch_op.f('ix_crawl_statistics_job_id'), ['job_id'], unique=False)

    with op.batch_alter_table('crawl_jobs', schema=None) as batch_op:
        batch_op.drop_constraint('fk_crawl_jobs_project_id_projects', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_crawl_jobs_project_id'))
        batch_op.drop_column('project_id')

    with op.batch_alter_table('batch_jobs', schema=None) as batch_op:
        batch_op.drop_constraint('fk_batch_jobs_project_id_projects', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_batch_jobs_project_id'))
        batch_op.drop_column('project_id')

    with op.batch_alter_table('projects', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_projects_user_id'))
        batch_op.drop_index(batch_op.f('ix_projects_name'))
        batch_op.drop_index(batch_op.f('ix_projects_id'))

    op.drop_table('projects')
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_id'))
        batch_op.drop_index(batch_op.f('ix_users_email'))

    op.drop_table('users')
    # ### end Alembic commands ###
