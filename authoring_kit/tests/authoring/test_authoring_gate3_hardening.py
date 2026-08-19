from __future__ import annotations

import json
import os
import shutil
import subprocess
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path
from threading import Event, Thread

import pytest
from pydantic import ValidationError
from test_authoring_flow import (
    _TEST_PROVIDERS,
    _canonical,
    _decision,
    _digest,
    _intent,
    _prepare_evidence,
    _prepare_proposal,
    _propose,
    _provider,
    _source,
    _TestTrustProvider,
    _workspace,
    _write_pack_document,
    compile_questions,
    confirm_proposal,
    get_workspace_revision,
    register_source,
    update_session_state,
    withdraw_source,
)

import ontowiz_authoring.authoring as authoring_module
from ontowiz_authoring.authoring import (
    AuthoringAtomicError,
    AuthoringTrustContext,
    AuthorizationError,
    OperationCredential,
    PrincipalGrant,
)
from ontowiz_authoring.workspace import WorkspaceError


class _InjectedExitError(RuntimeError):
    pass


def _kill_after(point: str):
    def inject(actual: str) -> None:
        if actual == point:
            raise _InjectedExitError(point)

    return inject


def _journal_path(workspace: object) -> Path:
    root = workspace.root if hasattr(workspace, "root") else Path(workspace)
    journals = sorted((root / "locks" / "transactions").glob("*.journal"))
    assert len(journals) == 1
    return journals[0]


def _rebind_external_transaction(
    provider: _TestTrustProvider,
    journal_path: Path,
    data: dict[str, object],
) -> None:
    draft = authoring_module._TransactionJournal.model_validate(data)
    pending = provider.authoring_state(draft.workspace_id).pending
    assert pending is not None
    changes = tuple(
        sorted(
            (
                authoring_module.AuthoringTransactionChange(
                    kind=change.kind,
                    entity_id=change.entity_id,
                    before_digest=change.before_digest,
                    after_digest=change.after_digest,
                )
                for change in draft.changes
            ),
            key=lambda change: (change.kind, change.entity_id or ""),
        )
    )
    identity = pending.model_copy(
        update={
            "workspace_id": draft.workspace_id,
            "transaction_id": draft.transaction_id,
            "operation": draft.operation,
            "revision_before": draft.revision_before,
            "revision_after": draft.revision_after,
            "intent_digest": draft.intent_digest,
            "authority_revision": draft.authority_before_revision,
            "authority_digest": draft.authority_before_digest,
            "delta_id": draft.delta_id,
            "target_path": draft.target_path,
            "changes": changes,
        }
    )
    journal = draft.model_copy(
        update={
            "provider_transaction_digest": (
                authoring_module.authoring_transaction_digest(identity)
            )
        }
    )
    provider.force_pending_for_test(identity)
    journal_path.write_bytes(_canonical(journal.model_dump(mode="json")))


@pytest.mark.adversarial
def test_production_surface_has_no_workspace_trust_bootstrap_or_capability_loader(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path)
    assert not hasattr(authoring_module, "bootstrap_authority_trust")
    assert not hasattr(authoring_module, "load_actor_capability")
    assert not (workspace.root / "locks" / "authority-trust.json").exists()
    with pytest.raises(TypeError):
        authoring_module.get_workspace_revision(workspace)  # type: ignore[call-arg]


@pytest.mark.adversarial
def test_operation_credential_rejects_wrong_intent_bad_pop_and_nonce_replay(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path)
    provider = _provider(workspace)
    source = _source(id="SRC-CREDENTIAL")
    request = {
        "source": source.model_dump(mode="json"),
        "material_path": None,
    }
    correct_intent = _intent("register_source", workspace, None, request)
    wrong_context = provider.context(
        provider.actor("draft-agent"),
        "sha256:" + "0" * 64,
    )
    with pytest.raises(AuthorizationError, match="another intent"):
        authoring_module.register_source(
            workspace,
            source,
            trust=wrong_context,
        )

    context = provider.context(provider.actor("draft-agent"), correct_intent)
    bad_credential = context.credential.model_copy(update={"proof_signature": "0" * 128})
    with pytest.raises(AuthorizationError, match="proof-of-possession"):
        authoring_module.register_source(
            workspace,
            source,
            trust=AuthoringTrustContext(
                provider=provider,
                credential=bad_credential,
            ),
        )

    replay_context = provider.context(provider.actor("draft-agent"), correct_intent)
    assert (
        authoring_module.register_source(
            workspace,
            source,
            trust=replay_context,
        )
        == source
    )
    with pytest.raises(AuthorizationError, match="proof-of-possession"):
        authoring_module.register_source(
            workspace,
            source,
            trust=replay_context,
        )


