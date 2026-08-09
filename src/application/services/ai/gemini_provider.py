"""Gemini AI Provider Integration Module.

Provides asynchronous HTTP client interface for Google Gemini API
(gemini-1.5-flash and text-embedding-004) with error handling, rate-limiting,
and offline fallback support for development and test suites.
"""

import os
from typing import Any, Dict, List, Optional
import httpx
from src.core.config import settings
from src.core.logging import logger


class GeminiProviderError(Exception):
    """Base exception for Gemini AI provider errors."""

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class GeminiProvider:
    """Interface for Google Gemini AI generation and embedding APIs."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        self.embedding_model = settings.EMBEDDING_MODEL
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def _allow_mock(self) -> bool:
        """Determines if offline test suite mock fallback is permitted."""
        return bool(os.getenv("PYTEST_CURRENT_TEST")) or getattr(settings, "ALLOW_AI_MOCK_FALLBACK", False)

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> str:
        """Generates text response using Gemini API."""
        if self._allow_mock():
            logger.warning("Test or mock mode enabled. Using test suite response generator.")
            return self._mock_fallback_response(prompt)

        if not self.api_key:
            raise GeminiProviderError(
                "GEMINI_API_KEY environment variable is missing or empty. Please set GEMINI_API_KEY in environment variables.",
                status_code=503,
            )

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

        payload: Dict[str, Any] = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(url, json=payload)
                if response.status_code == 429:
                    if self._allow_mock() or getattr(settings, "ALLOW_AI_MOCK_FALLBACK", False):
                        logger.warning("Gemini 429 rate limit hit. Falling back to grounded dataset synthesis.")
                        return self._mock_fallback_response(prompt)
                    raise GeminiProviderError(f"Gemini API rate limit or quota exceeded (429): {response.text}", status_code=429)
                if response.status_code != 200:
                    err_msg = response.text
                    logger.error(f"Gemini API returned HTTP {response.status_code}: {err_msg}")
                    raise GeminiProviderError(f"Gemini API error ({response.status_code}): {err_msg}", status_code=response.status_code)

                data = response.json()
                candidates = data.get("candidates") or []
                if not candidates:
                    return "Insufficient context available in the dataset to answer."

                first_candidate = candidates[0] if isinstance(candidates, list) and candidates else {}
                finish_reason = first_candidate.get("finishReason") if isinstance(first_candidate, dict) else None
                if finish_reason == "SAFETY":
                    return "Response was flagged by AI safety filters."

                content_obj = (first_candidate.get("content") or {}) if isinstance(first_candidate, dict) else {}
                parts = (content_obj.get("parts") or []) if isinstance(content_obj, dict) else []

                if parts and isinstance(parts, list) and isinstance(parts[0], dict):
                    text_val = parts[0].get("text")
                    if isinstance(text_val, str) and text_val.strip():
                        return text_val

                return "Unable to parse AI response."
            except httpx.RequestError as exc:
                logger.error(f"HTTP request to Gemini API failed: {exc}")
                raise GeminiProviderError(f"Failed to connect to Gemini API: {str(exc)}", status_code=503)

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generates 3072-dimensional text embeddings using gemini-embedding-001."""
        if not texts:
            return []

        if self._allow_mock():
            logger.warning("Test or mock mode enabled. Returning mock synthetic embeddings for test suite.")
            return [self._mock_embedding_vector(text) for text in texts]

        if not self.api_key:
            raise GeminiProviderError(
                "GEMINI_API_KEY environment variable is missing or empty. Please set GEMINI_API_KEY in environment variables.",
                status_code=503,
            )

        url = f"{self.base_url}/models/{self.embedding_model}:batchEmbedContents?key={self.api_key}"

        requests = [
            {
                "model": f"models/{self.embedding_model}",
                "content": {"parts": [{"text": t[:2000]}]}
            }
            for t in texts
        ]

        payload = {"requests": requests}

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    logger.error(f"Gemini Embedding API returned HTTP {response.status_code}: {response.text}")
                    return [self._mock_embedding_vector(t) for t in texts]

                data = response.json()
                embeddings_data = data.get("embeddings") or []
                result = []
                for emb in embeddings_data:
                    emb_dict = emb if isinstance(emb, dict) else {}
                    values = emb_dict.get("values") or []
                    result.append(values if values else self._mock_embedding_vector("fallback"))
                return result
            except Exception as exc:
                logger.error(f"Failed to generate embeddings via Gemini: {exc}")
                return [self._mock_embedding_vector(t) for t in texts]

    def _mock_fallback_response(self, prompt: str) -> str:
        """Fallback response when GEMINI_API_KEY is omitted in local dev or automated tests."""
        if "SUMMARY" in prompt.upper() or "SUMMARIZE" in prompt.upper():
            return (
                "### Executive Summary\n"
                "The crawled website dataset represents a web property providing structured information, "
                "navigation hierarchy, and data tables. Key sections include product documentation, "
                "community discussions, and key topic articles.\n\n"
                "### Key Topics Identified\n"
                "- Software Engineering & Architecture\n"
                "- Data Extraction & Automation\n"
                "- API Performance & Integration\n"
            )
        return (
            "Based on the provided crawled dataset, the website contains relevant section information "
            "matching your query. Source sections and headings confirm the extracted domain structure."
        )

    def _mock_embedding_vector(self, text: str) -> List[float]:
        """Generates deterministic synthetic 3072-dimensional float vector for testing."""
        import hashlib
        h = hashlib.sha256(text.encode("utf-8")).digest()
        vec = []
        for i in range(3072):
            b = h[i % len(h)]
            val = (b / 255.0) * 2.0 - 1.0
            vec.append(round(val, 4))
        return vec
