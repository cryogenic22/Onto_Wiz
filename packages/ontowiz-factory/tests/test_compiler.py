"""Loop 1 (F2-A) — pack compiler tests."""

from __future__ import annotations

from ontowiz_factory.compiler import CompiledPack, compile_pack
from ontowiz_spec import DataQuirk, Lifecycle, MetricDefinition


def _active(art):
    return art.transition(Lifecycle.ACTIVE, changed_by="curator", delta_id="d1")


def test_compile_includes_only_active_artifacts():
    dq = _active(DataQuirk(id="dq1", name="iqvia-lag", data_source="IQVIA"))
    draft = MetricDefinition(id="m1", name="trx")  # stays DRAFT
    pack = compile_pack([dq, draft], name="commercial_analytics", version="0.1.0")
    assert isinstance(pack, CompiledPack)
    assert pack.manifest.name == "commercial_analytics"
    assert pack.manifest.version == "0.1.0"
    assert pack.manifest.artifact_count == 1
    names = [s.name.lower() for s in pack.l2_doc.body]
    assert any("dq1" in n for n in names)
    assert all("m1" not in n for n in names)  # draft excluded from the pack


def test_manifest_counts_kinds():
    pack = compile_pack(
        [_active(DataQuirk(id="dq1", name="q")), _active(MetricDefinition(id="m1", name="trx"))],
        name="p", version="0.1.0",
    )
    assert pack.manifest.artifact_count == 2
    assert pack.manifest.artifact_kinds["data_quirk"] == 1
    assert pack.manifest.artifact_kinds["metric_definition"] == 1


def test_l3_directory_is_hydration_map():
    pack = compile_pack([_active(DataQuirk(id="dq1", name="iqvia-lag"))], name="p", version="0.1.0")
    assert "ctx/hydrate" in pack.l3_directory
    assert "dq1" in pack.l3_directory.lower()
    # serializable L2 context layer
    assert "dq1" in pack.l2_text().lower()


def test_empty_pack_is_valid():
    pack = compile_pack([], name="p", version="0.1.0")
    assert pack.manifest.artifact_count == 0
    assert pack.l2_doc.body == ()


def test_compiled_section_carries_knowledge_not_just_metadata():
    # the agent must actually receive the metric's content, not only its name
    m = _active(MetricDefinition(id="trx", name="Total Rx", formula="sum(scripts)"))
    pack = compile_pack([m], name="p", version="0.1.0")
    ctx = pack.l2_text()
    assert "BODY:" in ctx
    assert "sum(scripts)" in ctx  # the formula reaches the compiled context


def test_unbalanced_bracket_in_body_does_not_swallow_next_section():
    # CTX parser continues a value across lines while brackets are unbalanced — an
    # unclosed '[' in a regex/array index would eat the following section. The
    # compiler must neutralise brackets so every section survives the round-trip.
    from ontowiz_ctx.core.model import Section
    from ontowiz_ctx.core.parser import parse

    m1 = _active(MetricDefinition(id="m1", name="m1", formula="value[0 unclosed"))
    m2 = _active(MetricDefinition(id="m2", name="m2", formula="second"))
    pack = compile_pack([m1, m2], name="p", version="0.1.0")
    reparsed = parse(pack.l2_text(), level=2)
    names = {s.name for s in reparsed.body if isinstance(s, Section)}
    assert "METRIC_DEFINITION-M1" in names
    assert "METRIC_DEFINITION-M2" in names  # not swallowed


def test_field_newline_cannot_forge_a_section():
    # a value containing a section marker + newline must not create a 2nd section
    from ontowiz_ctx.core.model import Section
    from ontowiz_ctx.core.parser import parse

    m = _active(MetricDefinition(id="x", name="real\n±FAKE\nID:evil"))
    pack = compile_pack([m], name="p", version="0.1.0")
    reparsed = parse(pack.l2_text(), level=2)
    sections = [e for e in reparsed.body if isinstance(e, Section)]
    assert len(sections) == 1  # the forged ±FAKE never becomes its own section
    assert "FAKE" not in sections[0].name


# ─────────────────────────────────────────────────────────────────────────────
# S1.1 — deterministic, fresh, digest-addressed compile + exact inventory.
# Spec docs/specs/S1-1_DETERMINISTIC_COMPILE.md @ f8a79a3; §10 test grid.
# ─────────────────────────────────────────────────────────────────────────────

import os  # noqa: E402
import threading  # noqa: E402

