"""Loop 4 (live) — agent-lift benchmark harness tests.

Proves the *faithful* benchmark: the with-pack path runs the real CTX
LLM-as-router loop (directory → ctx_hydrate tool-call → section body → answer),
the lift is computed from the shared evals scorer, and the verdict is written
back into the pack manifest. The live LLM is stood in for by a FakeChatAgent so
the gates run offline; the only un-covered code is the network call itself.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import yaml
from ontowiz_ctx.core.hydrator import list_sections
from ontowiz_factory.benchmark import (
    HYDRATE_TOOL,
    BenchmarkReport,
    make_hydrate_handler,
    run_lift_benchmark,
    with_pack_answer,
    without_pack_answer,
    write_results_to_manifest,
)
from ontowiz_factory.commercial_eval_suite import COMMERCIAL_EVAL_CASES
from ontowiz_runtime.registry import load_pack
from ontowiz_spec import EvalCase, PackEvalSummary, PackManifest

PACK_DIR = Path(__file__).resolve().parents[3] / "packs" / "commercial_analytics" / "0.1.0"


class FakeChatAgent:
    """Stand-in for a live LLM. With tools it exercises the hydrate loop then
    returns the 'with-pack' answer; without tools it returns the 'blind' answer."""

    def __init__(self, with_by_q: dict[str, str], without_by_q: dict[str, str]) -> None:
        self.with_by_q = with_by_q
        self.without_by_q = without_by_q
        self.hydrations: list[str] = []

    def run(self, *, system, user, tools=None, tool_handler=None, max_tokens=1024):  # noqa: ANN001
        assert system  # a system prompt is always supplied
        if tools and tool_handler is not None:
            # the agent is the router: it must reach the directory + the tool
            assert any(t["name"] == "ctx_hydrate" for t in tools)
            self.hydrations.append(tool_handler("ctx_hydrate", {"section": "ALL"}))
            return self.with_by_q[user]
        return self.without_by_q[user]


def _two_cases() -> list[EvalCase]:
    return [
        EvalCase(id="b_safety", name="safety", question="Volume fell as safety inquiries rose. Why?",
                 must_contain=["safety"], must_not_contain=["pricing"]),
        EvalCase(id="b_supply", name="supply", question="Units fell 30% with a plant outage. Why?",
                 must_contain=["supply"]),
    ]


def _fake_that_helps(cases: list[EvalCase]) -> FakeChatAgent:
    # with-pack answers carry the governed term; blind answers miss it
    with_by_q = {c.question: f"Root cause: {c.must_contain[0]} driven." for c in cases}
    without_by_q = {c.question: "Root cause: generic market softness." for c in cases}
    return FakeChatAgent(with_by_q, without_by_q)


def test_hydrate_tool_has_valid_anthropic_shape():
    assert HYDRATE_TOOL["name"] == "ctx_hydrate"  # '/' is illegal in a tool name
    assert "input_schema" in HYDRATE_TOOL
    assert "section" in HYDRATE_TOOL["input_schema"]["properties"]


def test_hydrate_handler_returns_section_body_for_real_pack():
    pack = load_pack(PACK_DIR)
    handler = make_hydrate_handler(pack.l2_doc)
    name = list_sections(pack.l2_doc)[0]["name"]
    body = handler("ctx_hydrate", {"section": name})
    assert body and body != "No matching sections."
    assert handler("ctx_hydrate", {"section": "DOES-NOT-EXIST"}) == "No matching sections."


def test_with_and_without_answer_paths_differ_in_tooling():
    pack = load_pack(PACK_DIR)
    cases = _two_cases()
    agent = _fake_that_helps(cases)
    w = with_pack_answer(cases[0], pack, agent, agent_type="commercial_analyst")
    wo = without_pack_answer(cases[0], agent)
    assert "safety" in w.lower()
    assert "safety" not in wo.lower()
    assert agent.hydrations  # the with-pack path actually invoked the router/tool


def test_run_lift_benchmark_computes_positive_lift_and_gates():
    pack = load_pack(PACK_DIR)
    cases = _two_cases()
    agent = _fake_that_helps(cases)
    report = run_lift_benchmark(pack, agent, cases, min_lift=0.05)
    assert isinstance(report, BenchmarkReport)
    assert report.n_cases == 2
    assert report.with_pack.pass_rate == 1.0
    assert report.without_pack.pass_rate == 0.0
    assert report.agent_lift > 0
    assert report.gate_passed is True


def test_benchmark_with_no_lift_does_not_pass_the_gate():
    pack = load_pack(PACK_DIR)
    cases = _two_cases()
    # an agent that answers identically with or without the pack adds no lift
    same = {c.question: f"{c.must_contain[0]} present" for c in cases}
    agent = FakeChatAgent(same, dict(same))
    report = run_lift_benchmark(pack, agent, cases, min_lift=0.05)
    assert report.agent_lift == 0.0
    assert report.gate_passed is False  # passes evals but adds no lift → blocked


def test_write_results_to_manifest(tmp_path):
    # work on a throwaway copy so the shipped pack.yaml is untouched
    src = PackManifest.model_validate(yaml.safe_load((PACK_DIR / "pack.yaml").read_text()))
    (tmp_path / "pack.yaml").write_text(yaml.safe_dump(src.model_dump(), sort_keys=False))

    pack = load_pack(PACK_DIR)
    cases = _two_cases()
    report = run_lift_benchmark(pack, _fake_that_helps(cases), cases, min_lift=0.05)
    written = write_results_to_manifest(tmp_path, report, run_at="2026-06-11T12:00:00")

    assert isinstance(written.evals, PackEvalSummary)
    reloaded = PackManifest.model_validate(yaml.safe_load((tmp_path / "pack.yaml").read_text()))
    assert reloaded.evals.agent_lift == report.agent_lift
    assert reloaded.evals.eval_cases == 2
    assert reloaded.evals.gate_passed is True
    assert reloaded.evals.last_run_at == "2026-06-11T12:00:00"


def test_write_results_reseals_signed_pack(tmp_path):
    # writing eval results into a SIGNED pack must not leave the integrity seal stale
    from ontowiz_factory.compiler import verify_pack

    dest = tmp_path / "0.1.0"
    shutil.copytree(PACK_DIR, dest)
    assert verify_pack(dest)  # the copy starts valid

    pack = load_pack(dest)
    cases = _two_cases()
    report = run_lift_benchmark(pack, _fake_that_helps(cases), cases, min_lift=0.05)
    write_results_to_manifest(dest, report, run_at="2026-06-11T12:00:00")

    assert verify_pack(dest)  # re-sealed → still valid after the governed edit


def test_commercial_eval_suite_is_grounded_and_well_formed():
    cases = COMMERCIAL_EVAL_CASES
    assert len(cases) >= 24  # the larger suite
    ids = [c.id for c in cases]
    assert len(ids) == len(set(ids))  # unique ids
    assert all(c.must_contain for c in cases)  # every case asserts something
    assert all(c.question.strip() for c in cases)


def test_suite_does_not_hand_the_answer_token_to_the_model():
    # hardness invariant: the required governed term must NOT appear verbatim in
    # the question, so the model must supply it from knowledge/the pack, not echo.
    for c in COMMERCIAL_EVAL_CASES:
        q = c.question.lower()
        for token in c.must_contain:
            assert token.lower() not in q, f"{c.id}: question leaks token '{token}'"
