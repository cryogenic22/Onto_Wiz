"""Strict public contracts for an externally custodied held-out evaluation."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Mapping
from typing import Any, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

Digest: TypeAlias = str

_DIGEST_PATTERN = r"^sha256:[0-9a-f]{64}$"
_IDENTIFIER_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$"
_UTC_PATTERN = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
_FORBIDDEN_SCENARIO_KEYS = {
    "answer_key",
    "arm_mapping",
    "critical_failure",
    "critical_failures",
    "expected_answer",
    "hidden_predicate",
    "hidden_rubric",
    "oracle",
    "oracles",
    "private_case_id",
    "protected_path",
    "rubric",
    "rubrics",
    "secret",
    "signing_key",
    "vault_path",
}


def canonical_json(value: object) -> bytes:
    """Serialize one contract value deterministically for digest commitments."""

    serialized = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return (unicodedata.normalize("NFC", serialized) + "\n").encode("utf-8")


def digest_value(value: object) -> Digest:
    """Return the SHA-256 commitment for a canonical JSON value."""

    return "sha256:" + hashlib.sha256(canonical_json(value)).hexdigest()


class FrozenContract(BaseModel):
    """Base for immutable, extra-forbid evaluator boundary contracts."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        allow_inf_nan=False,
    )


class EvaluationArm(FrozenContract):
    """One pre-registered arm, represented only by an opaque configuration digest."""

    arm_id: str = Field(pattern=_IDENTIFIER_PATTERN)
    configuration_digest: Digest = Field(pattern=_DIGEST_PATTERN)


class PreregistrationRecord(FrozenContract):
    """Externally supplied preregistration; only an approved record may execute."""

    format: Literal["ontowiz-evaluation-preregistration"]
    format_version: Literal[1]
    status: Literal["draft", "approved"]
    preregistration_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    candidate_author: str = Field(pattern=_IDENTIFIER_PATTERN)
    approved_by: str | None = Field(default=None, pattern=_IDENTIFIER_PATTERN)
    approved_at: str | None = Field(default=None, pattern=_UTC_PATTERN)
    approval_signature_digest: Digest | None = Field(default=None, pattern=_DIGEST_PATTERN)
    arms: tuple[EvaluationArm, ...]
    repetitions: int = Field(ge=1, le=100)
    expected_case_count: int = Field(ge=1, le=100_000)
    scorer_ids: tuple[str, ...]
    adjudicator_id: str | None = Field(default=None, pattern=_IDENTIFIER_PATTERN)
    minimum_score: float = Field(ge=0.0, le=1.0)
    maximum_critical_failures: int = Field(ge=0)

    @model_validator(mode="after")
    def ordered_unique_contract(self) -> PreregistrationRecord:
        if not self.arms or tuple(arm.arm_id for arm in self.arms) != tuple(
            sorted({arm.arm_id for arm in self.arms})
        ):
            raise ValueError("preregistered arms must be non-empty, unique, and ordered")
        if not self.scorer_ids or self.scorer_ids != tuple(sorted(set(self.scorer_ids))):
            raise ValueError("scorer ids must be non-empty, unique, and ordered")
        return self


class VaultIsolationProof(FrozenContract):
    """Attestation that draft and worker principals cannot list or read the vault."""

    format: Literal["ontowiz-vault-isolation-proof"]
    format_version: Literal[1]
    proof_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    proof_signature_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    drafting_principal: str = Field(pattern=_IDENTIFIER_PATTERN)
    worker_principal: str = Field(pattern=_IDENTIFIER_PATTERN)
    evaluator_principal: str = Field(pattern=_IDENTIFIER_PATTERN)
    drafting_list_denied: bool
    drafting_read_denied: bool
    worker_list_denied: bool
    worker_read_denied: bool
    checked_at: str = Field(pattern=_UTC_PATTERN)


class FrozenSuiteDescriptor(FrozenContract):
    """Opaque lock for a protected suite held entirely by the custodian."""

    format: Literal["ontowiz-frozen-evaluation-suite"]
    format_version: Literal[1]
    suite_id: str = Field(pattern=_IDENTIFIER_PATTERN)
    suite_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    preregistration_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    isolation_proof_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    inventory_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    lock_signature_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    case_count: int = Field(ge=1, le=100_000)
    frozen_at: str = Field(pattern=_UTC_PATTERN)


