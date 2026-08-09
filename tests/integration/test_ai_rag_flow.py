"""Integration tests for AI Direct vs RAG execution paths, vector indexing, and grounded Q&A."""

import uuid
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_full_ai_and_rag_pipeline():
    """Tests the full AI workflow from crawl job creation, analysis, RAG indexing, and grounded Q&A."""
    # 1. Initiate Crawl Job
    crawl_res = client.post("/api/v1/crawl", json={"url": "https://example.com"})
    assert crawl_res.status_code == 202
    job_id = crawl_res.json()["id"]

    # 2. Run Direct AI Analysis
    analyze_res = client.post(f"/api/v1/ai/crawl/{job_id}/analyze")
    assert analyze_res.status_code == 200
    a_data = analyze_res.json()
    assert a_data["job_id"] == job_id
    assert "analysis" in a_data
    assert a_data["execution_path"] in ["DIRECT_AI", "RAG"]
    assert len(a_data["sources"]) > 0

    # 3. Index RAG Embeddings
    rag_prep_res = client.post(f"/api/v1/ai/crawl/{job_id}/prepare-rag")
    assert rag_prep_res.status_code == 200
    rag_data = rag_prep_res.json()
    assert rag_data["job_id"] == job_id
    assert rag_data["status"] == "INDEXED"
    assert rag_data["chunks_indexed"] >= 1

    # 4. Grounded AI Question Answering with Conversation History
    query_res = client.post(
        f"/api/v1/ai/crawl/{job_id}/query",
        json={
            "question": "What domain illustrative example is mentioned?",
            "history": [
                {"role": "user", "content": "What website is this?"},
                {"role": "assistant", "content": "This is example.com."}
            ]
        }
    )
    assert query_res.status_code == 200
    q_data = query_res.json()
    assert q_data["job_id"] == job_id
    assert "answer" in q_data
    assert len(q_data["sources"]) > 0


def test_batch_ai_analysis_and_query():
    """Tests multi-website batch AI synthesis and multi-turn grounded Q&A."""
    batch_res = client.post("/api/v1/batch", json={"urls": ["https://example.com"]})
    assert batch_res.status_code == 202
    batch_id = batch_res.json()["id"]

    analyze_res = client.post(f"/api/v1/ai/batch/{batch_id}/analyze")
    assert analyze_res.status_code == 200
    assert analyze_res.json()["batch_id"] == batch_id

    query_res = client.post(
        f"/api/v1/ai/batch/{batch_id}/query",
        json={
            "question": "Summarize the websites in this batch.",
            "history": []
        }
    )
    assert query_res.status_code == 200
    assert query_res.json()["batch_id"] == batch_id
    assert "answer" in query_res.json()


def test_ai_query_nonexistent_job():
    """Verifies HTTP 404 is returned when asking questions on a non-existent job ID."""
    fake_id = str(uuid.uuid4())
    res = client.post(f"/api/v1/ai/crawl/{fake_id}/query", json={"question": "What is this?"})
    assert res.status_code == 404
