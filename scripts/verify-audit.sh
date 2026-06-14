#!/usr/bin/env bash
# Independent verification audit — the anti-overstatement gate.
#
# Mirrors Content_medical_hub ADR-0001 §2: a task is DONE only when this script
# passes. "Tests pass on my machine in chat" is not done; verify-audit is.
#
# Owned gates (must be green — this is the new code we are accountable for):
#   1. package tests + >=85% coverage on ontowiz-spec / ontowiz-runtime
#   2. ruff clean on our packages
#   3. mypy clean on Tier A source
#   4. Tier A -> Tier B boundary clean (ADR-012)
#   5. Cathedral Keeper: ZERO findings touching packages/
#   6. legacy src/ test suite still green (catches app breakage during re-homes)
#
# Pre-existing src/ quality-gate debt (14 findings) is reported but NOT counted
# against this audit — it predates the monorepo work and is tracked separately
# in docs/PROJECT_STATUS.md.

set -u
cd "$(dirname "$0")/.." || exit 2

FAILS=0
section() { echo ""; echo "── $1 ─────────────────────────────────────────"; }
check() {  # check <label> <exit_code>
  if [ "$2" -eq 0 ]; then echo "  PASS  $1"; else echo "  FAIL  $1"; FAILS=$((FAILS+1)); fi
}

section "1. package tests + coverage (>=85%)"
python -m pytest packages/ -p no:cacheprovider -q \
  --cov=ontowiz_spec --cov=ontowiz_runtime --cov=ontowiz_factory --cov=ontowiz_serve \
  --cov=ontowiz_core.bridge --cov-fail-under=85 >/tmp/va_pkg.txt 2>&1
check "package tests + coverage" $?
tail -3 /tmp/va_pkg.txt | sed 's/^/    /'

section "2. ruff (our packages)"
python -m ruff check packages/ontowiz-spec packages/ontowiz-runtime \
  packages/ontowiz-serve packages/ontowiz-core packages/ontowiz-factory >/tmp/va_ruff.txt 2>&1
check "ruff clean" $?

section "3. mypy (Tier A source)"
python -m mypy packages/ontowiz-spec/ontowiz_spec \
  packages/ontowiz-runtime/ontowiz_runtime --ignore-missing-imports >/tmp/va_mypy.txt 2>&1
check "mypy clean" $?

section "4. Tier A -> Tier B boundary (ADR-012)"
python tools/check_boundaries.py >/tmp/va_bnd.txt 2>&1
check "boundary clean" $?

section "5. Cathedral Keeper — zero NEW findings on packages/"
# Re-homed legacy modules (ontowiz-core) carry pre-existing PRS readability debt,
# faithfully relocated from src/core. They are tracked in docs/PROJECT_STATUS.md
# (debt) with a scheduled pay-down task. CK still scans them (visible in the
# report); this gate counts NEW-code findings only, excluding the named baseline.
INHERITED_DEBT="confidence.py delta_generator.py graph_store.py reasoning_event.py semantic_store.py stores.py"
python cathedral-keeper/ck.py analyze --root . \
  --out-json .quality-reports/cathedral-keeper/report.json >/dev/null 2>&1
PKG_FINDINGS=$(INHERITED_DEBT="$INHERITED_DEBT" python -c "
import json, os
debt = set(os.environ['INHERITED_DEBT'].split())
d = json.load(open('.quality-reports/cathedral-keeper/report.json'))
new = sum(1 for f in d['findings'] for e in (f.get('evidence') or [])
          if 'packages' in e.get('file','') and e['file'].split('/')[-1] not in debt)
print(new)
" 2>/dev/null)
DEBT_FINDINGS=$(INHERITED_DEBT="$INHERITED_DEBT" python -c "
import json, os
debt = set(os.environ['INHERITED_DEBT'].split())
d = json.load(open('.quality-reports/cathedral-keeper/report.json'))
old = sum(1 for f in d['findings'] for e in (f.get('evidence') or [])
          if 'packages' in e.get('file','') and e['file'].split('/')[-1] in debt)
print(old)
" 2>/dev/null)
[ "${PKG_FINDINGS:-1}" = "0" ]; check "CK new-code clean (new: ${PKG_FINDINGS:-?}, tracked legacy debt: ${DEBT_FINDINGS:-?})" $?

section "6. legacy src/ test suite (no app breakage)"
python -m pytest tests/ -p no:cacheprovider -q -m "not slow and not integration and not e2e" \
  >/tmp/va_src.txt 2>&1
check "src tests green" $?
tail -3 /tmp/va_src.txt | sed 's/^/    /'

echo ""
echo "════════════════════════════════════════════════════════"
if [ "$FAILS" -eq 0 ]; then
  echo "VERIFY-AUDIT: PASS — all owned gates green."
  exit 0
else
  echo "VERIFY-AUDIT: FAIL — $FAILS gate(s) red. Not done."
  exit 1
fi
