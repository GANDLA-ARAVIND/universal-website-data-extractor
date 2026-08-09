"""AI Service Layer Module.

Orchestrates dataset context preparation, dataset sizing assessment (Direct AI vs RAG),
Gemini LLM generation, grounded Q&A, and source attribution.
Enforces resource ownership isolation via CrawlJob and BatchJob repository checks.
"""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.config import settings
from src.core.logging import logger
from src.db.models.user import User
from src.db.models.chunk import DocumentChunk
from src.db.repositories.crawl_repository import CrawlRepository
from src.db.repositories.batch_repository import BatchRepository
from src.db.repositories.chunk_repository import ChunkRepository
from src.application.services.crawl_service import CrawlService, CrawlJobNotFoundException
from src.application.services.batch_service import BatchService, CrawlJobNotFoundException as BatchJobNotFoundException
from src.application.services.ai.gemini_provider import GeminiProvider
from src.application.services.ai.context_builder import ContextBuilder
from src.application.services.ai.chunker import Chunker
from src.schemas.dataset import StandardCrawlDataset, BatchDataset


class AIService:
    """Application use-case service for AI Analysis, Q&A, and RAG retrieval."""

    def __init__(
        self,
        crawl_service: CrawlService,
        batch_service: BatchService,
        session: Optional[AsyncSession] = None,
        gemini_provider: Optional[GeminiProvider] = None,
    ):
        self.crawl_service = crawl_service
        self.batch_service = batch_service
        self.session = session or crawl_service.session
        self.chunk_repo = ChunkRepository(self.session)
        self.gemini_provider = gemini_provider or GeminiProvider()

    async def assess_dataset_path(self, total_pages: int, total_text_char: int) -> str:
        """Determines whether to use 'DIRECT_AI' or 'RAG' based on context thresholds."""
        estimated_tokens = total_text_char // 4
        if estimated_tokens > settings.MAX_DIRECT_CONTEXT_TOKENS or total_pages > 50:
            return "RAG"
        return "DIRECT_AI"

    async def prepare_rag(
        self,
        job_id: uuid.UUID,
        user: Optional[User] = None,
    ) -> Dict[str, Any]:
        """Performs semantic chunking, embedding generation, and vector persistence for RAG retrieval."""
        job = await self.crawl_service.get_job_status(job_id, current_user=user)
        pages, _ = await self.crawl_service.get_job_results(job_id=job_id, page=1, limit=1000, current_user=user)

        # Clear old chunks if re-indexing
        await self.chunk_repo.delete_chunks_by_job_id(job_id)

        all_raw_chunks: List[Dict[str, Any]] = []
        for p in pages:
            p_chunks = Chunker.chunk_page(
                page=p,
                chunk_size=settings.DEFAULT_CHUNK_SIZE_CHAR,
                chunk_overlap=settings.DEFAULT_CHUNK_OVERLAP_CHAR,
            )
            all_raw_chunks.extend(p_chunks)

        if not all_raw_chunks:
            return {"job_id": str(job_id), "chunks_indexed": 0, "status": "NO_CONTENT"}

        texts = [c["text"] for c in all_raw_chunks]
        embeddings = await self.gemini_provider.generate_embeddings(texts)

        db_chunks: List[DocumentChunk] = []
        for idx, raw in enumerate(all_raw_chunks):
            emb = embeddings[idx] if idx < len(embeddings) else None
            chunk_obj = DocumentChunk(
                job_id=job_id,
                batch_id=job.batch_id,
                project_id=job.project_id,
                page_id=raw["page_id"],
                url=raw["url"],
                page_title=raw["page_title"],
                heading_path=raw["heading_path"],
                chunk_index=raw["chunk_index"],
                text=raw["text"],
                char_count=raw["char_count"],
                embedding=emb,
            )
            db_chunks.append(chunk_obj)

        await self.chunk_repo.save_chunks(db_chunks)

        return {
            "job_id": str(job_id),
            "chunks_indexed": len(db_chunks),
            "status": "INDEXED",
        }

    async def analyze_job(
        self,
        job_id: uuid.UUID,
        user: Optional[User] = None,
    ) -> Dict[str, Any]:
        """Generates AI executive summary and major topics analysis for a single crawl job dataset."""
        dataset = await self.crawl_service.get_job_dataset(job_id, current_user=user)
        seed_url = getattr(dataset.website_info, 'seed_url', None) or getattr(dataset, 'seed_url', 'Unknown Target')
        total_pages = getattr(dataset.statistics, 'pages_crawled', len(dataset.pages))

        context_str = ContextBuilder.build_dataset_context(dataset)
        path = await self.assess_dataset_path(total_pages, len(context_str))

        system_instruction = (
            "You are an expert AI Web Intelligence Analyst. Your role is to analyze "
            "the provided website crawl dataset and produce a structured, high-value executive summary. "
            "Strictly ground all findings in the provided dataset."
        )

        prompt = (
            f"Analyze the following website crawl dataset for target URL: {seed_url}\n\n"
            f"CRAWLED DATASET CONTEXT:\n{context_str}\n\n"
            "Produce a structured Markdown report containing:\n"
            "1. ### Executive Summary\n"
            "2. ### Major Topics & Structural Sections\n"
            "3. ### Key Extracted Insights\n"
            "4. ### Data Coverage Audit (Pages, Headings, Tables)\n"
        )

        analysis_text = await self.gemini_provider.generate_text(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.2,
        )

        sources = [
            {"page_title": page.title or "Untitled", "url": page.url}
            for page in dataset.pages[:5]
        ]

        return {
            "job_id": str(job_id),
            "seed_url": seed_url,
            "execution_path": path,
            "total_pages_analyzed": total_pages,
            "analysis": analysis_text,
            "sources": sources,
        }

    async def query_job(
        self,
        job_id: uuid.UUID,
        question: str,
        history: Optional[List[Dict[str, str]]] = None,
        user: Optional[User] = None,
    ) -> Dict[str, Any]:
        """Answers a user question grounded in the crawled dataset using Direct AI or RAG vector retrieval."""
        dataset = await self.crawl_service.get_job_dataset(job_id, current_user=user)
        seed_url = getattr(dataset.website_info, 'seed_url', None) or getattr(dataset, 'seed_url', 'Unknown Target')
        total_pages = getattr(dataset.statistics, 'pages_crawled', len(dataset.pages))

        context_str = ContextBuilder.build_dataset_context(dataset)
        path = await self.assess_dataset_path(total_pages, len(context_str))

        history_str = ""
        if history:
            recent_turns = history[-6:]
            history_str = "\n".join([f"{msg.get('role', 'user').upper()}: {msg.get('content', '')}" for msg in recent_turns])

        matching_sources = []
        retrieved_count = 0

        if path == "RAG":
            # Check if chunks exist; if not, index on demand
            existing_chunks = await self.chunk_repo.get_chunks_by_job_id(job_id)
            if not existing_chunks:
                await self.prepare_rag(job_id=job_id, user=user)

            # Generate vector embedding for question
            q_embeddings = await self.gemini_provider.generate_embeddings([question])
            q_emb = q_embeddings[0] if q_embeddings else []

            similar_chunks = await self.chunk_repo.search_similar_chunks(job_id, q_emb, top_k=5)
            retrieved_count = len(similar_chunks)
            rag_context_blocks = []
            for chunk, sim in similar_chunks:
                rag_context_blocks.append(f"[Source: {chunk.url} | Section: {chunk.heading_path}]\n{chunk.text}")
                matching_sources.append({
                    "page_title": chunk.page_title or "Page",
                    "url": chunk.url,
                    "heading": chunk.heading_path,
                })

            rag_context_str = "\n\n---\n\n".join(rag_context_blocks)

            system_instruction = (
                "You are an AI Question Answering assistant for the Website Intelligence Platform. "
                "Your task is to answer user questions using ONLY the retrieved context chunks below and conversation history. "
                "If the retrieved context does not contain sufficient information to answer the question, clearly state "
                "'The available crawled dataset does not contain sufficient information to answer this question.' "
                "Do NOT invent or hallucinate information outside the retrieved context."
            )

            prompt = (
                f"RETRIEVED RAG CONTEXT CHUNKS FOR {seed_url}:\n{rag_context_str}\n\n"
                f"{f'RECENT CONVERSATION HISTORY:\n{history_str}\n\n' if history_str else ''}"
                f"USER QUESTION: {question}\n\n"
                "Answer the question clearly and cite specific page URLs or section headings."
            )
        else:
            system_instruction = (
                "You are an AI Question Answering assistant for the Website Intelligence Platform. "
                "Your task is to answer user questions using ONLY the provided crawled website dataset and conversation history. "
                "If the dataset does not contain sufficient information to answer the question, clearly state "
                "'The available crawled dataset does not contain sufficient information to answer this question.' "
                "Do NOT invent or hallucinate information outside the dataset."
            )

            prompt = (
                f"CRAWLED DATASET CONTEXT FOR {seed_url}:\n{context_str}\n\n"
                f"{f'RECENT CONVERSATION HISTORY:\n{history_str}\n\n' if history_str else ''}"
                f"USER QUESTION: {question}\n\n"
                "Answer the question clearly and cite specific page URLs or section headings from the dataset."
            )

            q_lower = question.lower()
            for p in dataset.pages:
                p_text = (p.title or "") + " " + (p.url or "")
                if any(term in p_text.lower() for term in q_lower.split()):
                    matching_sources.append({"page_title": p.title or "Page", "url": p.url})

            if not matching_sources and dataset.pages:
                matching_sources = [{"page_title": dataset.pages[0].title or "Home", "url": dataset.pages[0].url}]

        answer_text = await self.gemini_provider.generate_text(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.1,
        )

        return {
            "job_id": str(job_id),
            "question": question,
            "execution_path": path,
            "retrieved_chunks_count": retrieved_count,
            "answer": answer_text,
            "sources": matching_sources[:5],
        }

    async def analyze_batch(
        self,
        batch_id: uuid.UUID,
        user: Optional[User] = None,
    ) -> Dict[str, Any]:
        """Generates AI synthesis and comparative analysis across all websites in a batch dataset."""
        batch_dataset = await self.batch_service.get_batch_dataset(batch_id, current_user=user)
        total_websites = getattr(batch_dataset.batch_statistics, 'total_websites', len(batch_dataset.websites))
        context_str = ContextBuilder.build_batch_dataset_context(batch_dataset)

        system_instruction = (
            "You are a Multi-Website Intelligence Competitive Analyst. "
            "Analyze the provided multi-website batch dataset and generate a comparative synthesis."
        )

        prompt = (
            f"Analyze the multi-website batch dataset #{batch_id} containing {total_websites} targets:\n\n"
            f"{context_str}\n\n"
            "Provide:\n"
            "1. ### Executive Batch Summary\n"
            "2. ### Cross-Site Comparative Analysis\n"
            "3. ### Key Industry / Topic Patterns\n"
        )

        analysis_text = await self.gemini_provider.generate_text(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.2,
        )

        sources = [
            {"page_title": site.website_url, "url": site.website_url}
            for site in batch_dataset.websites
        ]

        return {
            "batch_id": str(batch_id),
            "total_websites": total_websites,
            "execution_path": "DIRECT_AI",
            "analysis": analysis_text,
            "sources": sources,
        }

    async def query_batch(
        self,
        batch_id: uuid.UUID,
        question: str,
        history: Optional[List[Dict[str, str]]] = None,
        user: Optional[User] = None,
    ) -> Dict[str, Any]:
        """Answers a user question grounded across all websites in a multi-website batch dataset."""
        batch_dataset = await self.batch_service.get_batch_dataset(batch_id, current_user=user)
        total_websites = getattr(batch_dataset.batch_statistics, 'total_websites', len(batch_dataset.websites))
        context_str = ContextBuilder.build_batch_dataset_context(batch_dataset)

        history_str = ""
        if history:
            recent_turns = history[-6:]
            history_str = "\n".join([f"{msg.get('role', 'user').upper()}: {msg.get('content', '')}" for msg in recent_turns])

        system_instruction = (
            "You are a Multi-Website Intelligence Assistant. "
            "Your task is to answer user questions grounded across all websites in the provided batch dataset. "
            "Strictly ground all answers in the dataset provided. If information is missing, state so clearly."
        )

        prompt = (
            f"BATCH DATASET CONTEXT ({total_websites} WEBSITES):\n{context_str}\n\n"
            f"{f'RECENT CONVERSATION HISTORY:\n{history_str}\n\n' if history_str else ''}"
            f"USER QUESTION: {question}\n\n"
            "Answer the question clearly and cite specific website URLs."
        )

        answer_text = await self.gemini_provider.generate_text(
            prompt=prompt,
            system_instruction=system_instruction,
            temperature=0.1,
        )

        sources = [
            {"page_title": site.website_url, "url": site.website_url}
            for site in batch_dataset.websites[:5]
        ]

        return {
            "batch_id": str(batch_id),
            "question": question,
            "execution_path": "DIRECT_AI",
            "retrieved_chunks_count": 0,
            "answer": answer_text,
            "sources": sources,
        }
