# Onto_Wiz Anti-Slop Protocol v1.0

> Zero tolerance for hallucinated code, phantom imports, and speculative abstractions.
> Every agent session must internalize this before writing a single line.

---

## Prime Directives

### 1. Context Over Guesswork
- **NEVER** generate code based on assumptions about what exists
- **ALWAYS** read the target file and its imports before modifying
- If you haven't read it, you can't edit it

### 2. No Silent Failures
- **NEVER** write `except: pass` or `catch(e) {}`
- **NEVER** swallow errors — log them, raise them, or handle them explicitly
- If uncertain about an import or API, say so — don't guess

### 3. Refactor, Don't Patch
- Fix root causes, not symptoms
- If a function is too long, extract — don't add comments explaining the mess
- If a pattern is repeated 3x, extract — but not before 3x

### 4. Spec-First Generation
- Write a Micro-Spec before implementation code
- Micro-Specs prevent scope creep and hallucination

---

## 3-Phase Workflow

### Phase 1: DISCOVERY (Before Writing Anything)

```
1. READ all files in the sprint scope (Lead2Dev acceptance criteria)
2. READ imports and dependencies of those files
3. IDENTIFY existing patterns: How does the codebase solve similar problems?
4. IDENTIFY architectural boundaries: What can import what? (see .cathedral-keeper.json)
5. LIST what already exists that you can reuse
```

**Output:** Mental model of current state. No code yet.

### Phase 2: MICRO-SPEC (Before Writing Code)

Write this in your Dev2Lead report or as a code comment:

```
**Proposed Plan:**
1. Files to Touch: [exact list]
2. New Functions/Classes: [names and signatures]
3. Slop Risk: [where hallucination might happen — unfamiliar APIs, complex types]
4. Complexity Score: [Low/Med/High] + justification
5. Reuse Opportunities: [existing code to leverage]
```

**If Complexity is HIGH:** Stop. Report to Lead. Wait for guidance.

### Phase 3: IMPLEMENTATION

Rules:
- **No-Fluff Comments:** Explain WHY, not WHAT. `# Calculate confidence` is slop. `# Decay by half-life to penalize stale evidence` is useful.
- **DRY Enforcement:** Before creating a utility, search for existing ones in `src/core/`
- **Type Everything:** All function signatures get type hints. No `Any` at API boundaries.
- **Error Handling:** Narrow exceptions only. `except KeyError` not `except Exception`.
- **Test Immediately:** Write the test before or alongside the implementation, not after.

---

## Onto_Wiz-Specific Rules

### Domain Model Integrity
- The **Delta Model** is sacred. Everything is a proposal. Don't bypass it.
- New data that enters the system MUST go through a Delta — no direct graph mutations.
- `JudgmentType` determines governance flow. Respect the enum; don't add values without Lead approval.

### Ontology Safety
- YAML ontology files (`ontology/`) are the source of truth for domain knowledge
- Never generate synthetic ontology entries in production code
- Synthetic data lives ONLY in `ontology/synthetic_data/`

### Evidence-First
- Every assertion in the system must link to evidence
- If you create a new data structure, it needs an `evidence_ids: List[str]` field or equivalent
- Confidence scores without evidence sources are meaningless — don't generate them

### Architectural Boundaries (Enforced by Cathedral Keeper)
```
src/core/    →  MUST NOT import from  →  src/api/
src/reasoning/ →  MUST NOT import from  →  src/api/
src/api/     →  CAN import from       →  src/core/, src/reasoning/
tests/       →  CAN import from       →  anything in src/
```

---

## Verification Checklist

Before marking any sprint DONE, verify:

| Check | How |
|-------|-----|
| **Hallucination Check** | Did I invent any library function that doesn't exist? |
| **Import Audit** | Are all imports used? Do all imports resolve? |
| **Type Safety** | No `Any` types at function boundaries? |
| **Security** | No hardcoded credentials, API keys, or secrets? |
| **Test Coverage** | Every new public function has at least 1 test? |
| **Existing Tests** | `python -m pytest tests/ -v` still passes? |
| **Quality Gate** | `python quality-gate/quality_gate.py` passes? |
| **Cathedral Keeper** | `python cathedral-keeper/ck.py analyze --root .` — no new HIGH findings? |
| **Scope** | Did I ONLY touch files listed in the sprint scope? |
| **Delta Model** | Any new data path goes through a Delta proposal? |

---

## Red Flags (Stop and Escalate)

- You're about to create a file not in the sprint scope
- You need to modify `models.py` enum values
- You're writing more than 50 lines without a test
- Confidence in your approach is below 70%
- You're copy-pasting more than 10 lines from another file
- You want to add a new dependency (pip install / npm install)

---

_This protocol is enforced. Violations are caught by quality-gate and Cathedral Keeper._
_When in doubt, ask the Lead._
