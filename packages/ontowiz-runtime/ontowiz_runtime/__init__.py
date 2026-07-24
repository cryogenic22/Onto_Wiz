"""ontowiz-runtime — the consumer-facing SDK (Tier A).

A trusted in-process agent imports this directly:

    from ontowiz_runtime import get_context
    ctx = get_context("Why did Brand X lose share?", doc=pack_doc,
                      agent_type="commercial", artifacts=pack_artifacts)
    system_prompt = ctx.system_prompt   # the CTX L3 directory for the LLM

The same get_context() is what ontowiz-serve wraps for the REST and MCP doors.
This package may import ontowiz_spec and ontowiz_ctx only — never Tier B.
"""

from __future__ import annotations

from .artifact_view import ArtifactView, artifact_view
from .catalog import (
    CatalogEntry,
    FunctionSlice,
    SearchHit,
    catalog_index,
    catalog_search,
    function_counts,
    pack_functions,
)
from .comments import Comment, CommentStore
from .context import (
    ContextResult,
    TrustEnvelope,
    context_for_function,
    context_for_pack,
    gate,
    get_context,
)
from .db import Database
from .diff import DiffResult, pack_diff
from .governance import (
    ApprovalRecord,
    AuditRecord,
    ContributionRecord,
    DeltaEvent,
    DeltaRecord,
    GovernanceStore,
)
from .hydrate import (
    HydrationPayload,
    SectionNotServableError,
    hydrate_for_pack,
    hydrate_from_result,
    hydrate_sections,
    servable_sections,
)
from .lineage import LineageEntry, explain_concept
from .registry import LoadedPack, PackRegistry, load_pack
from .registry_view import ArtifactRow, PackDetail, pack_detail
from .telemetry import PackUsage, UsageRecord, UsageStore, catalog_stats

__version__ = "0.1.0"

__all__ = [
    "get_context",
    "context_for_pack",
    "context_for_function",
    "hydrate_sections",
    "hydrate_for_pack",
    "hydrate_from_result",
    "servable_sections",
    "HydrationPayload",
    "SectionNotServableError",
    "catalog_index",
    "CatalogEntry",
    "function_counts",
    "pack_functions",
    "FunctionSlice",
    "catalog_search",
    "SearchHit",
    "artifact_view",
    "ArtifactView",
    "CommentStore",
    "Comment",
    "Database",
    "pack_diff",
    "DiffResult",
    "UsageStore",
    "UsageRecord",
    "PackUsage",
    "catalog_stats",
    "GovernanceStore",
    "DeltaRecord",
    "DeltaEvent",
    "ApprovalRecord",
    "AuditRecord",
    "ContributionRecord",
    "gate",
    "ContextResult",
    "TrustEnvelope",
    "LoadedPack",
    "PackRegistry",
    "load_pack",
    "pack_detail",
    "PackDetail",
    "ArtifactRow",
    "explain_concept",
    "LineageEntry",
]
