from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

import ontowiz_evaluator.evaluator as evaluator_module
from ontowiz_evaluator import (
    AgentTrace,
    EvaluationArm,
    EvaluationCoordinator,
    EvaluationRefusal,
    EvaluationRunPlan,
    ExecutionDigests,
    FrozenSuiteDescriptor,
    IsolatedWorkerResult,
    PreregistrationRecord,
    PrivateCaseResult,
    PrivateEvaluationReceipt,
    PublicScenario,
    ReceiptCommitment,
    VaultIsolationProof,
    WorkerIsolationAttestation,
    digest_value,
    freeze_heldout_suite,
)


def _digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode()).hexdigest()


class _Custodian:
    def __init__(self, candidate_digest: str) -> None:
        self.prereg = PreregistrationRecord(
            format="ontowiz-evaluation-preregistration",
            format_version=1,
            status="approved",
            preregistration_digest=_digest("preregistration"),
            candidate_author="candidate-author",
            approved_by="platform-approver",
            approved_at="2026-07-25T12:00:00Z",
            approval_signature_digest=_digest("preregistration-signature"),
            arms=(
                EvaluationArm(arm_id="A", configuration_digest=_digest("arm-a")),
                EvaluationArm(arm_id="B", configuration_digest=_digest("arm-b")),
            ),
            repetitions=2,
            expected_case_count=1,
            scorer_ids=("scorer-one", "scorer-two"),
            adjudicator_id="adjudicator",
            minimum_score=0.8,
            maximum_critical_failures=0,
        )
        self.proof = VaultIsolationProof(
            format="ontowiz-vault-isolation-proof",
            format_version=1,
            proof_digest=_digest("isolation-proof"),
            proof_signature_digest=_digest("isolation-signature"),
            drafting_principal="drafting-principal",
            worker_principal="worker-principal",
            evaluator_principal="evaluator-principal",
            drafting_list_denied=True,
            drafting_read_denied=True,
            worker_list_denied=True,
            worker_read_denied=True,
            checked_at="2026-07-25T12:01:00Z",
        )
        self.suite = FrozenSuiteDescriptor(
            format="ontowiz-frozen-evaluation-suite",
            format_version=1,
            suite_id="suite-one",
            suite_digest=_digest("suite"),
            preregistration_digest=self.prereg.preregistration_digest,
            isolation_proof_digest=self.proof.proof_digest,
            inventory_digest=_digest("private-inventory"),
            lock_signature_digest=_digest("suite-signature"),
            case_count=1,
            frozen_at="2026-07-25T12:02:00Z",
        )
        self.candidate_digest = candidate_digest
        self.preregistration_verified = True
        self.isolation_verified = True
        self.suite_verified = True
        self.plan_verified = True
        self.worker_isolation_verified = True
        self.blind_verified = True
        self.handles = ("opaque-scenario-1",)
        self.duplicate_blind_token = False
        self.incomplete_trace = False
        self.critical_failure = False
        self.scorer_agreement = True
        self.mismatched_score_trace = False
        self.adjudicated_by: str | None = None
        self.adjudication_digest: str | None = None
        self.drift_after_scores = False
        self.score_count = 0

    def preregistration(self) -> PreregistrationRecord:
        return self.prereg

    def verify_preregistration(self, record: PreregistrationRecord) -> bool:
        return self.preregistration_verified and record == self.prereg

    def isolation_proof(
        self,
        *,
        drafting_principal: str,
        worker_principal: str,
    ) -> VaultIsolationProof:
        assert drafting_principal
        assert worker_principal
        return self.proof

    def verify_isolation_proof(self, proof: VaultIsolationProof) -> bool:
        return self.isolation_verified and proof == self.proof

    def freeze_suite(
        self,
        *,
        preregistration_digest: str,
        isolation_proof_digest: str,
    ) -> FrozenSuiteDescriptor:
        assert preregistration_digest == self.prereg.preregistration_digest
        assert isolation_proof_digest == self.proof.proof_digest
        return self.suite

    def current_suite(self) -> FrozenSuiteDescriptor:
        if self.drift_after_scores and self.score_count:
            return self.suite.model_copy(update={"suite_digest": _digest("drifted-suite")})
        return self.suite

    def verify_suite_lock(self, descriptor: FrozenSuiteDescriptor) -> bool:
        return self.suite_verified and descriptor.lock_signature_digest == (
            self.suite.lock_signature_digest
        )

    def verify_run_plan(self, plan: EvaluationRunPlan) -> bool:
        return self.plan_verified and plan.candidate_digest == self.candidate_digest

    def verify_worker_isolation(
        self,
        attestation: WorkerIsolationAttestation,
    ) -> bool:
        return self.worker_isolation_verified and attestation.process_isolation_proof_digest == (
            _digest("process-isolation")
        )

    def scenario_handles(self, *, suite_digest: str) -> tuple[str, ...]:
        assert suite_digest == self.suite.suite_digest
        return self.handles

    def public_scenario(
        self,
        *,
        suite_digest: str,
        scenario_handle: str,
    ) -> PublicScenario:
        assert suite_digest == self.suite.suite_digest
        return PublicScenario(
            format="ontowiz-public-evaluation-scenario",
            format_version=1,
            scenario_handle=scenario_handle,
            instructions="Answer from the candidate context or abstain.",
            inputs={"signal": "public synthetic input"},
            deliberately_missing=(),
        )

    def blind_arm_token(
        self,
        *,
        run_plan_digest: str,
        scenario_handle: str,
        repetition: int,
        arm: EvaluationArm,
    ) -> str:
        if self.duplicate_blind_token:
            return _digest("duplicate")
        return digest_value(
            {
                "plan": run_plan_digest,
                "handle": scenario_handle,
                "repetition": repetition,
                "arm": arm.arm_id,
            }
        )

    def verify_blind_arm_token(
        self,
        *,
        run_plan_digest: str,
        scenario_handle: str,
        repetition: int,
        arm: EvaluationArm,
        blind_arm_token: str,
    ) -> bool:
        return self.blind_verified and blind_arm_token == self.blind_arm_token(
            run_plan_digest=run_plan_digest,
            scenario_handle=scenario_handle,
            repetition=repetition,
            arm=arm,
        )

    def score_private(
        self,
        *,
        suite_digest: str,
        scenario_handle: str,
        trace: AgentTrace,
    ) -> PrivateCaseResult:
        assert suite_digest == self.suite.suite_digest
        self.score_count += 1
        return PrivateCaseResult(
            format="ontowiz-private-case-result",
            format_version=1,
            scenario_handle=scenario_handle,
            blind_arm_token=trace.blind_arm_token,
            repetition=trace.repetition,
            trace_digest=(
                _digest("mismatched-trace")
                if self.mismatched_score_trace
                else trace.trace_digest
            ),
            deterministic_score=1.0,
            rubric_score=1.0,
            passed=not self.critical_failure,
            critical_failure_ids=("CF-1",) if self.critical_failure else (),
            scorer_ids=self.prereg.scorer_ids,
            scorer_agreement=self.scorer_agreement,
            adjudicated_by=self.adjudicated_by,
            adjudication_digest=self.adjudication_digest,
        )


