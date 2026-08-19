"""Fail-closed orchestration across an external protected-evaluation boundary."""

from __future__ import annotations

import hashlib
import re
import stat
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Protocol, TypeVar, cast

from pydantic import BaseModel

from ontowiz_authoring.archive import ArchiveError, verify_archive

from .contracts import (
    AgentTrace,
    EvaluationArm,
    EvaluationOutcome,
    EvaluationRunPlan,
    FrozenSuiteDescriptor,
    IsolatedWorkerResult,
    PreregistrationRecord,
    PrivateCaseResult,
    PrivateEvaluationReceipt,
    PublicEvaluationAttestation,
    PublicScenario,
    ReceiptAppendRequest,
    ReceiptCommitment,
    ReceiptResultBinding,
    VaultIsolationProof,
    WorkerEnvelope,
    WorkerIsolationAttestation,
    contains_unresolved_marker,
)

EvaluationErrorCode = Literal[
    "E_PREREG_UNAPPROVED",
    "E_VAULT_ISOLATION_UNPROVEN",
    "E_LOCK_SIGNATURE_INVALID",
    "E_SUITE_DRIFT",
    "E_RUNPLAN_DRIFT",
    "E_CANDIDATE_DRIFT",
    "E_CANDIDATE_MUTATED",
    "E_ADAPTER_ISOLATION",
    "E_RUN_INCOMPLETE",
    "E_BLINDING_COMPROMISED",
    "E_SCORER_DISAGREEMENT",
    "E_RECEIPT_CONFLICT",
    "E_PROVIDER_UNAVAILABLE",
]

_ModelT = TypeVar("_ModelT", bound=BaseModel)


def _strict_external_model(value: object, model: type[_ModelT]) -> _ModelT:
    """Revalidate one exact external model without trusting subclasses or hints."""

    try:
        if type(value) is not model:
            raise TypeError("external model type differs from contract")
        return model.model_validate_json(value.model_dump_json())
    except Exception as exc:
        raise EvaluationError("E_PROVIDER_UNAVAILABLE") from exc


def _strict_scenario_handles(value: object) -> tuple[str, ...]:
    try:
        if type(value) is not tuple or any(
            type(item) is not str
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", item) is None
            for item in value
        ):
            raise TypeError("scenario inventory differs from contract")
        return cast(tuple[str, ...], value)
    except Exception as exc:
        raise EvaluationError("E_PROVIDER_UNAVAILABLE") from exc


def _strict_run_plan(value: object) -> EvaluationRunPlan:
    try:
        if type(value) is not EvaluationRunPlan:
            raise TypeError("run plan type differs from contract")
        return EvaluationRunPlan.model_validate_json(value.model_dump_json())
    except Exception as exc:
        raise EvaluationError("E_RUNPLAN_DRIFT") from exc


class EvaluationError(RuntimeError):
    """Public, redacted refusal that never embeds provider or protected details."""

    def __init__(self, code: EvaluationErrorCode) -> None:
        self.code = code
        super().__init__(f"{code}: evaluation refused")


EvaluationRefusal = EvaluationError


class EvaluationCustodian(Protocol):
    """External protected-suite custodian; implementations live outside this kit."""

    def preregistration(self) -> PreregistrationRecord: ...

    def verify_preregistration(self, record: PreregistrationRecord) -> bool: ...

    def isolation_proof(
        self,
        *,
        drafting_principal: str,
        worker_principal: str,
    ) -> VaultIsolationProof: ...

    def verify_isolation_proof(self, proof: VaultIsolationProof) -> bool: ...

    def freeze_suite(
        self,
        *,
        preregistration_digest: str,
        isolation_proof_digest: str,
    ) -> FrozenSuiteDescriptor: ...

    def current_suite(self) -> FrozenSuiteDescriptor: ...

    def verify_suite_lock(self, descriptor: FrozenSuiteDescriptor) -> bool: ...

    def verify_run_plan(self, plan: EvaluationRunPlan) -> bool: ...

    def verify_worker_isolation(
        self,
        attestation: WorkerIsolationAttestation,
    ) -> bool: ...

    def scenario_handles(self, *, suite_digest: str) -> tuple[str, ...]: ...

    def public_scenario(
        self,
        *,
        suite_digest: str,
        scenario_handle: str,
    ) -> PublicScenario: ...

    def blind_arm_token(
        self,
        *,
        run_plan_digest: str,
        scenario_handle: str,
        repetition: int,
        arm: EvaluationArm,
    ) -> str: ...

    def verify_blind_arm_token(
        self,
        *,
        run_plan_digest: str,
        scenario_handle: str,
        repetition: int,
        arm: EvaluationArm,
        blind_arm_token: str,
    ) -> bool: ...

    def score_private(
        self,
        *,
        suite_digest: str,
        scenario_handle: str,
        trace: AgentTrace,
    ) -> PrivateCaseResult: ...


