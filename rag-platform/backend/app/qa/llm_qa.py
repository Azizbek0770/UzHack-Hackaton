"""
LLM QA Module — v2 (Fixed & Hardened)
======================================
- Fixed: Google Gemini treated as OpenAI-compatible provider
- Fixed: Robust JSON extraction handles markdown-wrapped responses
- Fixed: Stronger Uzbek language enforcement in system prompt
- Fixed: No hallucination — strict grounding rules
- Fixed: Fallback path also returns clean Uzbek text
"""

from __future__ import annotations

import json
import re
from typing import List, Optional, Tuple, Union

import structlog

from app.core.config import settings
from app.core.logging import TimingLogger
from app.models.schemas import DocumentChunk, QueryType, TableChunk
from app.qa.classifier import QueryAnalysis

logger = structlog.get_logger(__name__)


# ── System Prompt — Strict, Uzbek-first, anti-hallucination ──────────────────
SYSTEM_PROMPT = """Siz O'zbekiston Milliy Banki (NBU) moliyaviy hujjatlarini tahlil qiluvchi sun'iy intellekt yordamchisisiz. Ismingiz "FinBot".

═══════════════════════════════════════════════════
MUTLAQ QOIDALAR (BUZIB BO'LMAYDI):
═══════════════════════════════════════════════════

1. FAQAT O'ZBEK TILIDA javob bering — savol qaysi tilda bo'lsa ham, JAVOB FAQAT O'ZBEK TILIDA bo'lishi shart.

2. FAQAT taqdim etilgan hujjat parchalaridan foydalaning. Agar javob hujjatlarda bo'lmasa, AYNAN shunday yozing:
   "Bu ma'lumot taqdim etilgan hujjatlarda topilmadi."

3. HECH QACHON:
   - Ma'lumot o'ylab topmang
   - Taxmin yoki ko'rsatma beritmang
   - Hujjatlarda ko'rsatilmagan raqamlarni ishlatmang
   - Interpolatsiya yoki hisob-kitob qilmang

4. Har doim MANBA ko'rsating: fayl nomi va sahifa/varaq raqami.

5. Raqamlarni AYNAN hujjatda yozilganidek ko'chiring — hisob-kitob qilmasdan.

6. Javob ANIQ va QISQA bo'lsin — moliyaviy foydalanuvchilar aniqlikni qadriyatlar.

7. Professional va rasmiy O'zbek tilida muloqot qiling.

═══════════════════════════════════════════════════
JAVOB FORMATI (JSON):
═══════════════════════════════════════════════════
{
  "answer": "O'zbek tilidagi to'liq va aniq javob. Ko'rsatkich qiymati va manba majburiy.",
  "confidence": 0.0-1.0,
  "sources_used": ["fayl_nomi:sahifa_yoki_varaq"]
}

MUHIM: JSON formatidan BOSHQA hech narsa yozmang. Markdown, ``` blok, yoki boshqa belgilar QILINMAYDI."""


USER_PROMPT_TEMPLATE = """SAVOL: {question}

═══════════════════════════════════════════════
HUJJAT PARCHALARI (faqat shu ma'lumotlardan foydalaning):
═══════════════════════════════════════════════
{context}
═══════════════════════════════════════════════

Yuqoridagi hujjat parchalarini diqqat bilan o'qing va FAQAT ularga asoslanib, O'ZBEK TILIDA JSON formatida javob bering.
Agar javob hujjatlarda bo'lmasa: {{"answer": "Bu ma'lumot taqdim etilgan hujjatlarda topilmadi.", "confidence": 0.0, "sources_used": []}}"""


