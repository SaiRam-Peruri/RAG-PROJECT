"""
LLM client with retry logic and structured access.
"""

from __future__ import annotations

from typing import List, Dict, Optional

from openai import OpenAI

from ..config import settings
from ..logging_config import get_logger
from .retry import retry

logger = get_logger("llm")


class LLMClient:
    """Wrapper around OpenAI with retry, logging, and model management."""

    def __init__(self, api_key: Optional[str] = None):
        key = api_key or settings.require_api_key()
        self._client = OpenAI(api_key=key)

    @retry(max_retries=3, base_delay=1.0)
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 3000,
    ) -> str:
        """Send a chat completion request with retry."""
        model = model or settings.llm_model
        logger.debug("LLM request: model=%s, messages=%d, temp=%.1f", model, len(messages), temperature)

        response = self._client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        content = response.choices[0].message.content or ""
        logger.debug("LLM response: %d chars", len(content))
        return content

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 3000,
    ) -> str:
        """Convenience: system + user prompt → response text."""
        return self.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )


# Singleton
_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