@pytest.mark.adversarial
def test_authority_cache_rollback_and_external_anchor_swap_fail_closed(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path)
    provider = _provider(workspace)
    cache = workspace.root / "locks" / "authoring-authority.json"
    revision_one = cache.read_bytes()
    grants = (
        PrincipalGrant(
            principal_id="brand-1",
            roles=("brand_owner",),
            client_boundary="client-a",
        ),
        PrincipalGrant(
            principal_id="draft-agent",
            roles=("steward",),
            client_boundary="client-a",
        ),
    )
    from test_authoring_flow import _install_authority

    _install_authority(
        workspace,
        grants=grants,
        authority_revision=2,
    )
    revision_two = cache.read_bytes()
    cache.write_bytes(revision_one)
    with pytest.raises(AuthorizationError, match="rollback"):
        get_workspace_revision(workspace)

    cache.write_bytes(revision_two)
    replacement = _TestTrustProvider(
        workspace.manifest.workspace_id,
        provider._journal_key,
    )
    replacement._high_water = replacement._high_water.model_copy(
        update={
            "authority_revision": provider._high_water.authority_revision,
            "authority_digest": provider._high_water.authority_digest,
        }
    )
    _TEST_PROVIDERS[str(workspace.root.absolute())] = replacement
    with pytest.raises(AuthorizationError, match="wrong trust key|substitution"):
        get_workspace_revision(workspace)


@pytest.mark.adversarial
def test_tampered_or_unbound_journal_recovery_fails_before_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _workspace(tmp_path)
    provider = _provider(workspace)
    monkeypatch.setattr(
        authoring_module,
        "_TEST_KILL_POINT",
        _kill_after("after-register_source-journal"),
    )
    with pytest.raises(_InjectedExitError):
        register_source(workspace, _source(id="SRC-JOURNAL"))
    monkeypatch.setattr(authoring_module, "_TEST_KILL_POINT", None)
    journal_path = _journal_path(workspace)
    data = json.loads(journal_path.read_text(encoding="utf-8"))
    original_intent = data["intent_digest"]
    data["intent_digest"] = "sha256:" + "0" * 64
    journal_path.write_bytes(_canonical(data))
    with pytest.raises(AuthoringAtomicError, match="external transaction identity"):
        get_workspace_revision(workspace)
    assert all(
        source.id != "SRC-JOURNAL"
        for source in authoring_module._load_source_register(workspace).sources
    )

    data["intent_digest"] = original_intent
    data["provider_transaction_digest"] = "sha256:" + "0" * 64
    journal_path.write_bytes(_canonical(data))
    with pytest.raises(AuthoringAtomicError, match="external transaction identity"):
        get_workspace_revision(workspace)
    assert provider.authority_high_water(workspace.manifest.workspace_id).authority_revision == 1


@pytest.mark.adversarial
def test_externally_reserved_self_consistent_source_resurrection_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _workspace(tmp_path)
    provider = _provider(workspace)
    register_source(workspace, _source())
    withdraw_source(
        workspace,
        "SRC-001",
        withdrawn_at=datetime(2026, 7, 26, tzinfo=UTC),
    )
    monkeypatch.setattr(
        authoring_module,
        "_TEST_KILL_POINT",
        _kill_after("after-register_source-journal"),
    )
    with pytest.raises(_InjectedExitError):
        register_source(
            workspace,
            _source(
                id="SRC-SECOND",
                checksum="sha256:" + "c" * 64,
            ),
        )
    monkeypatch.setattr(authoring_module, "_TEST_KILL_POINT", None)

    journal_path = _journal_path(workspace)
    data = json.loads(journal_path.read_text(encoding="utf-8"))
    source_index = next(
        index for index, change in enumerate(data["changes"]) if change["kind"] == "source_register"
    )
    stem = data["transaction_id"]
    before_path = workspace.root / "locks" / "transactions" / f"{stem}-{source_index:02}.before"
    stage_path = workspace.root / "locks" / "transactions" / f"{stem}-{source_index:02}.stage"
    register = json.loads(before_path.read_text(encoding="utf-8"))
    resurrected = register["sources"][0]
    resurrected["status"] = "current"
    resurrected["withdrawn_at"] = None
    payload = _canonical(register)
    stage_path.write_bytes(payload)
    data["changes"][source_index]["entity_id"] = "SRC-001"
    data["changes"][source_index]["after_digest"] = _digest(payload)
    data["changes"][source_index]["stage_digest"] = _digest(payload)
    _rebind_external_transaction(provider, journal_path, data)

    with pytest.raises(AuthoringAtomicError, match="only-add"):
        get_workspace_revision(workspace)
    persisted = authoring_module._load_source_register(workspace)
    assert persisted.sources[0].status.value == "withdrawn"