class ExecutionDigests(FrozenContract):
    """Exact environment commitments held fixed across paired runs."""

    agent_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    adapter_build_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    model_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    prompt_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    retrieval_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    tool_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    data_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    evaluator_build_digest: Digest = Field(pattern=_DIGEST_PATTERN)


class EvaluationRunPlan(FrozenContract):
    """Approved immutable plan that binds candidate, suite, arms, and environment."""

    format: Literal["ontowiz-evaluation-run-plan"]
    format_version: Literal[1]
    run_id: str = Field(pattern=_IDENTIFIER_PATTERN)
    candidate_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    preregistration_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    suite_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    arms: tuple[EvaluationArm, ...]
    repetitions: int = Field(ge=1, le=100)
    drafting_principal: str = Field(pattern=_IDENTIFIER_PATTERN)
    worker_principal: str = Field(pattern=_IDENTIFIER_PATTERN)
    evaluator_principal: str = Field(pattern=_IDENTIFIER_PATTERN)
    blinding_commitment_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    execution: ExecutionDigests
    approved_plan_signature_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    created_at: str = Field(pattern=_UTC_PATTERN)

    @model_validator(mode="after")
    def ordered_unique_arms(self) -> EvaluationRunPlan:
        if not self.arms or tuple(arm.arm_id for arm in self.arms) != tuple(
            sorted({arm.arm_id for arm in self.arms})
        ):
            raise ValueError("run-plan arms must be non-empty, unique, and ordered")
        return self

    @property
    def run_plan_digest(self) -> Digest:
        return digest_value(self.model_dump(mode="json"))


def _assert_public_scenario(value: object) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9]+", "_", str(key).casefold()).strip("_")
            if normalized in _FORBIDDEN_SCENARIO_KEYS:
                raise ValueError("public scenario contains a protected field")
            _assert_public_scenario(child)
    elif isinstance(value, list):
        for child in value:
            _assert_public_scenario(child)


class PublicScenario(FrozenContract):
    """The only scenario envelope that an adapter worker may receive."""

    format: Literal["ontowiz-public-evaluation-scenario"]
    format_version: Literal[1]
    scenario_handle: str = Field(pattern=_IDENTIFIER_PATTERN)
    instructions: str = Field(min_length=1, max_length=100_000)
    inputs: dict[str, JsonValue]
    deliberately_missing: tuple[str, ...] = ()

    @model_validator(mode="after")
    def contains_no_protected_fields(self) -> PublicScenario:
        _assert_public_scenario(self.inputs)
        if self.deliberately_missing != tuple(sorted(set(self.deliberately_missing))):
            raise ValueError("deliberately-missing fields must be unique and ordered")
        return self


class WorkerEnvelope(FrozenContract):
    """Blind, public-only input delivered to one ephemeral adapter worker."""

    format: Literal["ontowiz-evaluation-worker-envelope"]
    format_version: Literal[1]
    run_id: str = Field(pattern=_IDENTIFIER_PATTERN)
    candidate_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    suite_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    scenario: PublicScenario
    blind_arm_token: Digest = Field(pattern=_DIGEST_PATTERN)
    repetition: int = Field(ge=1, le=100)
    worker_principal: str = Field(pattern=_IDENTIFIER_PATTERN)
    execution: ExecutionDigests

    @property
    def envelope_digest(self) -> Digest:
        return digest_value(self.model_dump(mode="json"))


class ToolCallTrace(FrozenContract):
    """Content-bound tool-call metadata without raw tool payloads."""

    tool_id: str = Field(pattern=_IDENTIFIER_PATTERN)
    arguments_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    result_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    status: Literal["ok", "error", "refused"]


class AgentTrace(FrozenContract):
    """Complete private trace returned by the isolated worker."""

    format: Literal["ontowiz-evaluation-agent-trace"]
    format_version: Literal[1]
    run_id: str = Field(pattern=_IDENTIFIER_PATTERN)
    candidate_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    suite_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    scenario_handle: str = Field(pattern=_IDENTIFIER_PATTERN)
    blind_arm_token: Digest = Field(pattern=_DIGEST_PATTERN)
    repetition: int = Field(ge=1, le=100)
    worker_principal: str = Field(pattern=_IDENTIFIER_PATTERN)
    execution: ExecutionDigests
    output: str = Field(min_length=1, max_length=1_000_000)
    citation_ids: tuple[str, ...]
    retrieved_context_ids: tuple[str, ...]
    tool_calls: tuple[ToolCallTrace, ...]
    complete: bool

    @model_validator(mode="after")
    def ordered_trace_bindings(self) -> AgentTrace:
        if self.citation_ids != tuple(sorted(set(self.citation_ids))):
            raise ValueError("citation ids must be unique and ordered")
        if self.retrieved_context_ids != tuple(sorted(set(self.retrieved_context_ids))):
            raise ValueError("retrieved-context ids must be unique and ordered")
        return self

    @property
    def trace_digest(self) -> Digest:
        return digest_value(self.model_dump(mode="json"))