import pytest  # noqa: E402
import yaml  # noqa: E402
from ontowiz_factory.compiler import (  # noqa: E402
    CandidateDigestConflictError,
    DuplicateArtifactIdentityError,
    DuplicateOutputPathError,
    StagedCandidateInvalidError,
    UnsafeCandidatePathError,
    UnsafePackNameError,
    UnsafePackVersionError,
    verify_candidate_dir,
    write_pack,
)
from ontowiz_spec import PackEvalSummary, PackManifest  # noqa: E402


def _dq(i, name="q"):
    return _active(DataQuirk(id=i, name=name, data_source="IQVIA"))


def _md(i, name="m", formula="sum(x)"):
    return _active(MetricDefinition(id=i, name=name, formula=formula))


def _dir_bytes(root):
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in sorted(root.rglob("*")) if p.is_file()}


# ── #1 determinism: whole candidate dir is byte-identical ────────────────────

def test_shuffled_input_bytes_identical_full_dir(tmp_path):  # T1a
    arts = [_dq("dq1"), _md("m1"), _dq("dq2"), _md("m2")]
    p1 = write_pack(compile_pack(list(arts), name="p", version="0.1.0"), tmp_path / "a")
    p2 = write_pack(compile_pack(list(reversed(arts)), name="p", version="0.1.0"), tmp_path / "b")
    assert _dir_bytes(p1) == _dir_bytes(p2)  # every file, every byte


def test_different_workdir_and_sharding_identical(tmp_path):  # T1b
    arts = [_dq("dq1"), _md("m1"), _dq("dq2")]
    d1 = compile_pack(arts, name="p", version="0.1.0").manifest.candidate_digest
    d2 = compile_pack([arts[2], arts[0], arts[1]], name="p", version="0.1.0").manifest.candidate_digest
    assert d1 == d2 != ""
    pa = write_pack(compile_pack(arts, name="p", version="0.1.0"), tmp_path / "wd1")
    pb = write_pack(compile_pack(arts, name="p", version="0.1.0"), tmp_path / "wd2")
    assert (pa / "pack.yaml").read_bytes() == (pb / "pack.yaml").read_bytes()


def test_repeated_build_seal_and_manifest_identical(tmp_path):  # T1c
    arts = [_dq("dq1"), _md("m1")]
    p1 = write_pack(compile_pack(arts, name="p", version="0.1.0"), tmp_path / "1")
    p2 = write_pack(compile_pack(arts, name="p", version="0.1.0"), tmp_path / "2")
    assert (p1 / "pack.sig").read_bytes() == (p2 / "pack.sig").read_bytes()
    assert (p1 / "pack.yaml").read_bytes() == (p2 / "pack.yaml").read_bytes()


# ── #2 inventory / seal: no undeclared, missing, mismatched, or extra file ───

def test_undeclared_payload_file_rejected(tmp_path):  # T2a
    d = write_pack(compile_pack([_dq("dq1")], name="p", version="0.1.0"), tmp_path)
    assert verify_candidate_dir(d)
    (d / "artifacts" / "sneaky.yaml").write_text("x: 1", encoding="utf-8")
    assert not verify_candidate_dir(d)


def test_missing_declared_payload_rejected(tmp_path):  # T2b
    d = write_pack(compile_pack([_dq("dq1")], name="p", version="0.1.0"), tmp_path)
    next(iter((d / "artifacts").glob("*.yaml"))).unlink()
    assert not verify_candidate_dir(d)


def test_payload_digest_mismatch_rejected(tmp_path):  # T2c
    d = write_pack(compile_pack([_dq("dq1")], name="p", version="0.1.0"), tmp_path)
    (d / "context.ctx").write_text("tampered", encoding="utf-8")
    assert not verify_candidate_dir(d)


def test_unexpected_control_file_rejected(tmp_path):  # T2d
    d = write_pack(compile_pack([_dq("dq1")], name="p", version="0.1.0"), tmp_path)
    (d / "pack.backup").write_text("x", encoding="utf-8")
    assert not verify_candidate_dir(d)


# ── #3 injective output paths ────────────────────────────────────────────────

def test_same_id_different_kind_distinct_paths(tmp_path):  # T3a
    d = write_pack(compile_pack([_dq("x"), _md("x")], name="p", version="0.1.0"), tmp_path)
    files = {p.name for p in (d / "artifacts").glob("*.yaml")}
    assert files == {"data_quirk__x.yaml", "metric_definition__x.yaml"}
    assert verify_candidate_dir(d)