class _Worker:
    def __init__(self, custodian: _Custodian, candidate: Path) -> None:
        self.custodian = custodian
        self.candidate = candidate
        self.mutate_candidate = False
        self.reuse_runtime = False
        self.seen = []

    def run_isolated(self, envelope):  # type: ignore[no-untyped-def]
        self.seen.append(envelope)
        if self.mutate_candidate:
            self.candidate.write_bytes(b"mutated candidate")
        trace = AgentTrace(
            format="ontowiz-evaluation-agent-trace",
            format_version=1,
            run_id=envelope.run_id,
            candidate_digest=envelope.candidate_digest,
            suite_digest=envelope.suite_digest,
            scenario_handle=envelope.scenario.scenario_handle,
            blind_arm_token=envelope.blind_arm_token,
            repetition=envelope.repetition,
            worker_principal=envelope.worker_principal,
            execution=envelope.execution,
            output="A synthetic candidate answer.",
            citation_ids=("CTX-1",),
            retrieved_context_ids=("CTX-1",),
            tool_calls=(),
            complete=not self.custodian.incomplete_trace,
        )
        runtime_id = "runtime-reused" if self.reuse_runtime else f"runtime-{len(self.seen)}"
        isolation = WorkerIsolationAttestation(
            format="ontowiz-worker-isolation-attestation",
            format_version=1,
            run_id=envelope.run_id,
            envelope_digest=envelope.envelope_digest,
            worker_principal=envelope.worker_principal,
            runtime_instance_id=runtime_id,
            adapter_build_digest=envelope.execution.adapter_build_digest,
            process_isolation_proof_digest=_digest("process-isolation"),
            vault_list_denied=True,
            vault_read_denied=True,
            fresh_runtime=True,
            state_reused=False,
            checked_at="2026-07-25T12:30:00Z",
        )
        return IsolatedWorkerResult(trace=trace, isolation=isolation)