@pytest.mark.adversarial
def test_externally_reserved_authority_rollback_journal_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _workspace(tmp_path)
    provider = _provider(workspace)
    from test_authoring_flow import _install_authority

    grants = (
        PrincipalGrant(
            principal_id="brand-1",
            roles=("brand_owner",),
            client_boundary="client-a",
        ),
        PrincipalGrant(
            principal_id="draft-agent",
            roles=("steward",),
            client_boundary="client-a",
        ),
    )
    monkeypatch.setattr(
        authoring_module,
        "_TEST_KILL_POINT",
        _kill_after("after-install_authority-journal"),
    )
    with pytest.raises(_InjectedExitError):
        _install_authority(
            workspace,
            grants=grants,
            authority_revision=2,
        )
    monkeypatch.setattr(authoring_module, "_TEST_KILL_POINT", None)
    journal_path = _journal_path(workspace)
    data = json.loads(journal_path.read_text(encoding="utf-8"))
    authority_index = next(
        index for index, change in enumerate(data["changes"]) if change["kind"] == "authority"
    )
    stem = data["transaction_id"]
    before_path = workspace.root / "locks" / "transactions" / f"{stem}-{authority_index:02}.before"
    stage_path = workspace.root / "locks" / "transactions" / f"{stem}-{authority_index:02}.stage"
    rollback = before_path.read_bytes()
    stage_path.write_bytes(rollback)
    data["changes"][authority_index]["after_digest"] = _digest(rollback)
    data["changes"][authority_index]["stage_digest"] = _digest(rollback)
    _rebind_external_transaction(provider, journal_path, data)
    with pytest.raises(AuthoringAtomicError, match="authority after-state"):
        get_workspace_revision(workspace)
    assert provider.authority_high_water(workspace.manifest.workspace_id).authority_revision == 1


@pytest.mark.adversarial
def test_linked_locks_directory_causes_zero_outside_creation_or_deletion(
    tmp_path: Path,
) -> None:
    workspace = _workspace(tmp_path)
    outside = tmp_path / "outside-locks"
    original = tmp_path / "original-locks"
    shutil.move(str(workspace.root / "locks"), original)
    outside.mkdir()
    sentinel = outside / "sentinel.txt"
    sentinel.write_text("preserve", encoding="utf-8")
    link = workspace.root / "locks"
    try:
        os.symlink(outside, link, target_is_directory=True)
    except OSError as exc:
        if os.name != "nt":
            pytest.skip(f"directory symlink unavailable: {exc}")
        result = subprocess.run(
            ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(outside)],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            pytest.skip(f"directory junction unavailable: {result.stderr}")
    with pytest.raises(AuthoringAtomicError, match="ordinary directories"):
        get_workspace_revision(workspace)
    assert sentinel.read_text(encoding="utf-8") == "preserve"
    assert not (outside / "authoring.lock").exists()


@pytest.mark.adversarial
def test_operation_credential_contract_forbids_unbounded_extra_claims() -> None:
    with pytest.raises(ValidationError):
        OperationCredential.model_validate(
            {
                "format": "ontowiz-operation-credential",
                "format_version": 1,
                "workspace_id": "brand-variance",
                "principal_id": "draft-agent",
                "roles": ["steward"],
                "client_boundary": "client-a",
                "authority_revision": 1,
                "authority_digest": "sha256:" + "a" * 64,
                "trust_key_id": "sha256:" + "b" * 64,
                "intent_digest": "sha256:" + "c" * 64,
                "nonce": "nonce-1",
                "issued_at": "2026-07-25T00:00:00Z",
                "expires_at": "2026-07-26T00:00:00Z",
                "actor_key_id": "sha256:" + "d" * 64,
                "proof_signature": "0" * 128,
                "ambient_admin": True,
            }
        )


