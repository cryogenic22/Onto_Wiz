"""Pure deterministic HTML rendering for validated public candidate context."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Iterable, Sequence
from html import escape
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from ontowiz_spec import (
    CandidateArtifact,
    CandidatePackManifest,
    DecisionContract,
    PublicEvalCase,
)

_FORBIDDEN_CONTENT_MARKERS = (
    "-----begin private key",
    "api-key",
    "api_key",
    "authorization: bearer",
    "bearer ",
    "oracle answer",
    "private receipt",
    "private_receipt",
    "protected case",
    "protected_case",
    "runtime authority",
    "signing key",
    "vault://",
)

_CSP = "default-src 'none'; style-src 'unsafe-inline'; " "base-uri 'none'; form-action 'none'"
_STYLE = """
:root {
  --ink:#17221d; --muted:#637068; --paper:#f5f2e9; --card:#fffdf7;
  --line:#d9d4c5; --accent:#086c5c; --warn:#9d3b18;
}
* { box-sizing:border-box; }
body {
  margin:0; background:var(--paper); color:var(--ink);
  font:15px/1.55 ui-sans-serif,system-ui,sans-serif;
}
main { width:min(1120px,calc(100% - 32px)); margin:0 auto; padding:42px 0 72px; }
h1,h2,h3,h4,p { margin-top:0; }
h1 { font-size:clamp(2rem,5vw,4rem); line-height:1; }
h2 { margin-top:44px; border-bottom:1px solid var(--line); padding-bottom:10px; }
h3 { margin-bottom:5px; }
h4 {
  margin:16px 0 6px; font-size:.78rem; letter-spacing:.08em;
  text-transform:uppercase;
}
code { overflow-wrap:anywhere; color:var(--accent); }
ul { margin:0; padding-left:18px; }
.hero { padding:32px; border:1px solid var(--line); background:var(--card); }
.notice { border-left:5px solid var(--warn); padding:12px 16px; background:#fff4ec; }
.grid {
  display:grid; grid-template-columns:repeat(auto-fit,minmax(330px,1fr)); gap:16px;
}
.card,.case {
  border:1px solid var(--line); background:var(--card); padding:22px;
  break-inside:avoid;
}
.case { margin-bottom:12px; }
.card-head { display:flex; justify-content:space-between; gap:18px; align-items:flex-start; }
.eyebrow {
  color:var(--accent); font-size:.75rem; font-weight:700; letter-spacing:.1em;
  text-transform:uppercase;
}
.status {
  border:1px solid var(--line); border-radius:999px; padding:4px 9px;
  font-size:.72rem; text-transform:uppercase;
}
.subgrid {
  display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:12px;
}
.compact,.scenario {
  display:grid; grid-template-columns:minmax(120px,180px) 1fr; margin:0;
}
dt { font-weight:700; }
dd { margin:0 0 8px; }
.muted { color:var(--muted); }
footer { margin-top:48px; color:var(--muted); font-size:.85rem; }
@media print { body { background:#fff; } main { width:100%; } }
""".strip()
_NOTICE = (
    "<strong>Not approved for production.</strong> This explorer presents public "
    "synthetic candidate context only. It grants no release, runtime, approval, "
    "diagnostic, prescribing, or operational authority."
)
_FOOTER = (
    "Generated deterministically from validated canonical candidate models. "
    "Source and evidence identifiers are shown; raw source content, credentials, "
    "protected evaluations, and private receipts are not accepted by this renderer."
)


_CANDIDATE_ARTIFACT_PATH = re.compile(
    r"pack/(?:scope|ontology|metrics|methods|policies|retrieval|"
    r"workflows|tools|governance)/"
    r"[A-Za-z0-9][A-Za-z0-9._-]*\.(?:json|yaml)"
)
_CANDIDATE_DECISION_PATH = re.compile(r"pack/scope/[A-Za-z0-9][A-Za-z0-9._-]*\.(?:json|yaml)")
_CANDIDATE_EVALUATION_PATH = re.compile(
    r"pack/evaluations/[A-Za-z0-9][A-Za-z0-9._-]*\.(?:json|yaml)"
)
_SHA256_PATTERN = r"^sha256:[0-9a-f]{64}$"


class ExplorerContentError(ValueError):
    """Validated candidate context cannot be rendered as a safe public explorer."""


CandidateExplorerSourceDocument = tuple[
    str,
    CandidatePackManifest | CandidateArtifact | DecisionContract | PublicEvalCase,
    bytes,
]


class CandidateExplorerDocument(BaseModel):
    """Exact raw candidate-document identity retained by the normalized context."""

    path: str = Field(min_length=1)
    document_kind: Literal["manifest", "artifact", "decision", "evaluation"]
    document_id: str = Field(min_length=1)
    sha256: str = Field(pattern=_SHA256_PATTERN)

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def path_matches_kind(self) -> CandidateExplorerDocument:
        if self.path != unicodedata.normalize("NFC", self.path) or "\\" in self.path:
            raise ValueError("context document path is not canonical")
        matches = {
            "manifest": self.path == "pack/pack.yaml",
            "artifact": _CANDIDATE_ARTIFACT_PATH.fullmatch(self.path) is not None,
            "decision": _CANDIDATE_DECISION_PATH.fullmatch(self.path) is not None,
            "evaluation": _CANDIDATE_EVALUATION_PATH.fullmatch(self.path) is not None,
        }
        if not matches[self.document_kind]:
            raise ValueError("context document path differs from its kind")
        return self


class CandidateExplorerContext(BaseModel):
    """Validated normalized input and raw-document bindings for one explorer."""

    format: Literal["ontowiz-context-model"]
    format_version: Literal[1]
    workspace_id: str = Field(min_length=1)
    revision: int = Field(ge=0)
    manifest: CandidatePackManifest
    artifacts: tuple[CandidateArtifact, ...] = ()
    decisions: tuple[DecisionContract, ...] = ()
    evaluations: tuple[PublicEvalCase, ...] = ()
    documents: tuple[CandidateExplorerDocument, ...]

    model_config = ConfigDict(extra="forbid", frozen=True)

    @model_validator(mode="after")
    def graph_is_exact(self) -> CandidateExplorerContext:
        _validate_normalized_context(self)
        return self


def _canonical_json_value(value: object) -> bytes:
    serialized = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return (unicodedata.normalize("NFC", serialized) + "\n").encode("utf-8")


def _canonical_model(model: BaseModel) -> bytes:
    return _canonical_json_value(model.model_dump(mode="json"))


def _sha256(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _safe(value: object) -> str:
    return escape(unicodedata.normalize("NFC", str(value)), quote=True)


def _items(values: Iterable[object]) -> str:
    rendered = tuple(_safe(value) for value in values)
    if not rendered:
        return '<span class="muted">None declared</span>'
    return "<ul>" + "".join(f"<li>{value}</li>" for value in rendered) + "</ul>"


def _applicability(artifact: CandidateArtifact | DecisionContract | PublicEvalCase) -> str:
    applicability = artifact.applicability
    rows = (
        ("Markets", applicability.markets),
        ("Lifecycle stages", applicability.lifecycle_stages),
        ("Products", applicability.products),
        ("Audiences", applicability.audiences),
    )
    body = "".join(f"<dt>{_safe(label)}</dt><dd>{_items(values)}</dd>" for label, values in rows)
    return (
        '<dl class="compact">'
        f"<dt>Effective from</dt><dd>{_safe(applicability.effective_from.isoformat())}</dd>"
        f"{body}</dl>"
    )


def _validate_normalized_context(context: CandidateExplorerContext) -> None:
    if context.artifacts != tuple(sorted(context.artifacts, key=lambda item: item.id)):
        raise ValueError("context artifacts are not sorted")
    if context.decisions != tuple(sorted(context.decisions, key=lambda item: item.id)):
        raise ValueError("context decisions are not sorted")
    if context.evaluations != tuple(sorted(context.evaluations, key=lambda item: item.id)):
        raise ValueError("context evaluations are not sorted")
    if context.documents != tuple(sorted(context.documents, key=lambda item: item.path)):
        raise ValueError("context document bindings are not sorted")

    document_ids = tuple(item.id for item in context.artifacts) + tuple(
        item.id for item in context.decisions
    )
    evaluation_ids = tuple(item.id for item in context.evaluations)
    if len(document_ids) != len(set(document_ids)) or len(evaluation_ids) != len(
        set(evaluation_ids)
    ):
        raise ValueError("explorer context contains duplicate ids")

    expected_keys = {
        ("manifest", context.manifest.pack_id),
        *(("artifact", item.id) for item in context.artifacts),
        *(("decision", item.id) for item in context.decisions),
        *(("evaluation", item.id) for item in context.evaluations),
    }
    actual_keys = tuple(
        (binding.document_kind, binding.document_id) for binding in context.documents
    )
    actual_paths = tuple(binding.path for binding in context.documents)
    if (
        len(actual_keys) != len(set(actual_keys))
        or len(actual_paths) != len(set(actual_paths))
        or set(actual_keys) != expected_keys
    ):
        raise ValueError("candidate context document inventory is not exact")

    actual_artifacts = tuple(
        sorted(
            (
                (binding.document_id, binding.sha256)
                for binding in context.documents
                if binding.document_kind in {"artifact", "decision"}
            ),
            key=lambda item: item[0],
        )
    )
    declared_artifacts = tuple(
        (item.artifact_id, item.digest) for item in context.manifest.artifact_digests
    )
    if declared_artifacts != actual_artifacts:
        raise ValueError("candidate manifest digest inventory is not exact")

    decision_ids = {decision.id for decision in context.decisions}
    known_context = set(document_ids)
    declared_suites = {suite.value for suite in context.manifest.public_evaluation_suites}
    if any(
        evaluation.decision_id not in decision_ids
        or evaluation.suite.value not in declared_suites
        or not set(evaluation.required_context).issubset(known_context)
        for evaluation in context.evaluations
    ):
        raise ValueError("public evaluation graph is not exact")

    serialized_context = json.dumps(
        context.model_dump(mode="json"),
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).casefold()
    if any(marker in serialized_context for marker in _FORBIDDEN_CONTENT_MARKERS):
        raise ValueError("explorer context contains forbidden content")


def _document_kind(
    document: CandidatePackManifest | CandidateArtifact | DecisionContract | PublicEvalCase,
) -> Literal["manifest", "artifact", "decision", "evaluation"]:
    if isinstance(document, CandidatePackManifest):
        return "manifest"
    if isinstance(document, CandidateArtifact):
        return "artifact"
    if isinstance(document, DecisionContract):
        return "decision"
    if isinstance(document, PublicEvalCase):
        return "evaluation"
    raise ExplorerContentError("explorer requires validated candidate models")


def _validate_raw_document(
    document: CandidatePackManifest | CandidateArtifact | DecisionContract | PublicEvalCase,
    payload: bytes,
) -> None:
    validated: CandidatePackManifest | CandidateArtifact | DecisionContract | PublicEvalCase
    try:
        body = json.loads(payload)
        if _canonical_json_value(body) != payload:
            raise ValueError("payload is not canonical")
        if isinstance(document, CandidatePackManifest):
            validated = CandidatePackManifest.model_validate(body)
        elif isinstance(document, CandidateArtifact):
            validated = CandidateArtifact.model_validate(body)
        elif isinstance(document, DecisionContract):
            validated = DecisionContract.model_validate(body)
        elif isinstance(document, PublicEvalCase):
            validated = PublicEvalCase.model_validate(body)
        else:
            raise TypeError("unsupported candidate document")
    except (
        RecursionError,
        UnicodeDecodeError,
        ValidationError,
        ValueError,
        TypeError,
    ) as exc:
        raise ExplorerContentError("candidate document payload is invalid") from exc
    if validated != document:
        raise ExplorerContentError("candidate document payload differs from validated context")


def build_candidate_explorer_context(
    *,
    workspace_id: str,
    revision: int,
    documents: Sequence[CandidateExplorerSourceDocument],
) -> CandidateExplorerContext:
    """Normalize an exact validated candidate document set and its raw bindings."""

    artifacts: list[CandidateArtifact] = []
    decisions: list[DecisionContract] = []
    evaluations: list[PublicEvalCase] = []
    manifests: list[CandidatePackManifest] = []
    bindings: list[CandidateExplorerDocument] = []
    for path, document, payload in documents:
        if not isinstance(payload, bytes):
            raise ExplorerContentError("candidate document payload must be bytes")
        kind = _document_kind(document)
        _validate_raw_document(document, payload)
        if isinstance(document, CandidatePackManifest):
            manifests.append(document)
            document_id = document.pack_id
        elif isinstance(document, CandidateArtifact):
            artifacts.append(document)
            document_id = document.id
        elif isinstance(document, DecisionContract):
            decisions.append(document)
            document_id = document.id
        else:
            evaluations.append(document)
            document_id = document.id
        try:
            bindings.append(
                CandidateExplorerDocument(
                    path=path,
                    document_kind=kind,
                    document_id=document_id,
                    sha256=_sha256(payload),
                )
            )
        except ValidationError as exc:
            raise ExplorerContentError("candidate document path is invalid") from exc
    if len(manifests) != 1:
        raise ExplorerContentError("candidate context requires one pack manifest")
    try:
        return CandidateExplorerContext(
            format="ontowiz-context-model",
            format_version=1,
            workspace_id=workspace_id,
            revision=revision,
            manifest=manifests[0],
            artifacts=tuple(sorted(artifacts, key=lambda item: item.id)),
            decisions=tuple(sorted(decisions, key=lambda item: item.id)),
            evaluations=tuple(sorted(evaluations, key=lambda item: item.id)),
            documents=tuple(sorted(bindings, key=lambda item: item.path)),
        )
    except ValidationError as exc:
        raise ExplorerContentError(str(exc)) from exc


def _validated_context(context: CandidateExplorerContext) -> CandidateExplorerContext:
    try:
        return CandidateExplorerContext.model_validate(context.model_dump(mode="json"))
    except (AttributeError, ValidationError) as exc:
        raise ExplorerContentError("explorer context model is invalid") from exc


def candidate_explorer_context_bytes(context: CandidateExplorerContext) -> bytes:
    """Serialize the exact validated normalized explorer input deterministically."""

    return _canonical_model(_validated_context(context))


def _render_artifact(artifact: CandidateArtifact) -> str:
    optional = ""
    if artifact.formula is not None:
        optional += (
            '<div class="subgrid">'
            f"<div><h4>Formula</h4><code>{_safe(artifact.formula)}</code></div>"
            f"<div><h4>Inputs</h4>{_items(artifact.formula_inputs)}</div>"
            f"<div><h4>Unit</h4><p>{_safe(artifact.unit)}</p></div>"
            f"<div><h4>Grain</h4><p>{_safe(artifact.grain)}</p></div>"
            "</div>"
        )
    if artifact.alternatives or artifact.disconfirming_conditions:
        optional += (
            '<div class="subgrid">'
            f"<div><h4>Alternatives</h4>{_items(artifact.alternatives)}</div>"
            "<div><h4>Disconfirming conditions</h4>"
            f"{_items(artifact.disconfirming_conditions)}</div>"
            "</div>"
        )
    return (
        f'<article class="card" id="artifact-{_safe(artifact.id)}">'
        '<div class="card-head">'
        f'<div><span class="eyebrow">{_safe(artifact.kind.value)}</span>'
        f"<h3>{_safe(artifact.name)}</h3><code>{_safe(artifact.id)}</code></div>"
        f'<span class="status">{_safe(artifact.lifecycle.value)}</span></div>'
        f"<p>{_safe(artifact.definition)}</p>"
        '<div class="subgrid">'
        f"<div><h4>Owner</h4><p>{_safe(artifact.owner_role)}</p></div>"
        f"<div><h4>Confidence</h4><p>{artifact.confidence:.2f}</p></div>"
        f"<div><h4>Claim type</h4><p>{_safe(artifact.claim_type.value)}</p></div>"
        f"<div><h4>Risk</h4><p>{_safe(artifact.risk_level.value)}</p></div>"
        "</div>"
        f"{optional}"
        '<div class="subgrid">'
        f"<div><h4>Source identifiers</h4>{_items(artifact.source_document_ids)}</div>"
        f"<div><h4>Evidence identifiers</h4>{_items(artifact.evidence_refs)}</div>"
        f"<div><h4>Abstention</h4>{_items(artifact.abstention_conditions)}</div>"
        "<div><h4>Provenance</h4>"
        f"<p>{_safe(artifact.provenance.mode.value)} · "
        f"{_safe(artifact.provenance.supplied_by)}</p></div>"
        "</div>"
        f"<h4>Applicability</h4>{_applicability(artifact)}"
        "</article>"
    )


def _render_decision(decision: DecisionContract) -> str:
    return (
        f'<article class="card" id="decision-{_safe(decision.id)}">'
        '<div class="card-head"><div><span class="eyebrow">decision contract</span>'
        f"<h3>{_safe(decision.decision)}</h3><code>{_safe(decision.id)}</code></div>"
        f'<span class="status">{_safe(decision.action_mode)}</span></div>'
        '<div class="subgrid">'
        f"<div><h4>Human-owned actions</h4>{_items(decision.human_owned_actions)}</div>"
        f"<div><h4>Out of scope</h4>{_items(decision.out_of_scope)}</div>"
        "<div><h4>Materially unsafe answers</h4>"
        f"{_items(decision.materially_unsafe_answers)}</div>"
        f"<div><h4>Owner</h4><p>{_safe(decision.owner_role)}</p></div>"
        "</div>"
        f"<h4>Applicability</h4>{_applicability(decision)}"
        "</article>"
    )


def _render_evaluation(evaluation: PublicEvalCase) -> str:
    scenario = "".join(
        f"<dt>{_safe(item.name)}</dt><dd>{_safe(item.value)}</dd>" for item in evaluation.scenario
    )
    return (
        f'<article class="case" id="evaluation-{_safe(evaluation.id)}">'
        '<div class="card-head"><div>'
        f'<span class="eyebrow">{_safe(evaluation.suite.value)} · public synthetic</span>'
        f"<h3>{_safe(evaluation.id)}</h3><code>{_safe(evaluation.decision_id)}</code></div>"
        '<span class="status">candidate</span></div>'
        f'<dl class="scenario">{scenario}</dl>'
        '<div class="subgrid">'
        f"<div><h4>Required</h4>{_items(evaluation.required_behaviours)}</div>"
        f"<div><h4>Prohibited</h4>{_items(evaluation.prohibited_behaviours)}</div>"
        f"<div><h4>Deliberately missing</h4>{_items(evaluation.deliberately_missing)}</div>"
        f"<div><h4>Evidence expectations</h4>{_items(evaluation.evidence_expectations)}</div>"
        f"<div><h4>Critical failures</h4>{_items(evaluation.critical_failures)}</div>"
        f"<div><h4>Required context</h4>{_items(evaluation.required_context)}</div>"
        "</div></article>"
    )


def render_candidate_explorer(context: CandidateExplorerContext) -> bytes:
    """Render deterministic self-contained HTML from one validated context model."""

    validated = _validated_context(context)
    manifest = validated.manifest
    ordered_artifacts = validated.artifacts
    ordered_decisions = validated.decisions
    ordered_evaluations = validated.evaluations
    artifact_cards = "\n".join(_render_artifact(item) for item in ordered_artifacts)
    decision_cards = "\n".join(_render_decision(item) for item in ordered_decisions)
    evaluation_cards = "\n".join(_render_evaluation(item) for item in ordered_evaluations)
    identity = (
        f"Version {_safe(manifest.pack_version)} · {_safe(manifest.schema_target)} "
        f"revision {manifest.schema_revision}"
    )
    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<meta http-equiv="Content-Security-Policy" content="{_CSP}">
<title>{_safe(manifest.pack_id)} · OntoWiz candidate explorer</title>
<style>{_STYLE}</style>
</head>
<body>
<main>
<header class="hero">
<span class="eyebrow">OntoWiz authoring kit · candidate-only</span>
<h1>{_safe(manifest.pack_id)}</h1>
<p>{identity}</p>
<div class="notice">{_NOTICE}</div>
</header>
<section><h2>Decision boundaries</h2><div class="grid">{decision_cards}</div></section>
<section><h2>Candidate context</h2><div class="grid">{artifact_cards}</div></section>
<section><h2>Public behavior cases</h2>{evaluation_cards}</section>
<footer>{_FOOTER}</footer>
</main>
</body>
</html>
"""
    return unicodedata.normalize("NFC", document).encode("utf-8")
