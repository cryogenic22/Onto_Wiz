"""
Knowledge module protocols (interfaces).

ContextProvider: Protocol for context assembly implementations.
"""

from typing import Protocol

from .models import ContextPackage


class ContextProvider(Protocol):
    """Protocol for context assembly — query + agent_type + budget -> ContextPackage."""

    def assemble(
        self, query: str, agent_type: str, max_tokens: int
    ) -> ContextPackage: ...
