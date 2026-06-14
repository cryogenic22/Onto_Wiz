# Gold-Set Regression Framework

Gold-set tests validate that known-good outputs remain stable as the codebase evolves.
They are the "business-question test harness" referenced in the Onto_Wiz vision.

## How It Works

1. **Scenarios** are defined in `scenarios/` as YAML files
2. Each scenario has: input signal, expected reasoning output, confidence bounds
3. `test_gold_set.py` loads all scenarios and validates against the reasoning engine
4. If a scenario fails, it means a code change broke existing semantic reasoning

## Adding a Gold Scenario

Create a YAML file in `tests/gold_set/scenarios/`:

```yaml
id: GOLD-001
name: "Brand launch with competitor safety signal"
description: "Tests that a safety signal during brand launch triggers correct risk classification"

input:
  signal: "competitor_safety_signal"
  context:
    brand: "TestBrand"
    lifecycle_stage: "launch"
    therapeutic_area: "oncology"

expected:
  risk_class: "RESTRICTED"
  min_confidence: 0.7
  must_contain_drivers:
    - "safety"
    - "competitive_positioning"
  must_not_contain_drivers:
    - "pricing"
  guardrail_violations: 0
```

## Running Gold-Set Tests

```bash
# Run only gold-set tests
python -m pytest tests/ -v -m gold_set

# Run all tests including gold-set
python -m pytest tests/ -v
```

## When Gold-Set Tests Fail

A failing gold-set test means **the system's reasoning changed**. This is intentional:

1. If the change is **correct** (new delta improved reasoning): update the scenario expectations
2. If the change is **wrong** (regression): revert the code change and investigate

Never silently update gold-set expectations without understanding why they changed.
