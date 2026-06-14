#!/usr/bin/env python
"""Drive the full living loop end to end, live — the MVP coming to life.

    consult v0.1.0 (gap) -> SME Forge mission -> evolve_pack -> v0.2.0
        -> re-consult v0.2.0 (now answered) -> registry lists both versions

A real agent (live Anthropic) consumes the pack via the CTX router loop; a gap it
can't ground becomes a governed addition that ships in the next pack version,
which then serves the previously-missing knowledge. Writes packs/commercial_analytics/0.2.0/.

    python scripts/run_living_loop.py        (reads ANTHROPIC_API_KEY from env or ./.env)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Live model answers can contain non-cp1252 characters (arrows, dashes); make the
# console UTF-8 so printing them never crashes the demo on Windows.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ontowiz_runtime.registry import PackRegistry, load_pack
from ontowiz_spec import DecisionHeuristic, Tag, TagDimension

from ontowiz_factory.benchmark import AnthropicChatAgent
from ontowiz_factory.compiler import verify_pack, write_pack
from ontowiz_factory.consume import consult
from ontowiz_factory.missions import MissionSubmission, submit_mission
from ontowiz_factory.orchestrate import evolve_pack

REPO = Path(__file__).resolve().parents[1]
PACKS = REPO / "packs"
NAME = "commercial_analytics"
GAP_QUERY = "Our brand's volume collapsed after a cyberattack took the distributor's systems offline. Root cause?"


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def _show(label, c) -> None:  # noqa: ANN001 - operator script
    used = ", ".join(c.trust.artifacts_used[:3]) or "(none)"
    print(f"\n[{label}] helpful={c.usage.helpful}  top_artifacts=[{used}]  "
          f"confidence={c.trust.confidence}")
    print("  answer:", " ".join(c.answer.split())[:240])


def _new_cyber_heuristic() -> DecisionHeuristic:
    return DecisionHeuristic(
        id="rule_cyber_disruption",
        name="Cyber Disruption",
        decision_logic="cyberattack on distributor IT => fulfillment outage => volume drop",
        typical_outcome="Cyberattack-driven distribution outage: an IT incident at the "
        "distributor halted fulfillment — a supply-side outage, not demand or access.",
        trigger_context=["A cyber/IT incident at a distributor can masquerade as a demand drop."],
        confidence=0.85,
        tags=[Tag(dimension=TagDimension.ANALYTICS_DOMAIN, value="commercial")],
    )


def main() -> int:
    _load_dotenv(REPO / ".env")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set (env or .env).")
        return 2
    agent = AnthropicChatAgent()

    print("=" * 64)
    print("STEP 1 — consult v0.1.0 on a gap the pack does not cover")
    v1 = load_pack(PACKS / NAME / "0.1.0")
    c1 = consult(GAP_QUERY, v1, agent)
    _show("v0.1.0", c1)
    print(f"  (v0.1.0 has rule_cyber_disruption: "
          f"{any(a.id == 'rule_cyber_disruption' for a in v1.artifacts)})")

    print("\n" + "=" * 64)
    print("STEP 2 — an SME files a Forge mission to fill the gap")
    result = submit_mission(MissionSubmission(
        mission_type="add", artifact=_new_cyber_heuristic(), confidence=0.85,
        gold_answer="cyberattack distribution outage", question=GAP_QUERY, submitted_by="sme",
    ))
    print(f"  governed delta op={result.delta.content.get('op')}  "
          f"eval_case={result.eval_case.id}  confidence={result.confidence}")

    print("\n" + "=" * 64)
    print("STEP 3 — evolve the pack: govern the addition into v0.2.0")
    evolved = evolve_pack(v1.artifacts, [result.delta], name=NAME, version="0.2.0")
    write_pack(evolved, PACKS)
    v2_dir = PACKS / NAME / "0.2.0"
    print(f"  wrote {v2_dir}  artifacts={len(evolved.artifacts)} (was {len(v1.artifacts)})  "
          f"sealed={verify_pack(v2_dir)}")

    print("\n" + "=" * 64)
    print("STEP 4 — re-consult v0.2.0 on the same query")
    v2 = load_pack(v2_dir)
    c2 = consult(GAP_QUERY, v2, agent)
    _show("v0.2.0", c2)
    print(f"  (v0.2.0 now serves rule_cyber_disruption: "
          f"{'rule_cyber_disruption' in {a.id for a in c2_eligible(v2)}})")

    print("\n" + "=" * 64)
    print("STEP 5 — registry now offers both versions")
    for m in PackRegistry(PACKS).list_manifests():
        print(f"  {m.name}@{m.version}  artifacts={m.artifact_count}  "
              f"agent_lift={m.evals.agent_lift}")
    return 0


def c2_eligible(pack):  # noqa: ANN001 - operator script
    from ontowiz_runtime.context import context_for_pack
    return context_for_pack(GAP_QUERY, pack).eligible


if __name__ == "__main__":
    raise SystemExit(main())