@pytest.mark.adversarial
@pytest.mark.parametrize(
    ("point", "recovers_as_committed"),
    (
        ("before-register_source-reserve", False),
        ("after-register_source-reserve", False),
        ("after-register_source-journal", True),
        ("after-register_source-apply", True),
        ("after-register_source-finalize", True),
        ("after-register_source-cleanup", True),
    ),
)
def test_external_transaction_lifecycle_crash_windows_converge(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    point: str,
    recovers_as_committed: bool,
) -> None:
    workspace = _workspace(tmp_path)
    provider = _provider(workspace)
    source = _source(id="SRC-LIFECYCLE")
    before_revision = get_workspace_revision(workspace)
    monkeypatch.setattr(
        authoring_module,
        "_TEST_KILL_POINT",
        _kill_after(point),
    )
    with pytest.raises(_InjectedExitError):
        register_source(workspace, source)
    monkeypatch.setattr(authoring_module, "_TEST_KILL_POINT", None)

    recovered_revision = get_workspace_revision(workspace)
    state = provider.authoring_state(workspace.manifest.workspace_id)
    records = authoring_module._unique_sources(authoring_module._load_source_register(workspace))
    assert state.pending is None
    assert recovered_revision == state.authoring_revision
    if recovers_as_committed:
        assert recovered_revision == before_revision + 1
        assert records[source.id] == source
    else:
        assert recovered_revision == before_revision
        assert source.id not in records
    transaction_dir = workspace.root / "locks" / "transactions"
    assert not tuple(transaction_dir.glob("*.journal"))
    assert not tuple(transaction_dir.glob("*.stage"))
    assert not tuple(transaction_dir.glob("*.before"))


@pytest.mark.adversarial
def test_finalized_transaction_replay_after_later_mutation_is_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _workspace(tmp_path)
    provider = _provider(workspace)
    transaction_dir = workspace.root / "locks" / "transactions"
    source_a = _source(id="SRC-REPLAY-A")
    monkeypatch.setattr(
        authoring_module,
        "_TEST_KILL_POINT",
        _kill_after("after-register_source-journal"),
    )
    with pytest.raises(_InjectedExitError):
        register_source(workspace, source_a)
    monkeypatch.setattr(authoring_module, "_TEST_KILL_POINT", None)
    replay_files = {
        path.name: path.read_bytes()
        for path in transaction_dir.iterdir()
        if path.suffix in {".journal", ".stage", ".before"}
    }
    source_before = (workspace.root / "sources" / "source-register.yaml").read_bytes()
    revision_path = workspace.root / "locks" / "authoring-revision.json"
    revision_before = revision_path.read_bytes()

    get_workspace_revision(workspace)
    register_source(workspace, _source(id="SRC-REPLAY-B"))
    finalized_state = provider.authoring_state(workspace.manifest.workspace_id)
    (workspace.root / "sources" / "source-register.yaml").write_bytes(source_before)
    revision_path.write_bytes(revision_before)
    for name, payload in replay_files.items():
        (transaction_dir / name).write_bytes(payload)

    with pytest.raises(
        AuthoringAtomicError,
        match="external transaction identity is unavailable",
    ):
        get_workspace_revision(workspace)
    assert provider.authoring_state(workspace.manifest.workspace_id) == finalized_state
    assert (workspace.root / "sources" / "source-register.yaml").read_bytes() == source_before
    assert revision_path.read_bytes() == revision_before