class AdapterWorker(Protocol):
    """External broker that starts one fresh runtime for each blind envelope."""

    def run_isolated(self, envelope: WorkerEnvelope) -> IsolatedWorkerResult: ...


class AppendOnlyReceiptStore(Protocol):
    """External store that atomically compares and appends one exact request."""

    def append_atomic(self, request: ReceiptAppendRequest) -> ReceiptCommitment: ...


def _now_utc() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
    except OSError as exc:
        raise EvaluationRefusal("E_CANDIDATE_MUTATED") from exc
    return "sha256:" + digest.hexdigest()


def _candidate_identity(path: Path) -> tuple[int, int, int, int, int, str]:
    try:
        info = path.lstat()
    except OSError as exc:
        raise EvaluationRefusal("E_CANDIDATE_DRIFT") from exc
    if (
        not stat.S_ISREG(info.st_mode)
        or stat.S_ISLNK(info.st_mode)
        or info.st_nlink != 1
        or (
            getattr(info, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        )
    ):
        raise EvaluationRefusal("E_CANDIDATE_DRIFT")
    return (
        info.st_dev,
        info.st_ino,
        info.st_size,
        info.st_mtime_ns,
        info.st_nlink,
        _sha256_file(path),
    )


def _approved_preregistration(
    custodian: EvaluationCustodian,
) -> PreregistrationRecord:
    try:
        record = _strict_external_model(
            custodian.preregistration(),
            PreregistrationRecord,
        )
        verified = custodian.verify_preregistration(record)
        data = record.model_dump(mode="json")
    except EvaluationRefusal:
        raise
    except Exception as exc:
        raise EvaluationRefusal("E_PROVIDER_UNAVAILABLE") from exc
    if (
        record.status != "approved"
        or record.approved_by is None
        or record.approved_at is None
        or record.approval_signature_digest is None
        or record.approved_by == record.candidate_author
        or record.adjudicator_id is None
        or record.maximum_critical_failures != 0
        or contains_unresolved_marker(data)
        or verified is not True
    ):
        raise EvaluationRefusal("E_PREREG_UNAPPROVED")
    return record


def _isolation_proof(
    custodian: EvaluationCustodian,
    *,
    drafting_principal: str,
    worker_principal: str,
    evaluator_principal: str,
) -> VaultIsolationProof:
    try:
        proof = _strict_external_model(
            custodian.isolation_proof(
                drafting_principal=drafting_principal,
                worker_principal=worker_principal,
            ),
            VaultIsolationProof,
        )
        verified = custodian.verify_isolation_proof(proof)
    except EvaluationRefusal:
        raise
    except Exception as exc:
        raise EvaluationRefusal("E_PROVIDER_UNAVAILABLE") from exc
    if (
        proof.drafting_principal != drafting_principal
        or proof.worker_principal != worker_principal
        or proof.evaluator_principal != evaluator_principal
        or len({drafting_principal, worker_principal, evaluator_principal}) != 3
        or not proof.drafting_list_denied
        or not proof.drafting_read_denied
        or not proof.worker_list_denied
        or not proof.worker_read_denied
        or verified is not True
    ):
        raise EvaluationRefusal("E_VAULT_ISOLATION_UNPROVEN")
    return proof


def _verified_suite(
    custodian: EvaluationCustodian,
    descriptor: FrozenSuiteDescriptor,
) -> None:
    try:
        verified = custodian.verify_suite_lock(descriptor)
    except Exception as exc:
        raise EvaluationRefusal("E_PROVIDER_UNAVAILABLE") from exc
    if verified is not True:
        raise EvaluationRefusal("E_LOCK_SIGNATURE_INVALID")


def freeze_heldout_suite(
    custodian: EvaluationCustodian,
    *,
    drafting_principal: str,
    worker_principal: str,
    evaluator_principal: str,
) -> FrozenSuiteDescriptor:
    """Ask an external custodian to freeze an approved, isolated suite."""

    preregistration = _approved_preregistration(custodian)
    proof = _isolation_proof(
        custodian,
        drafting_principal=drafting_principal,
        worker_principal=worker_principal,
        evaluator_principal=evaluator_principal,
    )
    try:
        frozen = _strict_external_model(
            custodian.freeze_suite(
                preregistration_digest=preregistration.preregistration_digest,
                isolation_proof_digest=proof.proof_digest,
            ),
            FrozenSuiteDescriptor,
        )
        current = _strict_external_model(
            custodian.current_suite(),
            FrozenSuiteDescriptor,
        )
    except Exception as exc:
        raise EvaluationRefusal("E_PROVIDER_UNAVAILABLE") from exc
    if (
        frozen != current
        or frozen.preregistration_digest != preregistration.preregistration_digest
        or frozen.isolation_proof_digest != proof.proof_digest
        or frozen.case_count != preregistration.expected_case_count
    ):
        raise EvaluationRefusal("E_SUITE_DRIFT")
    _verified_suite(custodian, frozen)
    return frozen


def _verify_plan(
    plan: EvaluationRunPlan,
    preregistration: PreregistrationRecord,
    suite: FrozenSuiteDescriptor,
    proof: VaultIsolationProof,
) -> None:
    if (
        plan.preregistration_digest != preregistration.preregistration_digest
        or plan.suite_digest != suite.suite_digest
        or plan.arms != preregistration.arms
        or plan.repetitions != preregistration.repetitions
        or plan.drafting_principal != proof.drafting_principal
        or plan.worker_principal != proof.worker_principal
        or plan.evaluator_principal != proof.evaluator_principal
        or suite.preregistration_digest != preregistration.preregistration_digest
        or suite.isolation_proof_digest != proof.proof_digest
        or suite.case_count != preregistration.expected_case_count
    ):
        raise EvaluationRefusal("E_RUNPLAN_DRIFT")


def _verify_plan_signature(
    custodian: EvaluationCustodian,
    plan: EvaluationRunPlan,
) -> None:
    try:
        verified = custodian.verify_run_plan(plan)
    except Exception as exc:
        raise EvaluationRefusal("E_PROVIDER_UNAVAILABLE") from exc
    if verified is not True:
        raise EvaluationRefusal("E_RUNPLAN_DRIFT")


def _verify_trace(
    trace: AgentTrace,
    *,
    envelope: WorkerEnvelope,
) -> None:
    if (
        not trace.complete
        or trace.run_id != envelope.run_id
        or trace.candidate_digest != envelope.candidate_digest
        or trace.suite_digest != envelope.suite_digest
        or trace.scenario_handle != envelope.scenario.scenario_handle
        or trace.blind_arm_token != envelope.blind_arm_token
        or trace.repetition != envelope.repetition
        or trace.worker_principal != envelope.worker_principal
        or trace.execution != envelope.execution
    ):
        raise EvaluationRefusal("E_RUN_INCOMPLETE")


def _verify_worker_isolation(
    custodian: EvaluationCustodian,
    attestation: WorkerIsolationAttestation,
    *,
    envelope: WorkerEnvelope,
    used_runtime_ids: set[str],
) -> None:
    try:
        verified = custodian.verify_worker_isolation(attestation)
    except Exception as exc:
        raise EvaluationRefusal("E_PROVIDER_UNAVAILABLE") from exc
    if (
        attestation.run_id != envelope.run_id
        or attestation.envelope_digest != envelope.envelope_digest
        or attestation.worker_principal != envelope.worker_principal
        or attestation.adapter_build_digest != envelope.execution.adapter_build_digest
        or attestation.runtime_instance_id in used_runtime_ids
        or not attestation.vault_list_denied
        or not attestation.vault_read_denied
        or not attestation.fresh_runtime
        or attestation.state_reused
        or verified is not True
    ):
        raise EvaluationRefusal("E_ADAPTER_ISOLATION")
    used_runtime_ids.add(attestation.runtime_instance_id)


def _verify_result(
    result: PrivateCaseResult,
    *,
    trace: AgentTrace,
    preregistration: PreregistrationRecord,
) -> None:
    if (
        result.scenario_handle != trace.scenario_handle
        or result.blind_arm_token != trace.blind_arm_token
        or result.repetition != trace.repetition
        or result.trace_digest != trace.trace_digest
    ):
        raise EvaluationRefusal("E_RUN_INCOMPLETE")
    if result.scorer_ids != preregistration.scorer_ids:
        raise EvaluationRefusal("E_SCORER_DISAGREEMENT")
    if not result.scorer_agreement and (
        result.adjudicated_by != preregistration.adjudicator_id
        or result.adjudication_digest is None
    ):
        raise EvaluationRefusal("E_SCORER_DISAGREEMENT")


class EvaluationCoordinator:
    """Run one paired, repeated evaluation without exposing protected material."""

    def __init__(self, *, clock: Callable[[], str] = _now_utc) -> None:
        self._clock = clock

    def evaluate(
        self,
        candidate_pack: str | Path,
        plan: EvaluationRunPlan,
        *,
        custodian: EvaluationCustodian,
        worker: AdapterWorker,
        receipt_store: AppendOnlyReceiptStore,
    ) -> EvaluationOutcome:
        plan = _strict_run_plan(plan)
        candidate_path = Path(candidate_pack).absolute()
        initial_identity = _candidate_identity(candidate_path)
        try:
            verified_candidate = verify_archive(
                candidate_path,
                expected_format="ontowiz-candidate-pack",
            )
        except ArchiveError as exc:
            raise EvaluationRefusal("E_CANDIDATE_DRIFT") from exc
        if (
            verified_candidate.archive_sha256 != plan.candidate_digest
            or initial_identity[-1] != plan.candidate_digest
        ):
            raise EvaluationRefusal("E_CANDIDATE_DRIFT")

        preregistration = _approved_preregistration(custodian)
        proof = _isolation_proof(
            custodian,
            drafting_principal=plan.drafting_principal,
            worker_principal=plan.worker_principal,
            evaluator_principal=plan.evaluator_principal,
        )
        try:
            suite = _strict_external_model(
                custodian.current_suite(),
                FrozenSuiteDescriptor,
            )
        except Exception as exc:
            raise EvaluationRefusal("E_PROVIDER_UNAVAILABLE") from exc
        _verified_suite(custodian, suite)
        _verify_plan(plan, preregistration, suite, proof)
        _verify_plan_signature(custodian, plan)

        try:
            handles = _strict_scenario_handles(
                custodian.scenario_handles(suite_digest=suite.suite_digest)
            )
        except Exception as exc:
            raise EvaluationRefusal("E_PROVIDER_UNAVAILABLE") from exc
        if (
            len(handles) != suite.case_count
            or len(set(handles)) != len(handles)
            or handles != tuple(sorted(handles))
        ):
            raise EvaluationRefusal("E_RUN_INCOMPLETE")

        bindings: list[ReceiptResultBinding] = []
        traces: list[AgentTrace] = []
        used_blind_tokens: set[str] = set()
        schedule: list[tuple[str, EvaluationArm, PublicScenario, int]] = []
        for scenario_handle in handles:
            try:
                scenario = _strict_external_model(
                    custodian.public_scenario(
                        suite_digest=suite.suite_digest,
                        scenario_handle=scenario_handle,
                    ),
                    PublicScenario,
                )
            except Exception as exc:
                raise EvaluationRefusal("E_PROVIDER_UNAVAILABLE") from exc
            if scenario.scenario_handle != scenario_handle:
                raise EvaluationRefusal("E_RUN_INCOMPLETE")
            for repetition in range(1, plan.repetitions + 1):
                for arm in plan.arms:
                    try:
                        blind_token = custodian.blind_arm_token(
                            run_plan_digest=plan.run_plan_digest,
                            scenario_handle=scenario_handle,
                            repetition=repetition,
                            arm=arm,
                        )
                        if type(blind_token) is not str:
                            raise TypeError("blind token differs from contract")
                        blind_verified = custodian.verify_blind_arm_token(
                            run_plan_digest=plan.run_plan_digest,
                            scenario_handle=scenario_handle,
                            repetition=repetition,
                            arm=arm,
                            blind_arm_token=blind_token,
                        )
                    except Exception as exc:
                        raise EvaluationRefusal("E_PROVIDER_UNAVAILABLE") from exc
                    if (
                        not re.fullmatch(r"sha256:[0-9a-f]{64}", blind_token)
                        or blind_token in used_blind_tokens
                        or blind_verified is not True
                    ):
                        raise EvaluationRefusal("E_BLINDING_COMPROMISED")
                    used_blind_tokens.add(blind_token)
                    schedule.append((blind_token, arm, scenario, repetition))

        used_runtime_ids: set[str] = set()
        for blind_token, arm, scenario, repetition in sorted(
            schedule,
            key=lambda item: item[0],
        ):
            envelope = WorkerEnvelope(
                format="ontowiz-evaluation-worker-envelope",
                format_version=1,
                run_id=plan.run_id,
                candidate_digest=plan.candidate_digest,
                suite_digest=suite.suite_digest,
                scenario=scenario,
                blind_arm_token=blind_token,
                repetition=repetition,
                worker_principal=plan.worker_principal,
                execution=plan.execution,
            )
            try:
                isolated_result = _strict_external_model(
                    worker.run_isolated(envelope),
                    IsolatedWorkerResult,
                )
            except Exception as exc:
                raise EvaluationRefusal("E_RUN_INCOMPLETE") from exc
            if _candidate_identity(candidate_path) != initial_identity:
                raise EvaluationRefusal("E_CANDIDATE_MUTATED")
            _verify_worker_isolation(
                custodian,
                isolated_result.isolation,
                envelope=envelope,
                used_runtime_ids=used_runtime_ids,
            )
            trace = isolated_result.trace
            _verify_trace(trace, envelope=envelope)
            traces.append(trace)
            try:
                result = _strict_external_model(
                    custodian.score_private(
                        suite_digest=suite.suite_digest,
                        scenario_handle=scenario.scenario_handle,
                        trace=trace,
                    ),
                    PrivateCaseResult,
                )
            except Exception as exc:
                raise EvaluationRefusal("E_PROVIDER_UNAVAILABLE") from exc
            _verify_result(result, trace=trace, preregistration=preregistration)
            bindings.append(
                ReceiptResultBinding(
                    arm_id=arm.arm_id,
                    blind_arm_token=blind_token,
                    scenario_handle=scenario.scenario_handle,
                    repetition=repetition,
                    result=result,
                )
            )

        expected = suite.case_count * plan.repetitions * len(plan.arms)
        if len(bindings) != expected:
            raise EvaluationRefusal("E_RUN_INCOMPLETE")
        try:
            final_suite = _strict_external_model(
                custodian.current_suite(),
                FrozenSuiteDescriptor,
            )
        except Exception as exc:
            raise EvaluationRefusal("E_PROVIDER_UNAVAILABLE") from exc
        final_preregistration = _approved_preregistration(custodian)
        final_proof = _isolation_proof(
            custodian,
            drafting_principal=plan.drafting_principal,
            worker_principal=plan.worker_principal,
            evaluator_principal=plan.evaluator_principal,
        )
        if final_preregistration != preregistration:
            raise EvaluationRefusal("E_RUNPLAN_DRIFT")
        if final_proof != proof:
            raise EvaluationRefusal("E_VAULT_ISOLATION_UNPROVEN")
        if final_suite != suite:
            raise EvaluationRefusal("E_SUITE_DRIFT")
        _verified_suite(custodian, final_suite)
        _verify_plan_signature(custodian, plan)
        if _candidate_identity(candidate_path) != initial_identity:
            raise EvaluationRefusal("E_CANDIDATE_MUTATED")
        try:
            final_candidate = verify_archive(
                candidate_path,
                expected_format="ontowiz-candidate-pack",
            )
        except ArchiveError as exc:
            raise EvaluationRefusal("E_CANDIDATE_MUTATED") from exc
        if final_candidate.archive_sha256 != plan.candidate_digest:
            raise EvaluationRefusal("E_CANDIDATE_MUTATED")

        scores = [
            (binding.result.deterministic_score + binding.result.rubric_score) / 2.0
            for binding in bindings
        ]
        aggregate = sum(scores) / len(scores)
        critical_count = sum(
            len(binding.result.critical_failure_ids) for binding in bindings
        )
        gate_passed = (
            all(binding.result.passed for binding in bindings)
            and aggregate >= preregistration.minimum_score
            and critical_count == 0
        )
        created_at = self._clock()
        receipt = PrivateEvaluationReceipt(
            format="ontowiz-private-evaluation-receipt",
            format_version=1,
            run_id=plan.run_id,
            candidate_digest=plan.candidate_digest,
            preregistration_digest=preregistration.preregistration_digest,
            suite_digest=suite.suite_digest,
            run_plan_digest=plan.run_plan_digest,
            execution=plan.execution,
            expected_result_count=expected,
            observed_result_count=len(bindings),
            case_count=suite.case_count,
            arm_count=len(plan.arms),
            repetitions=plan.repetitions,
            aggregate_score=aggregate,
            critical_failure_count=critical_count,
            gate_passed=gate_passed,
            traces=tuple(traces),
            results=tuple(bindings),
            created_at=created_at,
        )
        attestation = PublicEvaluationAttestation(
            format="ontowiz-public-evaluation-attestation",
            format_version=1,
            run_id=plan.run_id,
            candidate_digest=plan.candidate_digest,
            preregistration_digest=preregistration.preregistration_digest,
            suite_digest=suite.suite_digest,
            run_plan_digest=plan.run_plan_digest,
            private_receipt_digest=receipt.receipt_digest,
            case_count=suite.case_count,
            arm_count=len(plan.arms),
            repetitions=plan.repetitions,
            aggregate_score=aggregate,
            critical_failure_count=critical_count,
            gate_passed=gate_passed,
            created_at=created_at,
        )
        append_request = ReceiptAppendRequest(
            format="ontowiz-evaluation-receipt-append-request",
            format_version=1,
            private_receipt=receipt,
            public_attestation=attestation,
            expected_private_receipt_digest=receipt.receipt_digest,
            expected_public_attestation_digest=attestation.attestation_digest,
        )
        try:
            commitment = _strict_external_model(
                receipt_store.append_atomic(append_request),
                ReceiptCommitment,
            )
        except Exception as exc:
            raise EvaluationRefusal("E_RECEIPT_CONFLICT") from exc
        if (
            commitment.candidate_digest != plan.candidate_digest
            or commitment.suite_digest != suite.suite_digest
            or commitment.run_plan_digest != plan.run_plan_digest
            or commitment.private_receipt_digest != receipt.receipt_digest
            or commitment.public_attestation_digest != attestation.attestation_digest
            or commitment.append_request_digest != append_request.request_digest
        ):
            raise EvaluationRefusal("E_RECEIPT_CONFLICT")
        if _candidate_identity(candidate_path) != initial_identity:
            raise EvaluationRefusal("E_CANDIDATE_MUTATED")
        return EvaluationOutcome(attestation=attestation, commitment=commitment)
