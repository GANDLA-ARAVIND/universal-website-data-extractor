"""Unit tests for Phase 1 AI Foundation (Gemini Provider, Context Builder, AI Service, and REST endpoints)."""

import uuid
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.schemas.dataset import (
    StandardCrawlDataset,
    WebsiteInformation,
    CrawlMetadata,
    CrawlStatistics,
    WebsiteSummary,
    PageDetail,
)
from src.application.services.ai.context_builder import ContextBuilder
from src.application.services.ai.gemini_provider import GeminiProvider

client = TestClient(app)


def test_context_builder_sanitization():
    """Verifies that ContextBuilder produces clean Markdown omitting timing & HTTP noise."""
    dataset = StandardCrawlDataset(
        website_info=WebsiteInformation(seed_url="https://example.com", domain="example.com"),
        metadata=CrawlMetadata(job_id=uuid.uuid4(), max_depth=1, max_pages=1, render_js=False),
        statistics=CrawlStatistics(pages_crawled=1, total_images=0, total_links=2),
        summary=WebsiteSummary(title="Example Domain", total_pages_extracted=1),
        pages=[
            PageDetail(
                id=uuid.uuid4(),
                url="https://example.com",
                normalized_url="https://example.com/",
                status_code=200,
                depth=1,
                response_time_ms=150.0,
                title="Example Domain",
                meta_description="Example domain meta",
                headings={"h1": ["Example Domain"]},
                paragraphs=["This domain is for use in illustrative examples in documents."],
            )
        ],
    )

    ctx = ContextBuilder.build_dataset_context(dataset)
    assert "# Website Crawl Dataset: example.com" in ctx
    assert "https://example.com" in ctx
    assert "Example domain meta" in ctx
    assert "[H1] Example Domain" in ctx
    assert "This domain is for use in illustrative examples" in ctx


@pytest.mark.asyncio
async def test_gemini_provider_generation():
    """Verifies GeminiProvider returns fallback/synthetic response when API key is unconfigured."""
    provider = GeminiProvider(api_key="")
    text = await provider.generate_text("Summarize this dataset", system_instruction="Test system prompt")
    assert "Executive Summary" in text or "crawled website" in text


@pytest.mark.asyncio
async def test_gemini_provider_rate_limit_and_config():
    """Verifies GeminiProvider error handling on 429 rate limit when fallback is disabled."""
    from unittest.mock import patch, MagicMock
    from src.application.services.ai.gemini_provider import GeminiProviderError
    import httpx

    provider = GeminiProvider(api_key="fake-key")

    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.text = '{"error": {"code": 429, "message": "Quota exceeded"}}'

    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        with patch.object(provider, "_allow_mock", return_value=False):
            with pytest.raises(GeminiProviderError) as exc_info:
                await provider.generate_text("Test question")
            assert exc_info.value.status_code == 429
            assert "quota exceeded" in exc_info.value.message.lower()


@pytest.mark.asyncio
async def test_embedding_model_config_consistency():
    """Verifies EMBEDDING_MODEL setting and vector dimension are consistent across configurations."""
    from src.core.config import settings
    from src.application.services.ai.gemini_provider import GeminiProvider

    assert settings.EMBEDDING_MODEL == "gemini-embedding-001"
    provider = GeminiProvider()
    vectors = await provider.generate_embeddings(["test embedding dimension"])
    assert len(vectors) == 1
    assert len(vectors[0]) == 3072


def test_ai_api_endpoints():
    """Tests /api/v1/ai endpoints for single crawl analysis and grounded Q&A."""
    # Initiate a crawl job
    crawl_res = client.post("/api/v1/crawl", json={"url": "https://example.com"})
    assert crawl_res.status_code == 202
    job_id = crawl_res.json()["id"]

    # Analyze crawl job
    analyze_res = client.post(f"/api/v1/ai/crawl/{job_id}/analyze")
    assert analyze_res.status_code == 200
    data = analyze_res.json()
    assert data["job_id"] == job_id
    assert data["execution_path"] in ["DIRECT_AI", "RAG"]
    assert "analysis" in data
    assert len(data["sources"]) > 0

    # Query crawl job
    query_res = client.post(f"/api/v1/ai/crawl/{job_id}/query", json={"question": "What is this website about?"})
    assert query_res.status_code == 200
    q_data = query_res.json()
    assert q_data["job_id"] == job_id
    assert q_data["question"] == "What is this website about?"
    assert "answer" in q_data
    assert len(q_data["sources"]) > 0
