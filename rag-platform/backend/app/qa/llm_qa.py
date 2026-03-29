"""
LLM QA Module
Uses LLM ONLY for reasoning over retrieved context.
Strict prompts prevent hallucination.
Supports OpenAI, Anthropic, and Ollama providers.
"""

from __future__ import annotations

import json
from typing import List, Optional, Tuple, Union

import structlog

from app.core.config import settings
from app.core.logging import TimingLogger
from app.models.schemas import DocumentChunk, QueryType, TableChunk
from app.qa.classifier import QueryAnalysis

logger = structlog.get_logger(__name__)


# ── System prompt — strict factual QA ────────────────────────────────────────
SYSTEM_PROMPT = """You are a financial document analysis assistant.

STRICT RULES:
1. Answer ONLY using information from the provided document excerpts
2. If the answer is not in the excerpts, say exactly: "Информация не найдена в предоставленных документах."
3. NEVER invent, extrapolate, or assume data not explicitly present
4. Always cite your source (file name and page/sheet)
5. For numbers: copy them exactly as they appear, do not calculate or estimate
6. Respond in the same language as the question (Russian or Uzbek)
7. Be concise and precise — financial users need accuracy, not verbosity

OUTPUT FORMAT (JSON):
{
  "answer": "...",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation of how you found this",
  "sources_used": ["filename:page"]
}"""

USER_PROMPT_TEMPLATE = """QUESTION: {question}

DOCUMENT EXCERPTS:
{context}

Based ONLY on the above excerpts, answer the question in JSON format."""


class LLMQAModule:
    """
    LLM-based QA for complex reasoning over retrieved context.
    
    Provider routing:
    - openai: GPT-4o-mini / GPT-4o
    - anthropic: Claude claude-sonnet-4-20250514
    - ollama: Local models (Llama3, Mistral, etc.)
    """

    def __init__(self):
        self._client = None
        self._provider = settings.LLM_PROVIDER

    def _get_client(self):
        """Lazy-initialize the LLM client."""
        if self._client is not None:
            return self._client

        if self._provider == "openai":
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(
                    api_key=settings.LLM_API_KEY,
                    base_url=settings.LLM_BASE_URL,
                )
            except ImportError:
                raise RuntimeError("openai not installed. Run: pip install openai")

        elif self._provider == "anthropic":
            try:
                import anthropic
                self._client = anthropic.AsyncAnthropic(
                    api_key=settings.LLM_API_KEY
                )
            except ImportError:
                raise RuntimeError("anthropic not installed. Run: pip install anthropic")

        elif self._provider == "ollama":
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(
                    base_url=settings.LLM_BASE_URL or "http://localhost:11434/v1",
                    api_key="ollama",
                )
            except ImportError:
                raise RuntimeError("openai package needed for Ollama. Run: pip install openai")

        return self._client

    async def answer(
        self,
        question: str,
        chunks: List[Union[DocumentChunk, TableChunk]],
        analysis: QueryAnalysis,
    ) -> Tuple[str, float]:
        """
        Generate an answer using the LLM over retrieved context.

        Args:
            question: Original user question.
            chunks: Retrieved and ranked chunks.
            analysis: Query analysis result.

        Returns:
            (answer_text, confidence_score)
        """
        if not chunks:
            return "Информация не найдена в предоставленных документах.", 0.0

        context = self._build_context(chunks)
        prompt = USER_PROMPT_TEMPLATE.format(
            question=question,
            context=context,
        )

        with TimingLogger("llm_call", logger, provider=self._provider):
            try:
                raw_response = await self._call_llm(prompt)
                answer, confidence = self._parse_response(raw_response)
            except Exception as e:
                logger.error("LLM call failed", error=str(e))
                # Graceful fallback — return best chunk content
                answer = self._fallback_answer(chunks, question)
                confidence = 0.3

        return answer, confidence

    async def _call_llm(self, user_prompt: str) -> str:
        """Dispatch to the appropriate LLM provider."""
        client = self._get_client()

        if self._provider in ("openai", "ollama"):
            response = await client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=settings.LLM_MAX_TOKENS,
                temperature=settings.LLM_TEMPERATURE,
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content

        elif self._provider == "anthropic":
            response = await client.messages.create(
                model=settings.LLM_MODEL,
                max_tokens=settings.LLM_MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return response.content[0].text

        raise ValueError(f"Unknown LLM provider: {self._provider}")

    def _parse_response(self, raw: str) -> Tuple[str, float]:
        """Parse the LLM JSON response into (answer, confidence)."""
        try:
            data = json.loads(raw)
            answer = data.get("answer", "").strip()
            confidence = float(data.get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))  # clamp

            if not answer:
                return "Ответ не сформирован.", 0.1

            return answer, confidence

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning("Failed to parse LLM JSON response", error=str(e))
            # Return raw text as answer
            clean = raw.strip().replace("```json", "").replace("```", "")
            return clean[:2000] if clean else "Ошибка формирования ответа.", 0.1

    def _build_context(self, chunks: List[Union[DocumentChunk, TableChunk]]) -> str:
        """
        Format retrieved chunks into a numbered context block for the LLM.
        Each chunk is labeled with its source for citation.
        """
        parts = []
        for i, chunk in enumerate(chunks, start=1):
            source = chunk.source_label

            if isinstance(chunk, TableChunk):
                content = chunk.summary
            else:
                content = chunk.content

            # Truncate very long chunks to stay within context window
            content = content[:1500] if len(content) > 1500 else content
            parts.append(f"[{i}] Source: {source}\n{content}")

        return "\n\n---\n\n".join(parts)

    def _fallback_answer(
        self, chunks: List[Union[DocumentChunk, TableChunk]], question: str
    ) -> str:
        """
        Emergency fallback when LLM is unavailable.
        Returns the most relevant chunk content directly.
        """
        if not chunks:
            return "Информация не найдена."

        best = chunks[0]
        content = best.summary if isinstance(best, TableChunk) else best.content
        return f"Из документа «{best.metadata.file_name}»:\n\n{content[:500]}..."