def test_case_fold_output_path_collision_fatal():  # T3b
    # The section-name check is the first line of defense at compile; the path
    # guard is the backstop against a case-insensitive filesystem collision.
    from ontowiz_factory.compiler import _assert_injective_paths
    with pytest.raises(DuplicateOutputPathError):
        _assert_injective_paths(
            ["artifacts/metric_definition__A.yaml", "artifacts/metric_definition__a.yaml"]
        )


def test_duplicate_logical_identity_fatal():  # T3c
    with pytest.raises(DuplicateArtifactIdentityError):
        compile_pack([_md("m1"), _md("m1")], name="p", version="0.1.0")


# ── #4 v1 migration vs conflict ──────────────────────────────────────────────

def _plant_v1(root, *, version="0.1.0"):
    d = root / "p" / version
    (d / "artifacts").mkdir(parents=True)
    (d / "pack.yaml").write_text(
        yaml.safe_dump({"name": "p", "version": version, "artifact_count": 0}), encoding="utf-8"
    )
    (d / "context.ctx").write_text("", encoding="utf-8")
    (d / "index.l3.ctx").write_text("", encoding="utf-8")
    return d


def test_recompile_over_existing_v1_same_version_conflicts(tmp_path):  # T4a
    _plant_v1(tmp_path)
    with pytest.raises(CandidateDigestConflictError):
        write_pack(compile_pack([_dq("dq1")], name="p", version="0.1.0"), tmp_path)


def test_v1_migration_requires_version_bump(tmp_path):  # T4b
    d1 = _plant_v1(tmp_path, version="0.1.0")
    before = (d1 / "pack.yaml").read_bytes()
    d2 = write_pack(compile_pack([_dq("dq1")], name="p", version="0.2.0"), tmp_path)
    assert d2.exists() and (d2 / "pack.yaml").is_file()
    assert (d1 / "pack.yaml").read_bytes() == before  # v1 target untouched


# ── #5 filesystem safety + concurrency ───────────────────────────────────────

@pytest.mark.parametrize("bad", ["../evil", "a/b", "CON", "nul", "UPPER", "a b", ""])
def test_unsafe_name_rejected(bad):  # T5a
    with pytest.raises(UnsafePackNameError):
        compile_pack([_dq("dq1")], name=bad, version="0.1.0")


@pytest.mark.parametrize("bad", ["../1", "0.1", "1.0.0/..", "latest", "1.0.0 "])
def test_unsafe_version_rejected(bad):  # T5b
    with pytest.raises(UnsafePackVersionError):
        compile_pack([_dq("dq1")], name="p", version=bad)