@pytest.mark.adversarial
def test_externally_reserved_proposal_with_forged_actor_is_rejected_live(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _workspace(tmp_path)
    provider = _provider(workspace)
    drafter, _, _ = _prepare_evidence(workspace)
    target = _write_pack_document(
        workspace,
        "pack/scope/decision.json",
        _decision("Recommend the initial response to NBRx variance."),
    )
    replacement = _decision("Recommend the edited, evidence-qualified response to NBRx variance.")
    monkeypatch.setattr(
        authoring_module,
        "_TEST_KILL_POINT",
        _kill_after("after-propose-journal"),
    )
    with pytest.raises(_InjectedExitError):
        _propose(
            workspace,
            drafter,
            expected_target_digest=_digest(target.read_bytes()),
            replacement=replacement,
        )
    monkeypatch.setattr(authoring_module, "_TEST_KILL_POINT", None)
    journal_path = _journal_path(workspace)
    data = json.loads(journal_path.read_text(encoding="utf-8"))
    proposal_index = next(
        index for index, change in enumerate(data["changes"]) if change["kind"] == "proposal"
    )
    stem = data["transaction_id"]
    stage_path = workspace.root / "locks" / "transactions" / f"{stem}-{proposal_index:02}.stage"
    proposal_data = json.loads(stage_path.read_text(encoding="utf-8"))
    proposal_data["proposer_principal"] = "brand-1"
    proposal_payload = _canonical(proposal_data)
    stage_path.write_bytes(proposal_payload)
    proposal_digest = _digest(proposal_payload)
    data["changes"][proposal_index]["after_digest"] = proposal_digest
    data["changes"][proposal_index]["stage_digest"] = proposal_digest
    data["proposal_after_digest"] = proposal_digest
    _rebind_external_transaction(provider, journal_path, data)

    with pytest.raises(AuthorizationError, match="proposal actor"):
        get_workspace_revision(workspace)
    assert not authoring_module._proposal_path(
        workspace,
        "DELTA-001",
    ).exists()
    assert json.loads(target.read_text(encoding="utf-8")) != replacement


@pytest.mark.adversarial
def test_externally_reserved_session_with_dangling_delta_is_rejected_live(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _workspace(tmp_path)
    provider = _provider(workspace)
    revision = get_workspace_revision(workspace)
    question_ids = tuple(question.id for question in compile_questions(workspace))
    monkeypatch.setattr(
        authoring_module,
        "_TEST_KILL_POINT",
        _kill_after("after-update_session-journal"),
    )
    with pytest.raises(_InjectedExitError):
        update_session_state(
            workspace,
            stage="discover",
            last_delta_id=None,
            open_question_ids=question_ids,
            next_mission="discover",
            expected_revision=revision,
        )
    monkeypatch.setattr(authoring_module, "_TEST_KILL_POINT", None)
    journal_path = _journal_path(workspace)
    data = json.loads(journal_path.read_text(encoding="utf-8"))
    stem = data["transaction_id"]
    session_index = next(
        index for index, change in enumerate(data["changes"]) if change["kind"] == "session"
    )
    revision_index = next(
        index for index, change in enumerate(data["changes"]) if change["kind"] == "revision"
    )
    session_stage = workspace.root / "locks" / "transactions" / f"{stem}-{session_index:02}.stage"
    session_data = json.loads(session_stage.read_text(encoding="utf-8"))
    session_data["last_delta_id"] = "DELTA-MISSING"
    session_payload = _canonical(session_data)
    session_stage.write_bytes(session_payload)
    session_digest = _digest(session_payload)
    data["changes"][session_index]["after_digest"] = session_digest
    data["changes"][session_index]["stage_digest"] = session_digest
    data["session_after_digest"] = session_digest

    revision_stage = workspace.root / "locks" / "transactions" / f"{stem}-{revision_index:02}.stage"
    revision_data = json.loads(revision_stage.read_text(encoding="utf-8"))
    revision_data["session_digest"] = session_digest
    revision_payload = _canonical(revision_data)
    revision_stage.write_bytes(revision_payload)
    revision_digest = _digest(revision_payload)
    data["changes"][revision_index]["after_digest"] = revision_digest
    data["changes"][revision_index]["stage_digest"] = revision_digest
    _rebind_external_transaction(provider, journal_path, data)

    with pytest.raises(WorkspaceError, match="proposal|DELTA-MISSING"):
        get_workspace_revision(workspace)
    assert not authoring_module._session_path(workspace).exists()


@pytest.mark.adversarial
@pytest.mark.skipif(os.name != "nt", reason="Windows relative-handle race")
def test_windows_lock_directory_swap_race_creates_nothing_outside(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _workspace(tmp_path)
    locks = workspace.root / "locks"
    moved = workspace.root / "locks-before-race"
    outside = tmp_path / "outside-race"
    outside.mkdir()
    sentinel = outside / "sentinel.txt"
    sentinel.write_text("preserve", encoding="utf-8")
    start = Event()
    finished = Event()
    attack_errors: list[BaseException] = []

    def attacker() -> None:
        assert start.wait(5)
        try:
            os.replace(locks, moved)
            result = subprocess.run(
                [
                    "cmd.exe",
                    "/d",
                    "/c",
                    "mklink",
                    "/J",
                    str(locks),
                    str(outside),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                attack_errors.append(RuntimeError(result.stderr))
        except BaseException as exc:
            attack_errors.append(exc)
        finally:
            finished.set()

    thread = Thread(target=attacker)
    thread.start()

    def inject(point: str) -> None:
        if point == "before-windows-relative-lock-create":
            start.set()
            assert finished.wait(10)

    monkeypatch.setattr(authoring_module, "_TEST_KILL_POINT", inject)
    try:
        with suppress(AuthoringAtomicError):
            get_workspace_revision(workspace)
    finally:
        monkeypatch.setattr(authoring_module, "_TEST_KILL_POINT", None)
        thread.join(timeout=10)
    assert not thread.is_alive()
    assert sentinel.read_text(encoding="utf-8") == "preserve"
    assert not (outside / "authoring.lock").exists()
    assert start.is_set() and finished.is_set()
    assert moved.exists() or attack_errors


class _ExpiredRecoveryClock(datetime):
    @classmethod
    def now(cls, tz: object = None) -> datetime:
        del tz
        return datetime(2040, 1, 1, tzinfo=UTC)


@pytest.mark.adversarial
@pytest.mark.parametrize(
    "cleanup_point",
    (
        "after-register_source-cleanup-unlink-journal",
        "after-register_source-cleanup-unlink-0-before",
        "after-register_source-cleanup-unlink-0-stage",
        "after-register_source-cleanup-unlink-1-before",
        "after-register_source-cleanup-unlink-1-stage",
    ),
)
def test_finalized_cleanup_crashes_are_idempotent_without_stages(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    cleanup_point: str,
) -> None:
    workspace = _workspace(tmp_path)
    provider = _provider(workspace)
    source = _source(id="SRC-CLEANUP")
    before = get_workspace_revision(workspace)
    monkeypatch.setattr(
        authoring_module,
        "_TEST_KILL_POINT",
        _kill_after(cleanup_point),
    )
    with pytest.raises(_InjectedExitError):
        register_source(workspace, source)
    monkeypatch.setattr(authoring_module, "_TEST_KILL_POINT", None)
    finalized = provider.authoring_state(workspace.manifest.workspace_id)

    assert get_workspace_revision(workspace) == before + 1
    assert provider.authoring_state(workspace.manifest.workspace_id) == finalized
    assert (
        authoring_module._unique_sources(authoring_module._load_source_register(workspace))[
            source.id
        ]
        == source
    )
    transaction_dir = workspace.root / "locks" / "transactions"
    assert not tuple(transaction_dir.glob("*.journal"))
    assert not tuple(transaction_dir.glob("*.stage"))
    assert not tuple(transaction_dir.glob("*.before"))


@pytest.mark.adversarial
def test_pending_recovery_authentication_survives_credential_expiry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _workspace(tmp_path)
    provider = _provider(workspace)
    source = _source(id="SRC-EXPIRED-PENDING")
    before = get_workspace_revision(workspace)
    monkeypatch.setattr(
        authoring_module,
        "_TEST_KILL_POINT",
        _kill_after("after-register_source-journal"),
    )
    with pytest.raises(_InjectedExitError):
        register_source(workspace, source)
    monkeypatch.setattr(authoring_module, "_TEST_KILL_POINT", None)
    monkeypatch.setattr(authoring_module, "datetime", _ExpiredRecoveryClock)

    assert get_workspace_revision(workspace) == before + 1
    assert provider.authoring_state(workspace.manifest.workspace_id).pending is None


@pytest.mark.adversarial
def test_finalized_cleanup_survives_expiry_and_missing_stage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _workspace(tmp_path)
    provider = _provider(workspace)
    source = _source(id="SRC-EXPIRED-FINAL")
    monkeypatch.setattr(
        authoring_module,
        "_TEST_KILL_POINT",
        _kill_after("after-register_source-finalize"),
    )
    with pytest.raises(_InjectedExitError):
        register_source(workspace, source)
    monkeypatch.setattr(authoring_module, "_TEST_KILL_POINT", None)
    transaction_dir = workspace.root / "locks" / "transactions"
    next(transaction_dir.glob("*.stage")).unlink()
    monkeypatch.setattr(authoring_module, "datetime", _ExpiredRecoveryClock)
    finalized = provider.authoring_state(workspace.manifest.workspace_id)

    assert get_workspace_revision(workspace) == finalized.authoring_revision
    assert provider.authoring_state(workspace.manifest.workspace_id) == finalized
    assert not tuple(transaction_dir.glob("*.journal"))
    assert not tuple(transaction_dir.glob("*.stage"))
    assert not tuple(transaction_dir.glob("*.before"))


@pytest.mark.adversarial
def test_recovery_authentication_rejects_wrong_external_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _workspace(tmp_path)
    provider = _provider(workspace)
    monkeypatch.setattr(
        authoring_module,
        "_TEST_KILL_POINT",
        _kill_after("after-register_source-journal"),
    )
    with pytest.raises(_InjectedExitError):
        register_source(workspace, _source(id="SRC-WRONG-RECOVERY"))
    monkeypatch.setattr(authoring_module, "_TEST_KILL_POINT", None)
    journal = authoring_module._load_canonical_model(
        _journal_path(workspace),
        authoring_module._TransactionJournal,
    )
    identity = provider.authoring_state(journal.workspace_id).pending
    assert identity is not None
    authorization = provider.authorize_recovery(identity)
    wrong = identity.model_copy(update={"actor_principal": "brand-1"})
    with pytest.raises(RuntimeError, match="mismatch"):
        provider.authenticate_recovery(wrong, authorization)
    get_workspace_revision(workspace)


def _forge_confirmation_session(
    workspace: object,
    provider: _TestTrustProvider,
    mutation: str,
) -> None:
    journal_path = _journal_path(workspace)
    data = json.loads(journal_path.read_text(encoding="utf-8"))
    stem = data["transaction_id"]
    session_index = next(
        index for index, change in enumerate(data["changes"]) if change["kind"] == "session"
    )
    revision_index = next(
        index for index, change in enumerate(data["changes"]) if change["kind"] == "revision"
    )
    transaction_dir = journal_path.parent
    session_path = transaction_dir / f"{stem}-{session_index:02}.stage"
    session = json.loads(session_path.read_text(encoding="utf-8"))
    if mutation == "missing_delta":
        session["last_delta_id"] = None
    elif mutation == "stale_questions":
        session["open_question_ids"] = ["Q-STALE-0000000000000000"]
    elif mutation == "stage":
        session["stage"] = "ratify"
    else:
        session["next_mission"] = "ratify"
    session_payload = _canonical(session)
    session_path.write_bytes(session_payload)
    session_digest = _digest(session_payload)
    data["changes"][session_index]["after_digest"] = session_digest
    data["changes"][session_index]["stage_digest"] = session_digest
    data["session_after_digest"] = session_digest
    revision_path = transaction_dir / f"{stem}-{revision_index:02}.stage"
    revision = json.loads(revision_path.read_text(encoding="utf-8"))
    revision["session_digest"] = session_digest
    revision_payload = _canonical(revision)
    revision_path.write_bytes(revision_payload)
    revision_digest = _digest(revision_payload)
    data["changes"][revision_index]["after_digest"] = revision_digest
    data["changes"][revision_index]["stage_digest"] = revision_digest
    _rebind_external_transaction(provider, journal_path, data)


@pytest.mark.adversarial
@pytest.mark.parametrize(
    "mutation",
    ("missing_delta", "stale_questions", "stage", "mission"),
)
def test_externally_reserved_confirmation_session_drift_rejects_before_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    workspace = _workspace(tmp_path)
    provider = _provider(workspace)
    target, _, _, owner = _prepare_proposal(workspace)
    target_before = target.read_bytes()
    proposal_before = authoring_module._load_proposal_path(
        workspace,
        authoring_module._proposal_path(workspace, "DELTA-001"),
    )
    monkeypatch.setattr(
        authoring_module,
        "_TEST_KILL_POINT",
        _kill_after("after-confirm-journal"),
    )
    with pytest.raises(_InjectedExitError):
        confirm_proposal(
            workspace,
            "DELTA-001",
            actor=owner,
            confirmed_at=datetime(2026, 7, 25, 13, 0, tzinfo=UTC),
        )
    monkeypatch.setattr(authoring_module, "_TEST_KILL_POINT", None)
    _forge_confirmation_session(workspace, provider, mutation)

    with pytest.raises(
        AuthoringAtomicError,
        match="confirmation session|intent",
    ):
        get_workspace_revision(workspace)
    assert target.read_bytes() == target_before
    assert (
        authoring_module._load_proposal_path(
            workspace,
            authoring_module._proposal_path(workspace, "DELTA-001"),
        )
        == proposal_before
    )
    assert not authoring_module._session_path(workspace).exists()


def _pending_confirmation_with_lagging_session(
    workspace: object,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, bytes, object]:
    revision = get_workspace_revision(workspace)
    update_session_state(
        workspace,
        stage="ratify",
        last_delta_id=None,
        open_question_ids=(),
        next_mission="ratify",
        expected_revision=revision,
    )
    target, _, _, owner = _prepare_proposal(workspace)
    target_before = target.read_bytes()
    monkeypatch.setattr(
        authoring_module,
        "_TEST_KILL_POINT",
        _kill_after("after-confirm-journal"),
    )
    with pytest.raises(_InjectedExitError):
        confirm_proposal(
            workspace,
            "DELTA-001",
            actor=owner,
            confirmed_at=datetime(2026, 7, 25, 13, 0, tzinfo=UTC),
        )
    monkeypatch.setattr(authoring_module, "_TEST_KILL_POINT", None)
    return target, target_before, owner


@pytest.mark.adversarial
def test_confirmation_recovery_accepts_session_lagging_workspace_revision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _workspace(tmp_path)
    target, _, _ = _pending_confirmation_with_lagging_session(
        workspace,
        monkeypatch,
    )
    before_recovery = authoring_module._load_revision(workspace).revision

    assert get_workspace_revision(workspace) == before_recovery + 1
    proposal = authoring_module._load_proposal_path(
        workspace,
        authoring_module._proposal_path(workspace, "DELTA-001"),
    )
    session = authoring_module._load_session_optional(workspace)
    assert proposal.status == "confirmed"
    assert session is not None
    assert session.revision == before_recovery + 1
    assert session.stage == "ratify"
    assert session.next_mission == "ratify"
    assert session.last_delta_id == "DELTA-001"
    assert session.open_question_ids == ()
    assert _digest(target.read_bytes()) == proposal.replacement_digest


@pytest.mark.adversarial
def test_confirmation_recovery_rejects_future_prior_session_revision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = _workspace(tmp_path)
    provider = _provider(workspace)
    target, target_before, _ = _pending_confirmation_with_lagging_session(
        workspace,
        monkeypatch,
    )
    journal_path = _journal_path(workspace)
    data = json.loads(journal_path.read_text(encoding="utf-8"))
    stem = data["transaction_id"]
    transaction_dir = journal_path.parent
    session_index = next(
        index
        for index, change in enumerate(data["changes"])
        if change["kind"] == "session"
    )
    revision_index = next(
        index
        for index, change in enumerate(data["changes"])
        if change["kind"] == "revision"
    )
    session_before_path = (
        transaction_dir / f"{stem}-{session_index:02}.before"
    )
    session_before = json.loads(
        session_before_path.read_text(encoding="utf-8")
    )
    session_before["revision"] = data["revision_before"] + 1
    session_before_payload = _canonical(session_before)
    session_before_digest = _digest(session_before_payload)
    session_before_path.write_bytes(session_before_payload)
    authoring_module._session_path(workspace).write_bytes(
        session_before_payload
    )
    data["changes"][session_index]["before_digest"] = session_before_digest
    data["changes"][session_index][
        "before_stage_digest"
    ] = session_before_digest
    data["session_before_digest"] = session_before_digest

    revision_before_path = (
        transaction_dir / f"{stem}-{revision_index:02}.before"
    )
    revision_before = json.loads(
        revision_before_path.read_text(encoding="utf-8")
    )
    revision_before["session_digest"] = session_before_digest
    revision_before_payload = _canonical(revision_before)
    revision_before_digest = _digest(revision_before_payload)
    revision_before_path.write_bytes(revision_before_payload)
    (
        workspace.root / "locks" / "authoring-revision.json"
    ).write_bytes(revision_before_payload)
    data["changes"][revision_index]["before_digest"] = revision_before_digest
    data["changes"][revision_index][
        "before_stage_digest"
    ] = revision_before_digest
    _rebind_external_transaction(provider, journal_path, data)

    with pytest.raises(
        AuthoringAtomicError,
        match="before-state is not canonical",
    ):
        get_workspace_revision(workspace)
    assert target.read_bytes() == target_before
    assert authoring_module._load_proposal_path(
        workspace,
        authoring_module._proposal_path(workspace, "DELTA-001"),
    ).status == "proposed"
