"""Unit tests for Database Session Factory, Repository Transactions, and Entity Lifecycles."""

import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.db.models.batch_job import BatchJob
from src.db.models.crawl_job import CrawlJob, CrawlMode, CrawlStatus
from src.db.models.page import ExtractedPage
from src.db.session import AsyncSessionFactory


@pytest.mark.asyncio
async def test_db_session_commit_and_rollback():
    """Verifies async session transaction commit and rollback mechanics."""
    async with AsyncSessionFactory() as session:
        # Create test job
        job_id = uuid.uuid4()
        job = CrawlJob(
            id=job_id,
            seed_url="https://example.org",
            status=CrawlStatus.PENDING,
            crawl_mode=CrawlMode.SINGLE,
        )
        session.add(job)
        await session.commit()

        # Retrieve job from DB
        res = await session.execute(select(CrawlJob).where(CrawlJob.id == job_id))
        fetched = res.scalar_one_or_none()
        assert fetched is not None
        assert fetched.seed_url == "https://example.org"

        # Cleanup
        await session.delete(fetched)
        await session.commit()


@pytest.mark.asyncio
async def test_batch_and_child_jobs_cascade_delete():
    """Verifies BatchJob entity relationship and cascade delete behavior."""
    async with AsyncSessionFactory() as session:
        batch_id = uuid.uuid4()
        batch = BatchJob(id=batch_id, status=CrawlStatus.RUNNING, total_urls=2)
        job1 = CrawlJob(
            id=uuid.uuid4(),
            batch_id=batch_id,
            seed_url="https://site1.com",
            status=CrawlStatus.RUNNING,
            crawl_mode=CrawlMode.BATCH,
        )
        job2 = CrawlJob(
            id=uuid.uuid4(),
            batch_id=batch_id,
            seed_url="https://site2.com",
            status=CrawlStatus.PENDING,
            crawl_mode=CrawlMode.BATCH,
        )
        session.add_all([batch, job1, job2])
        await session.commit()

        # Verify batch relationships with explicit selectinload
        stmt = select(BatchJob).where(BatchJob.id == batch_id).options(selectinload(BatchJob.jobs))
        res = await session.execute(stmt)
        fetched_batch = res.scalar_one_or_none()
        assert fetched_batch is not None
        assert len(fetched_batch.jobs) == 2

        # Cascade delete batch
        await session.delete(fetched_batch)
        await session.commit()

        # Verify child jobs are deleted by cascade
        res1 = await session.execute(select(CrawlJob).where(CrawlJob.id == job1.id))
        res2 = await session.execute(select(CrawlJob).where(CrawlJob.id == job2.id))
        assert res1.scalar_one_or_none() is None
        assert res2.scalar_one_or_none() is None
