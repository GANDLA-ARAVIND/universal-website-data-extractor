"""Integration tests for Alembic database migrations and schema lifecycle."""

import pytest
from alembic.command import downgrade, upgrade
from alembic.config import Config
from src.core.config import settings


@pytest.fixture
def alembic_cfg():
    """Returns configured Alembic Config instance."""
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", settings.ASYNC_DATABASE_URI)
    return cfg


def test_alembic_migration_upgrade_and_downgrade(alembic_cfg):
    """Verifies that Alembic migrations can execute upgrade head and downgrade base cleanly."""
    # Test upgrading to latest revision
    upgrade(alembic_cfg, "head")

    # Test downgrading to base
    downgrade(alembic_cfg, "base")

    # Re-apply upgrade to head to restore database state for remaining tests
    upgrade(alembic_cfg, "head")
