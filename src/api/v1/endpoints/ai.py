"""REST API V1 Endpoints for AI Analysis and Grounded Q&A."""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from src.api.dependencies import get_current_user_optional, get_ai_service
from src.application.services.ai.ai_service import AIService
from src.application.services.ai.gemini_provider import GeminiProviderError
from src.db.models.user import User
from src.schemas.ai import (
    AIAnalysisResponse,
    AIQueryRequest,
    AIQueryResponse,
    AIBatchAnalysisResponse,
)

router = APIRouter(prefix="/ai", tags=["AI Intelligence & Q&A"])


@router.post(
    "/crawl/{job_id}/analyze",
    response_model=AIAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate AI Website Executive Summary",
    description="Analyzes the crawled dataset for a job, generating executive summaries, major topics, and key structural insights.",
)
async def analyze_crawl_job(
    job_id: uuid.UUID,
    current_user: Optional[User] = Depends(get_current_user_optional),
    ai_service: AIService = Depends(get_ai_service),
) -> AIAnalysisResponse:
    """Dispatches dataset context analysis to Gemini AI provider."""
    try:
        res = await ai_service.analyze_job(job_id=job_id, user=current_user)
        return AIAnalysisResponse.model_validate(res)
    except GeminiProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post(
    "/crawl/{job_id}/query",
    response_model=AIQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Grounded AI Question Answering",
    description="Answers user questions strictly grounded in the extracted dataset, returning source citations.",
)
async def query_crawl_job(
    job_id: uuid.UUID,
    body: AIQueryRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    ai_service: AIService = Depends(get_ai_service),
) -> AIQueryResponse:
    """Answers a question grounded in the job dataset."""
    try:
        res = await ai_service.query_job(job_id=job_id, question=body.question, history=body.history, user=current_user)
        return AIQueryResponse.model_validate(res)
    except GeminiProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post(
    "/batch/{batch_id}/analyze",
    response_model=AIBatchAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate AI Multi-Website Batch Synthesis",
    description="Generates cross-site comparative analysis across all websites in a batch job.",
)
async def analyze_batch_job(
    batch_id: uuid.UUID,
    current_user: Optional[User] = Depends(get_current_user_optional),
    ai_service: AIService = Depends(get_ai_service),
) -> AIBatchAnalysisResponse:
    """Dispatches batch dataset analysis to Gemini AI provider."""
    try:
        res = await ai_service.analyze_batch(batch_id=batch_id, user=current_user)
        return AIBatchAnalysisResponse.model_validate(res)
    except GeminiProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post(
    "/batch/{batch_id}/query",
    response_model=AIQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Grounded Multi-Website Batch AI Question Answering",
    description="Answers user questions grounded across all websites in a batch job dataset.",
)
async def query_batch_job(
    batch_id: uuid.UUID,
    body: AIQueryRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    ai_service: AIService = Depends(get_ai_service),
) -> AIQueryResponse:
    """Answers a question grounded in the multi-website batch dataset."""
    try:
        res = await ai_service.query_batch(batch_id=batch_id, question=body.question, history=body.history, user=current_user)
        return AIQueryResponse.model_validate(res)
    except GeminiProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post(
    "/crawl/{job_id}/prepare-rag",
    status_code=status.HTTP_200_OK,
    summary="Prepare RAG Vector Embeddings",
    description="Performs semantic chunking and generates vector embeddings for a crawl job dataset.",
)
async def prepare_rag_job(
    job_id: uuid.UUID,
    current_user: Optional[User] = Depends(get_current_user_optional),
    ai_service: AIService = Depends(get_ai_service),
):
    """Indexes crawl job content into document chunks and vector embeddings."""
    try:
        return await ai_service.prepare_rag(job_id=job_id, user=current_user)
    except GeminiProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)