class _Store:
    def __init__(self) -> None:
        self.receipt = None
        self.attestation = None
        self.conflict = False
        self.wrong_commitment = False

    def append_atomic(self, request):  # type: ignore[no-untyped-def]
        if self.conflict:
            raise RuntimeError("protected store detail must stay redacted")
        receipt_digest = request.private_receipt.receipt_digest
        if self.wrong_commitment:
            receipt_digest = _digest("wrong-receipt")
        else:
            self.receipt = request.private_receipt
            self.attestation = request.public_attestation
        return ReceiptCommitment(
            format="ontowiz-evaluation-receipt-commitment",
            format_version=1,
            candidate_digest=request.private_receipt.candidate_digest,
            suite_digest=request.private_receipt.suite_digest,
            run_plan_digest=request.private_receipt.run_plan_digest,
            private_receipt_digest=receipt_digest,
            public_attestation_digest=request.public_attestation.attestation_digest,
            append_request_digest=request.request_digest,
            append_sequence_digest=_digest("append-sequence"),
        )


@pytest.fixture
def evaluation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    candidate = tmp_path / "candidate.owpack"
    candidate.write_bytes(b"synthetic candidate archive boundary")
    candidate_digest = _digest("synthetic candidate archive boundary")

    def verified(path: Path, *, expected_format: str):
        assert expected_format == "ontowiz-candidate-pack"
        return SimpleNamespace(archive_sha256=_digest(Path(path).read_text()))

    monkeypatch.setattr(evaluator_module, "verify_archive", verified)
    custodian = _Custodian(candidate_digest)
    execution = ExecutionDigests(
        agent_digest=_digest("agent"),
        adapter_build_digest=_digest("adapter"),
        model_digest=_digest("model"),
        prompt_digest=_digest("prompt"),
        retrieval_digest=_digest("retrieval"),
        tool_digest=_digest("tools"),
        data_digest=_digest("data"),
        evaluator_build_digest=_digest("evaluator"),
    )
    plan = EvaluationRunPlan(
        format="ontowiz-evaluation-run-plan",
        format_version=1,
        run_id="run-one",
        candidate_digest=candidate_digest,
        preregistration_digest=custodian.prereg.preregistration_digest,
        suite_digest=custodian.suite.suite_digest,
        arms=custodian.prereg.arms,
        repetitions=custodian.prereg.repetitions,
        drafting_principal=custodian.proof.drafting_principal,
        worker_principal=custodian.proof.worker_principal,
        evaluator_principal=custodian.proof.evaluator_principal,
        blinding_commitment_digest=_digest("blinding"),
        execution=execution,
        approved_plan_signature_digest=_digest("plan-signature"),
        created_at="2026-07-25T12:03:00Z",
    )
    return candidate, custodian, plan, _Worker(custodian, candidate), _Store()


