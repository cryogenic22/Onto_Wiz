"""
Provider-neutral LLM service with retry resilience.

Protocol-based design allows swapping providers without touching extraction logic.
Ported from Transmax resilience patterns.
"""

import logging
import os
import time
from typing import Dict, Optional, Protocol

from .json_parser import RobustParser

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
BASE_DELAY = 1.0  # seconds
BACKOFF_FACTOR = 2.0


class LLMService(Protocol):
    """Protocol for LLM completion services."""

    def complete(
        self, prompt: str, system: str = "", max_tokens: int = 2000
    ) -> str: ...

    def complete_json(
        self, prompt: str, system: str = "", max_tokens: int = 2000
    ) -> Dict: ...


class OpenAILLMService:
    """
    OpenAI-compatible LLM service with exponential backoff retry.

    Uses the openai library if available, otherwise raises ImportError.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        self._model = model
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._base_url = base_url
        self._parser = RobustParser()

    def complete(
        self, prompt: str, system: str = "", max_tokens: int = 2000
    ) -> str:
        """Complete a prompt with retry logic."""
        return self._call_with_retry(prompt, system, max_tokens)

    def complete_json(
        self, prompt: str, system: str = "", max_tokens: int = 2000
    ) -> Dict:
        """Complete and parse response as JSON using RobustParser."""
        raw = self._call_with_retry(prompt, system, max_tokens)
        return self._parser.parse(raw)

    def _call_with_retry(
        self, prompt: str, system: str, max_tokens: int
    ) -> str:
        """Call LLM with exponential backoff retry."""
        last_error: Optional[Exception] = None

        for attempt in range(MAX_RETRIES):
            try:
                return self._raw_call(prompt, system, max_tokens)
            except Exception as exc:
                last_error = exc
                if attempt < MAX_RETRIES - 1:
                    delay = BASE_DELAY * (BACKOFF_FACTOR ** attempt)
                    logger.warning(
                        "LLM call failed (attempt %d/%d): %s. Retrying in %.1fs",
                        attempt + 1,
                        MAX_RETRIES,
                        exc,
                        delay,
                    )
                    time.sleep(delay)

        raise RuntimeError(
            f"LLM call failed after {MAX_RETRIES} attempts: {last_error}"
        )

    def _raw_call(self, prompt: str, system: str, max_tokens: int) -> str:
        """Make the actual API call."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package required for OpenAILLMService. "
                "Install with: pip install openai"
            )

        client_kwargs = {}
        if self._api_key:
            client_kwargs["api_key"] = self._api_key
        if self._base_url:
            client_kwargs["base_url"] = self._base_url

        client = OpenAI(**client_kwargs)

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=self._model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.1,
        )
        return response.choices[0].message.content or ""


class MockLLMService:
    """Mock LLM service for testing. Returns predefined responses."""

    def __init__(self, responses: Optional[Dict[str, str]] = None) -> None:
        self._responses = responses or {}
        self._default_response = '{"patterns": [], "entities": []}'
        self._call_count = 0
        self._parser = RobustParser()

    def complete(
        self, prompt: str, system: str = "", max_tokens: int = 2000
    ) -> str:
        self._call_count += 1
        # Check for matching response by keyword
        for key, response in self._responses.items():
            if key.lower() in prompt.lower():
                return response
        return self._default_response

    def complete_json(
        self, prompt: str, system: str = "", max_tokens: int = 2000
    ) -> Dict:
        raw = self.complete(prompt, system, max_tokens)
        return self._parser.parse(raw)

    @property
    def call_count(self) -> int:
        return self._call_count
