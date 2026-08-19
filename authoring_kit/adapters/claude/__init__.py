"""Claude surface for the provider-neutral OntoWiz adapter protocol."""

from typing import TypeAlias

from ontowiz_authoring.adapters import AdapterSession

ClaudeAdapterSession: TypeAlias = AdapterSession

__all__ = ["ClaudeAdapterSession"]