def _evaluate(evaluation):
    candidate, custodian, plan, worker, store = evaluation
    outcome = EvaluationCoordinator(clock=lambda: "2026-07-25T13:00:00Z").evaluate(
        candidate,
        plan,
        custodian=custodian,
        worker=worker,
        receipt_store=store,
    )
    return outcome, store


def _refusal(evaluation, code: str) -> None:
    with pytest.raises(EvaluationRefusal) as caught:
        _evaluate(evaluation)
    assert caught.value.code == code
    assert str(caught.value) == f"{code}: evaluation refused"


def test_complete_paired_run_returns_only_redacted_attestation(evaluation) -> None:
    outcome, store = _evaluate(evaluation)
    assert outcome.attestation.gate_passed is True
    assert outcome.attestation.arm_count == 2
    assert outcome.attestation.repetitions == 2
    assert store.receipt.expected_result_count == 4
    assert store.receipt.observed_result_count == 4
    assert len(store.receipt.traces) == 4
    assert store.receipt.traces[0].output == "A synthetic candidate answer."
    assert [item.blind_arm_token for item in evaluation[3].seen] == sorted(
        item.blind_arm_token for item in evaluation[3].seen
    )
    assert len({item.blind_arm_token for item in evaluation[3].seen}) == 4
    public = outcome.model_dump_json()
    assert "opaque-scenario" not in public
    assert "synthetic candidate answer" not in public
    assert '"arm_id"' not in public


def test_reused_worker_runtime_refuses(evaluation) -> None:
    evaluation[3].reuse_runtime = True
    _refusal(evaluation, "E_ADAPTER_ISOLATION")
    assert evaluation[4].receipt is None


def test_unverified_worker_isolation_refuses(evaluation) -> None:
    evaluation[1].worker_isolation_verified = False
    _refusal(evaluation, "E_ADAPTER_ISOLATION")
    assert evaluation[4].receipt is None


@pytest.mark.parametrize("mutation", ["missing_trace", "duplicate_result"])
def test_private_receipt_rejects_incomplete_or_duplicate_inventory(
    evaluation,
    mutation: str,
) -> None:
    _, store = _evaluate(evaluation)
    data = json.loads(store.receipt.model_dump_json())
    if mutation == "missing_trace":
        data["traces"] = data["traces"][:-1]
    else:
        data["results"][-1] = data["results"][0]
    with pytest.raises(ValidationError):
        PrivateEvaluationReceipt.model_validate_json(json.dumps(data))


def test_critical_failure_gets_immutable_failed_receipt(evaluation) -> None:
    evaluation[1].critical_failure = True
    outcome, store = _evaluate(evaluation)
    assert outcome.attestation.gate_passed is False
    assert outcome.attestation.critical_failure_count == 4
    assert store.receipt.gate_passed is False


def test_positive_critical_failure_allowance_is_not_approvable(evaluation) -> None:
    custodian = evaluation[1]
    custodian.prereg = custodian.prereg.model_copy(
        update={"maximum_critical_failures": 1}
    )
    _refusal(evaluation, "E_PREREG_UNAPPROVED")


def test_unapproved_preregistration_refuses(evaluation) -> None:
    custodian = evaluation[1]
    custodian.prereg = custodian.prereg.model_copy(update={"status": "draft"})
    _refusal(evaluation, "E_PREREG_UNAPPROVED")


@pytest.mark.parametrize(
    ("flag", "code"),
    [
        ("preregistration_verified", "E_PREREG_UNAPPROVED"),
        ("isolation_verified", "E_VAULT_ISOLATION_UNPROVEN"),
        ("suite_verified", "E_LOCK_SIGNATURE_INVALID"),
        ("plan_verified", "E_RUNPLAN_DRIFT"),
    ],
)
def test_unverified_external_signatures_refuse(
    evaluation,
    flag: str,
    code: str,
) -> None:
    setattr(evaluation[1], flag, False)
    _refusal(evaluation, code)


