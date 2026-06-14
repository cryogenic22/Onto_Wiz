"""
Robust JSON parser for LLM outputs.

Handles common LLM response formats:
1. Direct JSON parse
2. Strip markdown code fences (```json ... ```)
3. Regex extraction of first {...} or [...]

Ported from Transmax RobustParser.
"""

import json
import logging
import re
from typing import Any, Dict, Union

logger = logging.getLogger(__name__)


class RobustParser:
    """Parse JSON from LLM output with multiple fallback strategies."""

    def parse(self, text: str) -> Dict[str, Any]:
        """
        Parse JSON from LLM text output.

        Tries in order:
        1. Direct json.loads()
        2. Strip markdown code fences
        3. Regex extract first JSON object/array
        """
        text = text.strip()
        if not text:
            return {}

        # Strategy 1: Direct parse
        result = self._try_direct(text)
        if result is not None:
            return self._ensure_dict(result)

        # Strategy 2: Strip code fences
        result = self._try_strip_fences(text)
        if result is not None:
            return self._ensure_dict(result)

        # Strategy 3: Regex extraction
        result = self._try_regex_extract(text)
        if result is not None:
            return self._ensure_dict(result)

        logger.warning("Failed to parse JSON from LLM output (length=%d)", len(text))
        return {"raw_text": text, "_parse_failed": True}

    def _try_direct(self, text: str) -> Any:
        """Try direct JSON parse."""
        try:
            return json.loads(text)
        except (json.JSONDecodeError, ValueError):
            return None

    def _try_strip_fences(self, text: str) -> Any:
        """Strip markdown code fences and try parsing."""
        # Match ```json ... ``` or ``` ... ```
        pattern = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            inner = match.group(1).strip()
            try:
                return json.loads(inner)
            except (json.JSONDecodeError, ValueError):
                pass
        return None

    def _try_regex_extract(self, text: str) -> Any:
        """Extract first JSON object or array using regex."""
        # Try object first
        obj_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
        if obj_match:
            try:
                return json.loads(obj_match.group())
            except (json.JSONDecodeError, ValueError):
                pass

        # Try array
        arr_match = re.search(r"\[.*\]", text, re.DOTALL)
        if arr_match:
            try:
                return json.loads(arr_match.group())
            except (json.JSONDecodeError, ValueError):
                pass

        return None

    def _ensure_dict(self, result: Any) -> Dict[str, Any]:
        """Ensure result is a dict. Wrap lists/primitives."""
        if isinstance(result, dict):
            return result
        if isinstance(result, list):
            return {"items": result}
        return {"value": result}
