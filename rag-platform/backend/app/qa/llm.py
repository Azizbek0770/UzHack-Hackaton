from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import requests

from app.core.logger import get_logger


@dataclass
class LLMResponse:
    """Response from LLM inference."""

    answer: str


class LLMClient:
    """LLM client that enforces strict grounding."""

    def __init__(self, endpoint: Optional[str], api_key: Optional[str]) -> None:
        self._endpoint = endpoint
        self._api_key = api_key
        self._logger = get_logger("llm_client")

    def answer(self, question: str, context: str) -> LLMResponse:
        """Generate an answer grounded strictly in provided context."""

        if not self._endpoint:
            return LLMResponse(answer="")
        payload = {
            "prompt": self._build_prompt(question, context),
        }
        headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}
        try:
            response = requests.post(self._endpoint, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            self._logger.warning("LLM request failed: %s", exc)
            return LLMResponse(answer="")
        answer = data.get("answer") or data.get("output") or data.get("text") or ""
        return LLMResponse(answer=str(answer))

    @staticmethod
    def _build_prompt(question: str, context: str) -> str:
        """Build strict prompt preventing hallucinations."""

        return (
            "You are a financial analyst assistant.\n"
            "Rules:\n"
            "1) Answer only from the provided context.\n"
            "2) Do not invent values or companies.\n"
            "3) If context is insufficient, answer exactly: Insufficient context to answer from provided documents.\n"
            "4) Keep answer concise and factual.\n\n"
            f"Question: {question}\n\nContext:\n{context}\n\nAnswer:"
        )
