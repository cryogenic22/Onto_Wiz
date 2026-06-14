"""
Onto_Wiz Knowledge Orchestration Module

Context assembly, document parsing, LLM extraction, and quality assurance
for the SpecOmagic integration.

Import direction: src/knowledge/ -> imports from src/core/ only.
"""

from .models import FewShotExample, ContextPackage
from .protocols import ContextProvider
from .few_shot_store import FewShotStore
from .assembler import ContextAssembler

__all__ = [
    "FewShotExample",
    "ContextPackage",
    "ContextProvider",
    "FewShotStore",
    "ContextAssembler",
]