class LLMQAModule:
    """
    LLM-based QA for complex reasoning over retrieved context.

    Provider routing:
    - openai: GPT-4o-mini / GPT-4o
    - anthropic: Claude claude-sonnet-4-20250514
    - ollama: Local models (Llama3, Mistral, etc.)
    - google: Treated as OpenAI-compatible (Gemini via OpenAI endpoint)
    """

    def __init__(self):
        self._client = None
        self._provider = settings.LLM_PROVIDER

    def _get_client(self):
        """Lazy-initialize the LLM client."""
        if self._client is not None:
            return self._client

        # Both "openai" and "google" use the OpenAI-compatible client
        if self._provider in ("openai", "google"):
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(
                    api_key=settings.LLM_API_KEY,
                    base_url=settings.LLM_BASE_URL,
                )
                logger.info(
                    "LLM client initialized",
                    provider=self._provider,
                    model=settings.LLM_MODEL,
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

        else:
            raise ValueError(
                f"Unknown LLM provider: '{self._provider}'. "
                f"Supported: openai, google, anthropic, ollama"
            )

        return self._client

    async def answer(
        self,
        question: str,
        chunks: List[Union[DocumentChunk, TableChunk]],
        analysis: QueryAnalysis,
    ) -> Tuple[str, float]:
        """
        Generate an answer using the LLM over retrieved context.

        Returns:
            (answer_text, confidence_score)
        """
        if not chunks:
            return "Bu ma'lumot taqdim etilgan hujjatlarda topilmadi.", 0.0

        context = self._build_context(chunks)
        prompt = USER_PROMPT_TEMPLATE.format(
            question=question,
            context=context,
        )

        with TimingLogger("llm_call", logger, provider=self._provider):
            try:
                raw_response = await self._call_llm(prompt)
                logger.debug("Raw LLM response received", length=len(raw_response))
                answer, confidence = self._parse_response(raw_response)
            except Exception as e:
                error_msg = str(e)
                logger.error("LLM call failed", error=error_msg, exc_info=True)
                
                # Check for rate limit / quota exceeded
                if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                    answer = "⚠️ LLM API limiti tugadi (Quota Exceeded yoki Rate Limit). Iltimos, .env faylida yangi API kalit qo'ying yoki biroz kuting."
                    confidence = 0.0
                else:
                    # Graceful fallback — return best chunk content in Uzbek
                    answer = self._fallback_answer(chunks, question)
                    confidence = 0.25

        # Final safety check — ensure answer is not empty or just whitespace/JSON
        answer = self._sanitize_answer(answer)
        return answer, confidence

    async def _call_llm(self, user_prompt: str) -> str:
        """Dispatch to the appropriate LLM provider."""
        client = self._get_client()

        if self._provider in ("openai", "google", "ollama"):
            response = await client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=settings.LLM_MAX_TOKENS,
                temperature=settings.LLM_TEMPERATURE,
                # Note: response_format json_object not supported by all Gemini endpoints
                # We handle JSON parsing robustly instead
            )
            return response.choices[0].message.content or ""

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
        """
        Parse the LLM JSON response into (answer, confidence).

        Handles:
        - Clean JSON: {"answer": "...", "confidence": 0.9}
        - Markdown-wrapped: ```json\n{...}\n```
        - JSON embedded in text: some text {"answer": "..."} more text
        - Partial JSON: missing fields
        """
        if not raw or not raw.strip():
            return "Javob olinmadi.", 0.0

        # Step 1: Try direct JSON parse
        cleaned = raw.strip()
        try:
            data = json.loads(cleaned)
            return self._extract_from_dict(data)
        except (json.JSONDecodeError, ValueError):
            pass

        # Step 2: Strip markdown code fences (```json ... ``` or ``` ... ```)
        # Handle both opening and closing fences
        fence_pattern = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)
        fence_match = fence_pattern.search(cleaned)
        if fence_match:
            try:
                data = json.loads(fence_match.group(1))
                return self._extract_from_dict(data)
            except (json.JSONDecodeError, ValueError):
                pass

        # Step 3: Find any JSON object in the text using regex
        json_pattern = re.compile(r"\{[\s\S]*\}", re.DOTALL)
        json_match = json_pattern.search(cleaned)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                return self._extract_from_dict(data)
            except (json.JSONDecodeError, ValueError):
                pass

        # Step 4: The LLM returned plain text — treat as answer directly
        # But only if it looks like actual Uzbek/Russian text (not JSON garbage)
        plain = cleaned.replace("```json", "").replace("```", "").strip()

        # If it's meaningful text (not just symbols or broken JSON fragments)
        if len(plain) > 20 and not plain.startswith("{") and not plain.startswith("["):
            logger.warning("LLM returned plain text instead of JSON, using as answer")
            return plain[:2000], 0.4

        logger.error("Cannot extract answer from LLM response", raw=raw[:200])
        return "Javob shakllantirishda xatolik yuz berdi.", 0.0

    def _extract_from_dict(self, data: dict) -> Tuple[str, float]:
        """Extract answer and confidence from a parsed JSON dict."""
        answer = data.get("answer", "").strip()
        confidence = float(data.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))

        if not answer or len(answer) < 5:
            return "Javob shakllantirilmadi.", 0.1

        return answer, confidence

    def _sanitize_answer(self, answer: str) -> str:
        """
        Final safety pass on the answer string:
        - Remove any remaining markdown artifacts
        - Ensure it's not raw JSON
        - Ensure minimum length
        """
        if not answer or not answer.strip():
            return "Bu ma'lumot taqdim etilgan hujjatlarda topilmadi."

        # Remove leading/trailing markdown fences if LLM somehow puts them in
        answer = answer.strip()
        answer = re.sub(r"^```(?:json|uz|ru)?\s*", "", answer)
        answer = re.sub(r"\s*```$", "", answer)
        answer = answer.strip()

        # If the "answer" is actually raw JSON, extract just the answer field
        if answer.startswith("{") and '"answer"' in answer:
            try:
                parsed = json.loads(answer)
                inner = parsed.get("answer", "").strip()
                if inner:
                    return inner
            except Exception:
                pass

        return answer

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
                chunk_label = "JADVAL"
            else:
                content = chunk.content
                chunk_label = "MATN"

            # Increase truncation to 2000 chars to preserve more financial data
            content = content[:2000] if len(content) > 2000 else content
            parts.append(
                f"[{i}] {chunk_label} | Manba: {source}\n{content}"
            )

        return "\n\n" + ("─" * 50) + "\n\n".join(parts)

    def _fallback_answer(
        self, chunks: List[Union[DocumentChunk, TableChunk]], question: str
    ) -> str:
        """
        Emergency fallback when LLM is unavailable.
        Returns the most relevant chunk content with Uzbek prefix.
        """
        if not chunks:
            return "Ma'lumot topilmadi. Iltimos, qayta so'rov yuboring."

        best = chunks[0]
        source = best.source_label
        content = best.summary if isinstance(best, TableChunk) else best.content
        clean_content = self._clean_pdf_text(content)

        # Format as Uzbek paragraph
        return (
            f"«{source}» hujjatidan topilgan ma'lumot:\n\n"
            f"{clean_content[:800]}"
            + ("\n\n[To'liq ma'lumot uchun hujjatni ko'ring]" if len(clean_content) > 800 else "")
        )

    def _clean_pdf_text(self, text: str) -> str:
        """Removes common parser artifacts like 'undefined'"""
        return text.replace("undefined", "").strip()
