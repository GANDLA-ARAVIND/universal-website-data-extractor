"""Pydantic Request and Response Schemas for AI Endpoints."""

import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AISourceReference(BaseModel):
    """Source page or section attribution metadata for AI answers."""

    page_title: Optional[str] = Field(None, description="Title of source page")
    url: str = Field(..., description="Canonical source page URL")
    heading: Optional[str] = Field(None, description="Heading/section title")


class AIAnalysisResponse(BaseModel):
    """Response model for single crawl job AI executive analysis."""

    job_id: uuid.UUID = Field(..., description="Crawl job ID")
    seed_url: str = Field(..., description="Target seed URL")
    execution_path: str = Field(..., description="AI execution strategy (DIRECT_AI or RAG)")
    total_pages_analyzed: int = Field(..., description="Pages included in context")
    analysis: str = Field(..., description="Structured AI executive summary & insights")
    sources: List[AISourceReference] = Field(default_factory=list, description="Grounding source citations")


class AIQueryRequest(BaseModel):
    """Request model for asking questions grounded in a dataset."""

    question: str = Field(..., min_length=2, max_length=1000, description="Natural language question")
    history: Optional[List[Dict[str, str]]] = Field(default_factory=list, description="Previous conversation turns")


class AIQueryResponse(BaseModel):
    """Response model for grounded AI question answering."""

    job_id: Optional[uuid.UUID] = Field(None, description="Crawl job ID")
    batch_id: Optional[uuid.UUID] = Field(None, description="Batch job ID")
    question: str = Field(..., description="Original user question")
    execution_path: str = Field(..., description="AI execution strategy (DIRECT_AI or RAG)")
    retrieved_chunks_count: Optional[int] = Field(0, description="Number of RAG vector chunks retrieved")
    answer: str = Field(..., description="Grounded AI answer text")
    sources: List[AISourceReference] = Field(default_factory=list, description="Source page citations")


class AIBatchAnalysisResponse(BaseModel):
    """Response model for multi-website batch AI synthesis."""

    batch_id: uuid.UUID = Field(..., description="Batch job ID")
    total_websites: int = Field(..., description="Websites included in synthesis")
    execution_path: str = Field(..., description="AI execution strategy")
    analysis: str = Field(..., description="Cross-website comparative analysis")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Source website list")
