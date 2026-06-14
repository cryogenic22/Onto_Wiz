"""Live agent-lift benchmark for a compiled Domain Pack (Tier B).

Measures the headline number — does the pack make a real agent *better*? — the
honest way: the with-pack path runs the genuine CTX LLM-as-router loop the
product ships (an L3 directory in the system prompt → the model calls
``ctx_hydrate`` → the pack's L2 section body comes back → the model answers).
The blind path asks the same question with no pack and no tools. Per-case scores
come from the shared deterministic judge in :mod:`ontowiz_factory.evals`; the
lift is their mean delta.

The LLM client is provider-neutral (:class:`ChatAgent`); the live
:class:`AnthropicChatAgent` is the only networked code and is excluded from
coverage — every offline path is exercised by a fake agent in the tests.

Tier B (factory). It may import Tier A (runtime/spec/ctx); Tier A never imports it.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import yaml
from ontowiz_ctx.core.hydrator import hydrate_by_name
from ontowiz_ctx.core.model import CTXDocument
from ontowiz_ctx.core.serializer import serialize_section
from ontowiz_runtime.context import ContextResult, context_for_pack
from ontowiz_runtime.registry import LoadedPack
from ontowiz_spec import EvalCase, PackEvalSummary, PackManifest

from .commercial_eval_suite import COMMERCIAL_EVAL_CASES
from .compiler import reseal_pack
from .evals import EvalSummary, agent_lift, gate, run_suite

# Mid-tier model by default: lift is more visible below the capability ceiling,
# and it keeps a full benchmark cheap. Override per run.
DEFAULT_MODEL = "claude-haiku-4-5-20251001"

# An Anthropic tool name must match ^[a-zA-Z0-9_-]{1,64}$, so the CTX verb
# "ctx/hydrate" is exposed to the model as "ctx_hydrate".
HYDRATE_TOOL: dict[str, Any] = {
    "name": "ctx_hydrate",
    "description": (
        "Retrieve the full detail of one or more sections listed in the domain "
        "knowledge directory. Pass the section name(s) exactly as shown, comma-separated."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "section": {
                "type": "string",
                "description": "Section name(s) to retrieve, comma-separated.",
            }
        },
        "required": ["section"],
    },
}

ToolHandler = Callable[[str, dict[str, Any]], str]


class ChatAgent(Protocol):
    """A provider-neutral agent that runs one user turn (with any tool calls) to
    completion and returns the final text.

    Generalised from the legacy OpenAI ``LLMService`` in
    ``src/knowledge/extraction/llm_service.py`` so the with-pack path can hand the
    model a ``ctx_hydrate`` tool and let it route. Implementations own their retry.
    """

    def run(
        self,
        *,
        system: str,
        user: str,
        tools: list[dict[str, Any]] | None = None,
        tool_handler: ToolHandler | None = None,
        max_tokens: int = 1024,
    ) -> str: ...


# ── the CTX hydration tool, backed by the pack's L2 doc ──


def _parse_section_names(args: dict[str, Any]) -> list[str]:
    raw = args.get("section") or args.get("sections") or ""
    if isinstance(raw, list):
        return [str(s).strip() for s in raw if str(s).strip()]
    return [s.strip() for s in str(raw).split(",") if s.strip()]


def make_hydrate_handler(doc: CTXDocument) -> ToolHandler:
    """Build a ``ctx_hydrate`` handler that serves section bodies from one L2 doc."""

    def handler(_name: str, args: dict[str, Any]) -> str:
        result = hydrate_by_name(doc, _parse_section_names(args), include_header=False)
        if not result.sections:
            return "No matching sections."
        return "\n\n".join("\n".join(serialize_section(s)) for s in result.sections)

    return handler


# ── the two answer paths the lift compares ──

_ANALYST = (
    "You are a senior commercial-pharma analyst. Give a concise root-cause "
    "diagnosis of the situation described, naming the specific driver."
)
_WITH_PACK = (
    _ANALYST
    + " A governed domain knowledge base is available: read the directory below and "
    "call ctx_hydrate(section=...) to retrieve any heuristic you need before answering."
)


def answer_with_pack(
    query: str,
    pack: LoadedPack,
    agent: ChatAgent,
    *,
    agent_type: str = "commercial_analyst",
) -> tuple[str, ContextResult]:
    """Answer a free query with the governed pack wired in via the CTX router loop.

    Returns the answer plus the ContextResult (trust envelope + eligible set) so a
    consumer can surface provenance. This is the single with-pack code path that
    both the benchmark and the live consumer (``consume.consult``) share.
    """
    ctx = context_for_pack(query, pack, agent_type=agent_type)
    system = f"{_WITH_PACK}\n\n{ctx.system_prompt}"
    answer = agent.run(
        system=system,
        user=query,
        tools=[HYDRATE_TOOL],
        tool_handler=make_hydrate_handler(pack.l2_doc),
    )
    return answer, ctx


def with_pack_answer(
    case: EvalCase,
    pack: LoadedPack,
    agent: ChatAgent,
    *,
    agent_type: str = "commercial_analyst",
) -> str:
    """Answer with the governed pack wired in via the real CTX router loop."""
    answer, _ = answer_with_pack(case.question, pack, agent, agent_type=agent_type)
    return answer


def without_pack_answer(case: EvalCase, agent: ChatAgent) -> str:
    """Answer the same question blind — no pack, no tools (the baseline)."""
    return agent.run(system=_ANALYST, user=case.question)


# ── the benchmark ──


@dataclass
class BenchmarkReport:
    """The verdict of one benchmark run over a pack."""

    pack: str
    model: str
    n_cases: int
    with_pack: EvalSummary
    without_pack: EvalSummary
    agent_lift: float
    gate_passed: bool


def _memoize(fn: Callable[[EvalCase], str]) -> Callable[[EvalCase], str]:
    """Cache answers by case id so each (case, condition) hits the LLM once;
    ``run_suite`` and ``agent_lift`` then reuse the same answers for free."""
    cache: dict[str, str] = {}

    def wrapped(case: EvalCase) -> str:
        if case.id not in cache:
            cache[case.id] = fn(case)
        return cache[case.id]

    return wrapped


def run_lift_benchmark(
    pack: LoadedPack,
    agent: ChatAgent,
    cases: list[EvalCase] | None = None,
    *,
    agent_type: str = "commercial_analyst",
    model: str = DEFAULT_MODEL,
    min_pass_rate: float = 0.8,
    min_lift: float = 0.05,
) -> BenchmarkReport:
    """Run the suite with-pack and blind, returning pass-rates, lift and verdict."""
    cases = cases if cases is not None else COMMERCIAL_EVAL_CASES
    with_fn = _memoize(lambda c: with_pack_answer(c, pack, agent, agent_type=agent_type))
    without_fn = _memoize(lambda c: without_pack_answer(c, agent))

    with_summary = run_suite(cases, with_fn)
    without_summary = run_suite(cases, without_fn)
    lift = agent_lift(cases, with_fn, without_fn)  # reuses the cached answers
    passed = gate(with_summary, min_pass_rate=min_pass_rate, lift=lift, min_lift=min_lift)

    return BenchmarkReport(
        pack=f"{pack.manifest.name}@{pack.manifest.version}",
        model=model,
        n_cases=len(cases),
        with_pack=with_summary,
        without_pack=without_summary,
        agent_lift=lift,
        gate_passed=passed,
    )


def write_results_to_manifest(
    pack_dir: str | Path, report: BenchmarkReport, *, run_at: str
) -> PackManifest:
    """Persist the eval verdict into ``<pack_dir>/pack.yaml`` (the evals block)."""
    path = Path(pack_dir) / "pack.yaml"
    manifest = PackManifest.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    manifest.evals = PackEvalSummary(
        eval_cases=report.n_cases,
        pass_rate=report.with_pack.pass_rate,
        agent_lift=report.agent_lift,
        last_run_at=run_at,
        gate_passed=report.gate_passed,
    )
    path.write_text(yaml.safe_dump(manifest.model_dump(), sort_keys=False), encoding="utf-8")
    # a manifest edit changes the pack bytes — re-seal so the integrity seal
    # (pack.sig) stays valid for an already-signed pack instead of going stale
    if (Path(pack_dir) / "pack.sig").is_file():
        reseal_pack(pack_dir)
    return manifest


# ── the live Anthropic agent (the only networked, un-covered code) ──


class AnthropicChatAgent:
    """A live :class:`ChatAgent` backed by the Anthropic Messages API + tool loop."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        *,
        api_key: str | None = None,
        max_turns: int = 5,
        temperature: float = 0.0,
    ) -> None:
        self.model = model
        self.max_turns = max_turns
        # 0.0 by default: greedy decoding makes the blind baseline reproducible,
        # so the measured lift reflects the pack, not run-to-run sampling noise.
        self.temperature = temperature
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")

    def run(  # pragma: no cover - networked
        self,
        *,
        system: str,
        user: str,
        tools: list[dict[str, Any]] | None = None,
        tool_handler: ToolHandler | None = None,
        max_tokens: int = 1024,
    ) -> str:
        from anthropic import Anthropic

        client = Anthropic(api_key=self._api_key or None)
        messages: list[dict[str, Any]] = [{"role": "user", "content": user}]
        resp: Any = None
        for _ in range(self.max_turns):
            resp = client.messages.create(
                model=self.model,
                system=system,
                messages=messages,
                tools=tools or [],
                max_tokens=max_tokens,
                temperature=self.temperature,
            )
            if resp.stop_reason != "tool_use" or tool_handler is None:
                return _text_of(resp)
            messages.append({"role": "assistant", "content": resp.content})
            messages.append({"role": "user", "content": _run_tools(resp, tool_handler)})
        return _text_of(resp)


def _text_of(resp: Any) -> str:  # pragma: no cover - networked
    parts = [b.text for b in resp.content if getattr(b, "type", "") == "text"]
    return "".join(parts).strip()


def _run_tools(resp: Any, tool_handler: ToolHandler) -> list[dict[str, Any]]:  # pragma: no cover
    results: list[dict[str, Any]] = []
    for block in resp.content:
        if getattr(block, "type", "") == "tool_use":
            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": tool_handler(block.name, dict(block.input)),
                }
            )
    return results