@pytest.mark.parametrize(
    "change",
    [
        {"drafting_read_denied": False},
        {"worker_list_denied": False},
        {"evaluator_principal": "drafting-principal"},
    ],
)
def test_unproven_acl_isolation_refuses(evaluation, change: dict[str, object]) -> None:
    custodian = evaluation[1]
    custodian.proof = custodian.proof.model_copy(update=change)
    _refusal(evaluation, "E_VAULT_ISOLATION_UNPROVEN")


def test_suite_drift_after_scoring_refuses_without_receipt(evaluation) -> None:
    custodian, store = evaluation[1], evaluation[4]
    custodian.drift_after_scores = True
    _refusal(evaluation, "E_SUITE_DRIFT")
    assert store.receipt is None


def test_run_plan_drift_refuses(evaluation) -> None:
    evaluation = list(evaluation)
    evaluation[2] = evaluation[2].model_copy(update={"repetitions": 1})
    _refusal(evaluation, "E_RUNPLAN_DRIFT")


def test_wrong_candidate_digest_refuses(evaluation) -> None:
    evaluation = list(evaluation)
    evaluation[2] = evaluation[2].model_copy(update={"candidate_digest": _digest("wrong")})
    _refusal(evaluation, "E_CANDIDATE_DRIFT")


def test_incomplete_trace_refuses_without_receipt(evaluation) -> None:
    evaluation[1].incomplete_trace = True
    _refusal(evaluation, "E_RUN_INCOMPLETE")
    assert evaluation[4].receipt is None


def test_incomplete_repetition_inventory_refuses(evaluation) -> None:
    evaluation[1].handles = ()
    _refusal(evaluation, "E_RUN_INCOMPLETE")


def test_duplicate_scenario_inventory_refuses(evaluation) -> None:
    custodian = evaluation[1]
    custodian.prereg = custodian.prereg.model_copy(update={"expected_case_count": 2})
    custodian.suite = custodian.suite.model_copy(update={"case_count": 2})
    custodian.handles = ("opaque-scenario-1", "opaque-scenario-1")
    _refusal(evaluation, "E_RUN_INCOMPLETE")


def test_mismatched_private_score_inventory_refuses(evaluation) -> None:
    evaluation[1].mismatched_score_trace = True
    _refusal(evaluation, "E_RUN_INCOMPLETE")


def test_unresolved_scorer_disagreement_refuses(evaluation) -> None:
    evaluation[1].scorer_agreement = False
    _refusal(evaluation, "E_SCORER_DISAGREEMENT")


def test_wrong_adjudicator_refuses(evaluation) -> None:
    custodian = evaluation[1]
    custodian.scorer_agreement = False
    custodian.adjudicated_by = "wrong-adjudicator"
    custodian.adjudication_digest = _digest("adjudication")
    _refusal(evaluation, "E_SCORER_DISAGREEMENT")


@pytest.mark.parametrize("flag", ["duplicate_blind_token", "blind_verified"])
def test_duplicate_or_unverified_blind_mapping_refuses(evaluation, flag: str) -> None:
    setattr(evaluation[1], flag, flag == "duplicate_blind_token")
    _refusal(evaluation, "E_BLINDING_COMPROMISED")


@pytest.mark.parametrize("mode", ["throw", "wrong"])
def test_append_only_receipt_conflict_refuses(evaluation, mode: str) -> None:
    store = evaluation[4]
    store.conflict = mode == "throw"
    store.wrong_commitment = mode == "wrong"
    _refusal(evaluation, "E_RECEIPT_CONFLICT")
    assert store.receipt is None


def test_candidate_mutation_by_external_worker_refuses(evaluation) -> None:
    evaluation[3].mutate_candidate = True
    _refusal(evaluation, "E_CANDIDATE_MUTATED")
    assert evaluation[4].receipt is None