class WorkerIsolationAttestation(FrozenContract):
    """Externally verifiable proof for one fresh worker runtime."""

    format: Literal["ontowiz-worker-isolation-attestation"]
    format_version: Literal[1]
    run_id: str = Field(pattern=_IDENTIFIER_PATTERN)
    envelope_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    worker_principal: str = Field(pattern=_IDENTIFIER_PATTERN)
    runtime_instance_id: str = Field(pattern=_IDENTIFIER_PATTERN)
    adapter_build_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    process_isolation_proof_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    vault_list_denied: bool
    vault_read_denied: bool
    fresh_runtime: bool
    state_reused: bool
    checked_at: str = Field(pattern=_UTC_PATTERN)


class IsolatedWorkerResult(FrozenContract):
    """One trace paired with proof of its fresh isolated runtime."""

    trace: AgentTrace
    isolation: WorkerIsolationAttestation


class PrivateCaseResult(FrozenContract):
    """Private scorer output; it is never returned by the public coordinator."""

    format: Literal["ontowiz-private-case-result"]
    format_version: Literal[1]
    scenario_handle: str = Field(pattern=_IDENTIFIER_PATTERN)
    blind_arm_token: Digest = Field(pattern=_DIGEST_PATTERN)
    repetition: int = Field(ge=1, le=100)
    trace_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    deterministic_score: float = Field(ge=0.0, le=1.0)
    rubric_score: float = Field(ge=0.0, le=1.0)
    passed: bool
    critical_failure_ids: tuple[str, ...]
    scorer_ids: tuple[str, ...]
    scorer_agreement: bool
    adjudicated_by: str | None = Field(default=None, pattern=_IDENTIFIER_PATTERN)
    adjudication_digest: Digest | None = Field(default=None, pattern=_DIGEST_PATTERN)

    @model_validator(mode="after")
    def ordered_private_bindings(self) -> PrivateCaseResult:
        if self.critical_failure_ids != tuple(sorted(set(self.critical_failure_ids))):
            raise ValueError("critical-failure ids must be unique and ordered")
        if self.scorer_ids != tuple(sorted(set(self.scorer_ids))):
            raise ValueError("scorer ids must be unique and ordered")
        if self.scorer_agreement and (
            self.adjudicated_by is not None or self.adjudication_digest is not None
        ):
            raise ValueError("an agreed result cannot claim adjudication")
        return self

    @property
    def result_digest(self) -> Digest:
        return digest_value(self.model_dump(mode="json"))


class ReceiptResultBinding(FrozenContract):
    """Private receipt binding between a pre-registered arm and scored result."""

    arm_id: str = Field(pattern=_IDENTIFIER_PATTERN)
    blind_arm_token: Digest = Field(pattern=_DIGEST_PATTERN)
    scenario_handle: str = Field(pattern=_IDENTIFIER_PATTERN)
    repetition: int = Field(ge=1, le=100)
    result: PrivateCaseResult

    @model_validator(mode="after")
    def matches_private_result(self) -> ReceiptResultBinding:
        if (
            self.blind_arm_token != self.result.blind_arm_token
            or self.scenario_handle != self.result.scenario_handle
            or self.repetition != self.result.repetition
        ):
            raise ValueError("receipt binding differs from private result")
        return self


