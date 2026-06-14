"""
Gold-Set Regression Tests for Onto_Wiz Reasoning Engine.

These tests validate that known-good reasoning outputs remain stable
as the codebase evolves. Each scenario in scenarios/ defines an input
signal + context and expected output characteristics.

Usage:
    python -m pytest tests/gold_set/test_gold_set.py -v
    python -m pytest tests/ -v -m gold_set
"""

from pathlib import Path

import pytest
import yaml

from src.reasoning.engine import ReasoningEngine, ScenarioContext

SCENARIOS_DIR = Path(__file__).parent / "scenarios"
ONTOLOGY_PATH = Path("ontology/commercial.yaml")
DATA_PATH = Path("ontology/synthetic_data/compellium_pharma.yaml")


def load_scenarios():
    """Load all gold-set scenario YAML files."""
    scenarios = []
    for filepath in sorted(SCENARIOS_DIR.glob("*.yaml")):
        with open(filepath) as f:
            scenario = yaml.safe_load(f)
            scenario["_file"] = filepath.name
            scenarios.append(scenario)
    return scenarios


def _build_engine():
    """Build a ReasoningEngine from standard ontology files."""
    with open(ONTOLOGY_PATH) as f:
        ontology = yaml.safe_load(f)
    with open(DATA_PATH) as f:
        data = yaml.safe_load(f)
    return ReasoningEngine(ontology, data)


SCENARIOS = load_scenarios()


@pytest.mark.gold_set
@pytest.mark.parametrize(
    "scenario",
    SCENARIOS,
    ids=[s.get("id", s["_file"]) for s in SCENARIOS],
)
def test_gold_scenario(scenario):
    """Validate a gold-set scenario against the reasoning engine."""
    engine = _build_engine()

    inp = scenario["input"]
    context = ScenarioContext(
        account_id=inp.get("context", {}).get("account_id", "test_account"),
        brand_id=inp.get("context", {}).get("brand_id", "test_brand"),
    )

    result = engine.reason(
        question=inp.get("signal", inp.get("question", "")),
        context=context,
    )

    expected = scenario["expected"]

    # Validate confidence bound
    if "min_confidence" in expected:
        assert result.confidence_score >= expected["min_confidence"], (
            f"[{scenario['id']}] Confidence {result.confidence_score} "
            f"below minimum {expected['min_confidence']}"
        )

    # Validate reasoning is not empty
    if expected.get("reasoning_not_empty", False):
        has_content = (
            len(result.identified_risks) > 0
            or len(result.verdict) > 0
        )
        assert has_content, (
            f"[{scenario['id']}] Reasoning output is empty"
        )

    # Validate required tags present in risks or verdict
    if "must_contain_tags" in expected:
        result_text = " ".join(result.identified_risks).lower()
        result_text += " " + result.verdict.lower()
        for tag in expected["must_contain_tags"]:
            assert tag.lower() in result_text, (
                f"[{scenario['id']}] Expected tag '{tag}' "
                f"not found in risks or verdict"
            )
