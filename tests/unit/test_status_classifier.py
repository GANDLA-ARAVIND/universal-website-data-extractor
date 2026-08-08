"""Unit tests for Crawl Result Extraction Status Classifier."""

import uuid
from src.db.models.crawl_job import CrawlJob, CrawlMode, CrawlStatus
from src.db.models.page import ExtractedPage
from src.utils.status_classifier import ExtractionStatus, classify_extraction_status


def test_classify_success() -> None:
    """Verifies SUCCESS classification for rich content extraction."""
    job = CrawlJob(id=uuid.uuid4(), seed_url="https://example.com", status=CrawlStatus.COMPLETED)
    page = ExtractedPage(
        id=uuid.uuid4(),
        job_id=job.id,
        url="https://example.com",
        status_code=200,
        title="Example Domain",
        paragraphs=["Sample paragraph content"],
        headings={"h1": ["Heading 1"]},
    )
    status = classify_extraction_status(pages=[page], job=job)
    assert status == ExtractionStatus.SUCCESS


def test_classify_captcha_detected() -> None:
    """Verifies CAPTCHA_DETECTED classification."""
    job = CrawlJob(id=uuid.uuid4(), seed_url="https://example.com", status=CrawlStatus.COMPLETED)
    page = ExtractedPage(
        id=uuid.uuid4(),
        job_id=job.id,
        url="https://example.com",
        status_code=200,
        title="Security Check - CAPTCHA Verification",
        paragraphs=["Please solve the g-recaptcha below."],
    )
    status = classify_extraction_status(pages=[page], job=job)
    assert status == ExtractionStatus.CAPTCHA_DETECTED


def test_classify_anti_bot_protection() -> None:
    """Verifies ANTI_BOT_PROTECTION classification."""
    job = CrawlJob(id=uuid.uuid4(), seed_url="https://example.com", status=CrawlStatus.COMPLETED)
    page = ExtractedPage(
        id=uuid.uuid4(),
        job_id=job.id,
        url="https://example.com",
        status_code=200,
        title="Just a moment... Cloudflare",
        paragraphs=["Checking your browser before accessing website."],
    )
    status = classify_extraction_status(pages=[page], job=job)
    assert status == ExtractionStatus.ANTI_BOT_PROTECTION


def test_classify_javascript_required() -> None:
    """Verifies JAVASCRIPT_REQUIRED classification."""
    job = CrawlJob(id=uuid.uuid4(), seed_url="https://example.com", status=CrawlStatus.COMPLETED)
    page = ExtractedPage(
        id=uuid.uuid4(),
        job_id=job.id,
        url="https://example.com",
        status_code=200,
        title="App Fallback",
        paragraphs=["You need to enable JavaScript to run this app."],
    )
    status = classify_extraction_status(pages=[page], job=job)
    assert status == ExtractionStatus.JAVASCRIPT_REQUIRED


def test_classify_login_required() -> None:
    """Verifies LOGIN_REQUIRED classification."""
    job = CrawlJob(id=uuid.uuid4(), seed_url="https://example.com", status=CrawlStatus.COMPLETED)
    page = ExtractedPage(
        id=uuid.uuid4(),
        job_id=job.id,
        url="https://example.com",
        status_code=200,
        title="User Sign In",
        paragraphs=["Please log in to continue to your account."],
    )
    status = classify_extraction_status(pages=[page], job=job)
    assert status == ExtractionStatus.LOGIN_REQUIRED


def test_classify_access_denied() -> None:
    """Verifies ACCESS_DENIED classification for 403 Forbidden."""
    job = CrawlJob(id=uuid.uuid4(), seed_url="https://example.com", status=CrawlStatus.COMPLETED)
    page = ExtractedPage(
        id=uuid.uuid4(),
        job_id=job.id,
        url="https://example.com",
        status_code=403,
        title="403 Forbidden",
        paragraphs=["Access to this page is denied."],
    )
    status = classify_extraction_status(pages=[page], job=job)
    assert status == ExtractionStatus.ACCESS_DENIED


def test_classify_no_content() -> None:
    """Verifies NO_CONTENT classification for empty pages."""
    job = CrawlJob(id=uuid.uuid4(), seed_url="https://example.com", status=CrawlStatus.COMPLETED)
    page = ExtractedPage(
        id=uuid.uuid4(),
        job_id=job.id,
        url="https://example.com",
        status_code=200,
        title="Blank",
        paragraphs=[],
        headings={},
    )
    status = classify_extraction_status(pages=[page], job=job)
    assert status == ExtractionStatus.NO_CONTENT


def test_classify_network_error() -> None:
    """Verifies NETWORK_ERROR classification for failed jobs."""
    job = CrawlJob(id=uuid.uuid4(), seed_url="https://example.com", status=CrawlStatus.FAILED)
    status = classify_extraction_status(pages=[], job=job, errors=["Connection refused by remote host"])
    assert status == ExtractionStatus.NETWORK_ERROR