class PrivateEvaluationReceipt(FrozenContract):
    """Full append-only receipt retained only by the protected receipt store."""

    format: Literal["ontowiz-private-evaluation-receipt"]
    format_version: Literal[1]
    run_id: str = Field(pattern=_IDENTIFIER_PATTERN)
    candidate_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    preregistration_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    suite_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    run_plan_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    execution: ExecutionDigests
    expected_result_count: int = Field(ge=1)
    observed_result_count: int = Field(ge=0)
    case_count: int = Field(ge=1)
    arm_count: int = Field(ge=1)
    repetitions: int = Field(ge=1)
    aggregate_score: float = Field(ge=0.0, le=1.0)
    critical_failure_count: int = Field(ge=0)
    gate_passed: bool
    traces: tuple[AgentTrace, ...]
    results: tuple[ReceiptResultBinding, ...]
    created_at: str = Field(pattern=_UTC_PATTERN)

    @model_validator(mode="after")
    def complete_unique_inventory(self) -> PrivateEvaluationReceipt:
        identities = tuple(
            (
                binding.arm_id,
                binding.scenario_handle,
                binding.repetition,
            )
            for binding in self.results
        )
        trace_identities = tuple(
            (
                trace.scenario_handle,
                trace.blind_arm_token,
                trace.repetition,
            )
            for trace in self.traces
        )
        trace_digests = {trace.trace_digest for trace in self.traces}
        result_trace_digests = {binding.result.trace_digest for binding in self.results}
        if (
            self.observed_result_count != len(self.results)
            or self.expected_result_count != self.observed_result_count
            or len(self.traces) != self.expected_result_count
            or len(set(identities)) != len(identities)
            or len(set(trace_identities)) != len(trace_identities)
            or trace_digests != result_trace_digests
        ):
            raise ValueError("private receipt trace/result inventory is incomplete or duplicated")
        return self

    @property
    def receipt_digest(self) -> Digest:
        return digest_value(self.model_dump(mode="json"))


class PublicEvaluationAttestation(FrozenContract):
    """Redacted public commitment; no scenario, trace, result, or arm map appears."""

    format: Literal["ontowiz-public-evaluation-attestation"]
    format_version: Literal[1]
    run_id: str = Field(pattern=_IDENTIFIER_PATTERN)
    candidate_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    preregistration_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    suite_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    run_plan_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    private_receipt_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    case_count: int = Field(ge=1)
    arm_count: int = Field(ge=1)
    repetitions: int = Field(ge=1)
    aggregate_score: float = Field(ge=0.0, le=1.0)
    critical_failure_count: int = Field(ge=0)
    gate_passed: bool
    created_at: str = Field(pattern=_UTC_PATTERN)

    @property
    def attestation_digest(self) -> Digest:
        return digest_value(self.model_dump(mode="json"))


class ReceiptAppendRequest(FrozenContract):
    """Atomic compare-and-append request for the external protected store."""

    format: Literal["ontowiz-evaluation-receipt-append-request"]
    format_version: Literal[1]
    private_receipt: PrivateEvaluationReceipt
    public_attestation: PublicEvaluationAttestation
    expected_private_receipt_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    expected_public_attestation_digest: Digest = Field(pattern=_DIGEST_PATTERN)

    @model_validator(mode="after")
    def expected_digests_match_exact_bytes(self) -> ReceiptAppendRequest:
        if (
            self.expected_private_receipt_digest != self.private_receipt.receipt_digest
            or self.expected_public_attestation_digest
            != self.public_attestation.attestation_digest
            or self.public_attestation.private_receipt_digest
            != self.private_receipt.receipt_digest
        ):
            raise ValueError("append request commitments differ from receipt bytes")
        return self

    @property
    def request_digest(self) -> Digest:
        return digest_value(self.model_dump(mode="json"))


class ReceiptCommitment(FrozenContract):
    """Opaque proof that the external store appended the receipt atomically."""

    format: Literal["ontowiz-evaluation-receipt-commitment"]
    format_version: Literal[1]
    candidate_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    suite_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    run_plan_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    private_receipt_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    public_attestation_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    append_request_digest: Digest = Field(pattern=_DIGEST_PATTERN)
    append_sequence_digest: Digest = Field(pattern=_DIGEST_PATTERN)


class EvaluationOutcome(FrozenContract):
    """Only public, redacted evaluation material returned to the caller."""

    attestation: PublicEvaluationAttestation
    commitment: ReceiptCommitment


def contains_unresolved_marker(value: Any) -> bool:
    """Detect unresolved owner/approval placeholders in a contract."""

    if isinstance(value, str):
        upper = value.upper()
        return any(marker in upper for marker in ("[OWNER]", "TBD", "TODO"))
    if isinstance(value, Mapping):
        return any(contains_unresolved_marker(item) for item in value.values())
    if isinstance(value, list | tuple):
        return any(contains_unresolved_marker(item) for item in value)
    return False