def test_public_scenario_rejects_protected_fields() -> None:
    with pytest.raises(ValidationError):
        PublicScenario(
            format="ontowiz-public-evaluation-scenario",
            format_version=1,
            scenario_handle="opaque",
            instructions="Synthetic prompt",
            inputs={"nested": {"oracle": "must not cross"}},
        )


def test_malformed_external_return_cannot_leak_protected_detail(evaluation) -> None:
    class MalformedRecord:
        def model_dump(self):  # type: ignore[no-untyped-def]
            raise RuntimeError("C:/protected/vault/secret-case.json")

    class MalformedCustodian(_Custodian):
        def preregistration(self):  # type: ignore[no-untyped-def]
            return MalformedRecord()

    malformed = MalformedCustodian(evaluation[2].candidate_digest)
    evaluation = list(evaluation)
    evaluation[1] = malformed
    evaluation[3] = _Worker(malformed, evaluation[0])
    _refusal(evaluation, "E_PROVIDER_UNAVAILABLE")


def test_truthy_signature_verifier_result_is_not_accepted(evaluation) -> None:
    class TruthyVerifierCustodian(_Custodian):
        def verify_preregistration(self, record):  # type: ignore[no-untyped-def]
            assert record == self.prereg
            return "invalid"

    custodian = TruthyVerifierCustodian(evaluation[2].candidate_digest)
    evaluation = list(evaluation)
    evaluation[1] = custodian
    evaluation[3] = _Worker(custodian, evaluation[0])
    _refusal(evaluation, "E_PREREG_UNAPPROVED")


def test_provider_error_is_redacted(evaluation) -> None:
    class BrokenCustodian(_Custodian):
        def preregistration(self) -> PreregistrationRecord:
            raise RuntimeError("C:/protected/vault/secret-case.json")

    broken = BrokenCustodian(evaluation[2].candidate_digest)
    evaluation = list(evaluation)
    evaluation[1] = broken
    evaluation[3] = _Worker(broken, evaluation[0])
    _refusal(evaluation, "E_PROVIDER_UNAVAILABLE")


def test_freeze_requires_approval_isolation_and_current_lock(evaluation) -> None:
    custodian = evaluation[1]
    frozen = freeze_heldout_suite(
        custodian,
        drafting_principal=custodian.proof.drafting_principal,
        worker_principal=custodian.proof.worker_principal,
        evaluator_principal=custodian.proof.evaluator_principal,
    )
    assert frozen == custodian.suite


def test_invalid_archive_refuses_before_provider_access(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.owpack"
    invalid.write_bytes(b"not a zip")
    digest = _digest("not a zip")
    custodian = _Custodian(digest)
    plan = EvaluationRunPlan(
        format="ontowiz-evaluation-run-plan",
        format_version=1,
        run_id="invalid-run",
        candidate_digest=digest,
        preregistration_digest=custodian.prereg.preregistration_digest,
        suite_digest=custodian.suite.suite_digest,
        arms=custodian.prereg.arms,
        repetitions=custodian.prereg.repetitions,
        drafting_principal=custodian.proof.drafting_principal,
        worker_principal=custodian.proof.worker_principal,
        evaluator_principal=custodian.proof.evaluator_principal,
        blinding_commitment_digest=_digest("blinding"),
        execution=ExecutionDigests(
            agent_digest=_digest("agent"),
            adapter_build_digest=_digest("adapter"),
            model_digest=_digest("model"),
            prompt_digest=_digest("prompt"),
            retrieval_digest=_digest("retrieval"),
            tool_digest=_digest("tools"),
            data_digest=_digest("data"),
            evaluator_build_digest=_digest("evaluator"),
        ),
        approved_plan_signature_digest=_digest("plan-signature"),
        created_at="2026-07-25T12:03:00Z",
    )
    with pytest.raises(EvaluationRefusal, match="E_CANDIDATE_DRIFT"):
        EvaluationCoordinator().evaluate(
            invalid,
            plan,
            custodian=custodian,
            worker=_Worker(custodian, invalid),
            receipt_store=_Store(),
        )
