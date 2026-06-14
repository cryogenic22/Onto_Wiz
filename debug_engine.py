import yaml
from pathlib import Path
from src.reasoning.engine import ReasoningEngine, ScenarioContext

DATA_PATH = Path("ontology/synthetic_data/compellium_pharma.yaml")
ONTOLOGY_PATH = Path("ontology/commercial.yaml")

print("--- DEBUG SCRIPT START ---")

# 1. Load Data
with open(DATA_PATH, "r") as f:
    data = yaml.safe_load(f)
print(f"Loaded Data ID: {data.get('company', {}).get('id')}")

market_context = data.get("market_context", {})
signals = market_context.get("dark_data_signals", [])
print(f"Total Signals in YAML: {len(signals)}")
for i, s in enumerate(signals):
    print(f"Signal {i}: Account={s.get('account_id')} Tags={s.get('tags')}")

# 2. Init Engine
with open(ONTOLOGY_PATH, "r") as f:
    ontology = yaml.safe_load(f)
engine = ReasoningEngine(ontology, data)

# 3. Content
context = ScenarioContext(account_id="st_mary_hospital", brand_id="brand_oncovance")
print(f"\nRunning Reason for {context.account_id}...")
response = engine.reason("Debug Question", context)

print(f"Verdict: {response.verdict}")
print(f"Score: {response.confidence_score}")
print(f"Risks: {response.identified_risks}")
print("--- DEBUG SCRIPT END ---")