def test_reparse_target_refused(tmp_path):  # T5c
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        os.symlink(outside, root / "p", target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation not permitted on this platform")
    with pytest.raises(UnsafeCandidatePathError):
        write_pack(compile_pack([_dq("dq1")], name="p", version="0.1.0"), root)


def test_concurrent_same_digest_one_dir(tmp_path):  # T5d
    packs = [compile_pack([_dq("dq1")], name="p", version="0.1.0") for _ in range(2)]
    errors: list[Exception] = []
    barrier = threading.Barrier(2)

    def go(pk):
        barrier.wait()
        try:
            write_pack(pk, tmp_path)
        except Exception as e:  # noqa: BLE001
            errors.append(e)

    threads = [threading.Thread(target=go, args=(pk,)) for pk in packs]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    assert [p.name for p in (tmp_path / "p").iterdir()] == ["0.1.0"]


def test_concurrent_different_digest_one_conflicts(tmp_path):  # T5e
    pk_a = compile_pack([_dq("dq1")], name="p", version="0.1.0")
    pk_b = compile_pack([_dq("dq2")], name="p", version="0.1.0")  # different content, same version
    oks: list = []
    conflicts: list = []
    barrier = threading.Barrier(2)

    def go(pk):
        barrier.wait()
        try:
            oks.append(write_pack(pk, tmp_path))
        except CandidateDigestConflictError as e:
            conflicts.append(e)

    threads = [threading.Thread(target=go, args=(pk,)) for pk in (pk_a, pk_b)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(oks) == 1 and len(conflicts) == 1
    assert [p.name for p in (tmp_path / "p").iterdir()] == ["0.1.0"]


# ── fresh write / staging / idempotency / inventory / empty / compat ─────────

def test_removed_artifact_absent_after_fresh_write(tmp_path):
    write_pack(compile_pack([_dq("dq1"), _md("m1")], name="p", version="0.1.0"), tmp_path)
    d2 = write_pack(compile_pack([_dq("dq1")], name="p", version="0.2.0"), tmp_path)  # m1 removed
    assert {p.name for p in (d2 / "artifacts").glob("*.yaml")} == {"data_quirk__dq1.yaml"}
    assert (tmp_path / "p" / "0.1.0" / "artifacts" / "metric_definition__m1.yaml").is_file()


def test_staging_failure_leaves_target_untouched(tmp_path, monkeypatch):
    from ontowiz_factory import writer  # write_pack calls verify_candidate_dir in writer
    monkeypatch.setattr(writer, "verify_candidate_dir", lambda d: False)
    with pytest.raises(StagedCandidateInvalidError):
        write_pack(compile_pack([_dq("dq1")], name="p", version="0.1.0"), tmp_path)
    assert not (tmp_path / "p" / "0.1.0").exists()
    assert not any((tmp_path / "p").iterdir())  # no orphan staging left behind


def test_recompile_same_digest_idempotent(tmp_path):
    a = write_pack(compile_pack([_dq("dq1")], name="p", version="0.1.0"), tmp_path)
    before = (a / "pack.sig").read_bytes()
    b = write_pack(compile_pack([_dq("dq1")], name="p", version="0.1.0"), tmp_path)
    assert a == b
    assert (b / "pack.sig").read_bytes() == before  # untouched, no rewrite


def test_input_inventory_exact(tmp_path):
    inv = compile_pack([_md("m1"), _dq("dq1")], name="p", version="0.1.0").manifest.input_inventory
    assert [(e.kind, e.id) for e in inv] == [("data_quirk", "dq1"), ("metric_definition", "m1")]
    assert all(len(e.content_digest) == 64 for e in inv)


def test_output_inventory_matches_disk_payload_only(tmp_path):
    d = write_pack(compile_pack([_dq("dq1")], name="p", version="0.1.0"), tmp_path)
    m = PackManifest.model_validate(yaml.safe_load((d / "pack.yaml").read_text(encoding="utf-8")))
    declared = {o.path for o in m.output_inventory}
    on_disk = {p.relative_to(d).as_posix() for p in d.rglob("*") if p.is_file()}
    assert declared == on_disk - {"pack.yaml", "pack.sig"}
    assert "pack.yaml" not in declared and "pack.sig" not in declared
    for o in m.output_inventory:
        assert o.byte_count == len((d / o.path).read_bytes())


def test_empty_candidate_not_releasable(tmp_path):
    pack = compile_pack([], name="p", version="0.1.0")
    assert pack.manifest.releasable is False
    assert pack.manifest.candidate_status == "diagnostic"
    assert verify_candidate_dir(write_pack(pack, tmp_path))


def test_v1_manifest_loads_in_compat_mode():
    m = PackManifest.model_validate({"name": "p", "version": "0.1.0", "artifact_count": 2})
    assert m.manifest_version == 1
    assert m.candidate_digest == ""
    assert m.input_inventory == [] and m.output_inventory == []


def test_absent_manifest_version_loads_as_v1():  # amend-1
    assert PackManifest.model_validate({"name": "p", "version": "0.1.0"}).manifest_version == 1


def test_mutable_metadata_stripped_bytes_unchanged(tmp_path):  # amend-2
    base = write_pack(compile_pack([_dq("dq1")], name="p", version="0.1.0"), tmp_path / "base")
    pk = compile_pack([_dq("dq1")], name="p", version="0.1.0")
    pk.manifest.evals = PackEvalSummary(eval_cases=9, pass_rate=0.5, agent_lift=0.9, gate_passed=True)
    pk.manifest.coverage = 0.77
    pk.manifest.freshness_days = 3
    pk.manifest.compiled_at = "2020-01-01T00:00:00Z"
    dirty = write_pack(pk, tmp_path / "dirty")
    assert (base / "pack.yaml").read_bytes() == (dirty / "pack.yaml").read_bytes()
    text = (dirty / "pack.yaml").read_text(encoding="utf-8")
    for stripped in ("evals", "coverage", "freshness_days", "compiled_at"):
        assert stripped not in text
    assert "candidate_digest" in text and "signed" in text  # kept
    assert PackManifest.model_validate(yaml.safe_load(text)).candidate_digest == pk.manifest.candidate_digest
