# Security Review Report (SEN-006)

> **Owner:** Team SENTINEL
> **Date:** 2026-02-01
> **Framework:** OWASP Top 10 (2021)
> **Scope:** `src/api/server.py`, `src/api/schemas.py`, `src/core/`, `src/reasoning/`, `frontend/`
> **DEC-011 Compliance:** Review-only. No source code modifications.

---

## Executive Summary

**Verdict: PASS_WITH_FINDINGS (7 findings: 2 HIGH, 3 MEDIUM, 2 LOW)**

The application has strong input validation at the API boundary (Pydantic models, enum constraints, bounded floats). However, the system has **no authentication or authorization**, a **fully permissive CORS policy**, **no rate limiting**, and **unbounded list fields** on several endpoints. These are expected for the current in-memory development phase but must be addressed before any deployment.

No injection vulnerabilities, SSRF, or command injection vectors were identified. The codebase uses `yaml.safe_load()` correctly and does not execute user-supplied strings.

---

## Findings Summary

| # | OWASP Category | Severity | Finding | Location |
|---|---|---|---|---|
| F-001 | A01: Broken Access Control | **HIGH** | No authentication or authorization on any endpoint | `server.py` (all endpoints) |
| F-002 | A05: Security Misconfiguration | **HIGH** | CORS allows all origins with credentials | `server.py:60-66` |
| F-003 | A01: Broken Access Control | MEDIUM | No object-level access control on approve/reject | `server.py:226-246` |
| F-004 | A05: Security Misconfiguration | MEDIUM | No rate limiting on any endpoint | `server.py` (all endpoints) |
| F-005 | A04: Insecure Design | MEDIUM | Unbounded list fields in request schemas | `schemas.py` (multiple) |
| F-006 | A09: Logging & Monitoring | LOW | No security event logging | `server.py`, `stores.py` |
| F-007 | A05: Security Misconfiguration | LOW | Missing security headers | `server.py` |

---

## Detailed Findings

### F-001: No Authentication or Authorization [HIGH]

**OWASP:** A01:2021 — Broken Access Control
**Location:** `src/api/server.py` — all 18 endpoints
**Severity:** HIGH

**Description:**
No endpoint requires authentication. Any client can:
- Create, approve, reject, and promote deltas (full write access to the knowledge graph)
- Create and approve patterns and guardrails (governance bypass)
- Access all session data and audit logs
- Invoke the reasoning engine

The `reviewer` field in `DeltaApprove` and `DeltaReject` is a self-declared string — there is no verification that the reviewer has authority.

**Evidence:**
```python
# server.py:226 — anyone can approve any delta
@app.post("/deltas/{delta_id}/approve", ...)
def approve_delta(delta_id: str, request: DeltaApprove):
    delta = delta_store.approve(delta_id, request.reviewer)  # reviewer is self-declared
```

```python
# server.py:289 — approver is a query parameter, no auth check
@app.post("/patterns/{pattern_id}/approve", ...)
def approve_pattern(pattern_id: str, approver: str = Query(...)):
```

**Impact:** Complete bypass of the governance model (DEC-001). Any client can approve their own proposals, defeating the Delta Model audit trail.

**Recommendation:** Ticket LENS-008 (RBAC Middleware + Auth Endpoints, Sprint 16) addresses this. Consider pulling it forward given it's the #1 OWASP risk. At minimum, add a shared API key for pre-production deployments.

---

### F-002: CORS Allows All Origins with Credentials [HIGH]

**OWASP:** A05:2021 — Security Misconfiguration
**Location:** `src/api/server.py:60-66`
**Severity:** HIGH

**Description:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

The combination of `allow_origins=["*"]` with `allow_credentials=True` is explicitly prohibited by the CORS specification (browsers will reject it). More critically, `allow_origins=["*"]` means any website can make API calls to this server. If the API is ever exposed on a network (not just localhost), any malicious page a user visits can silently call the API.

**Impact:** Cross-origin request forgery from any origin. Combined with F-001 (no auth), any website can modify the knowledge graph.

**Recommendation:** Restrict `allow_origins` to the Next.js frontend origin (e.g., `["http://localhost:3000"]` for development). Remove `allow_credentials=True` until authentication is implemented.

---

### F-003: No Object-Level Access Control [MEDIUM]

**OWASP:** A01:2021 — Broken Access Control
**Location:** `src/api/server.py:226-246`, `server.py:288-294`, `server.py:324-330`
**Severity:** MEDIUM

**Description:**
Approval and rejection endpoints accept any delta/pattern/guardrail ID without checking:
- Whether the caller has the role required by `delta.assigned_to` (e.g., `domain_expert` vs `governance_board`)
- Whether the caller is the assigned reviewer
- Whether the artifact's routing decision permits this approver

The HITL routing logic (CTX-006) correctly assigns deltas to queues and roles, but the API layer does not enforce these assignments.

**Evidence:**
```python
# A delta routed to governance_board can be approved by anyone calling themselves "intern"
delta_store.approve(delta_id, "intern")  # No role check
```

**Impact:** The routing matrix (CTX-006) is advisory only — it has no enforcement at the API boundary.

**Recommendation:** LENS-004 (HITL Endpoints) should enforce `delta.assigned_to == caller.role` before allowing approval. This requires auth (F-001) to be meaningful.

---

### F-004: No Rate Limiting [MEDIUM]

**OWASP:** A05:2021 — Security Misconfiguration
**Location:** All endpoints
**Severity:** MEDIUM

**Description:**
No rate limiting middleware is configured. The in-memory stores make every operation sub-millisecond, so a malicious client can:
- Create thousands of deltas per second (store exhaustion)
- Trigger thousands of intelligence packet generations
- Fill the audit log unboundedly

The `list_deltas` endpoint has `limit=Query(default=50, le=100)` which is good, but `list_sessions`, `list_patterns`, and `list_guardrails` have no pagination limits at all.

**Evidence:**
```python
# server.py:541 — returns ALL sessions, no limit
@app.get("/sessions", response_model=List[GameSessionSummary], tags=["Sessions"])
def list_sessions():
    return [... for e in reasoning_event_store.list_all()]  # unbounded
```

**Impact:** Denial of service via memory exhaustion. Also enables automated spamming of the review queue.

**Recommendation:** Add pagination to all list endpoints (consistent with `list_deltas` pattern). Consider rate limiting middleware for Phase 5+ when network exposure increases.

---

### F-005: Unbounded List Fields in Request Schemas [MEDIUM]

**OWASP:** A04:2021 — Insecure Design
**Location:** `src/api/schemas.py`
**Severity:** MEDIUM

**Description:**
Several request models accept lists with no maximum length:

| Schema | Field | Constraint |
|---|---|---|
| `DeltaCreate` | `evidence_pointers: List[str]` | No max length |
| `JudgmentPatternCreate` | `applies_when_signals: List[str]` | No max length |
| `JudgmentPatternCreate` | `typical_drivers: List[DriverAttributionAPI]` | No max length |
| `GuardrailCreate` | `blocks_action_types: List[str]` | No max length |
| `GuardrailCreate` | `blocks_drivers: List[str]` | No max length |
| `GameSessionCreate` | `signals: List[SignalInput]` | No max length |
| `GameSessionCreate` | `mistakes: List[MistakeInput]` | No max length |
| `GameSessionCreate` | `actions: List[ActionInput]` | No max length |
| `IntelligencePacketRequest` | `context: Dict[str, Any]` | Unbounded dict |

A client can send a request with 1 million items in any of these lists, causing memory exhaustion.

Additionally, `DeltaCreate.content: Dict[str, Any]` accepts arbitrary nested JSON with no depth or size limit.

**Impact:** Memory exhaustion, processing delays. The `find_matching_patterns()` and `find_conflicts()` operations scale linearly with store size, so injecting large numbers of patterns can degrade performance.

**Recommendation:** Add `max_items` constraints to Pydantic `Field()` for all list fields. Add a max body size limit via middleware. Suggested limits: signals ≤ 20, drivers ≤ 10, evidence_pointers ≤ 50, content dict depth ≤ 3.

---

### F-006: No Security Event Logging [LOW]

**OWASP:** A09:2021 — Security Logging and Monitoring Failures
**Location:** `src/api/server.py`, `src/core/stores.py`
**Severity:** LOW

**Description:**
The `_log_audit()` method in stores tracks operational events (propose, approve, reject, escalate) but does not log:
- Failed authentication attempts (N/A currently, but the hook doesn't exist)
- Requests to non-existent resources (404s are returned but not logged)
- Approval of high-risk deltas (NORMATIVE judgment type)
- Escalation events with context

The audit log is also in-memory and lost on restart.

**Impact:** No forensic trail for security incidents. Acceptable for current phase (DEC-005: in-memory until Phase 6) but must be addressed with persistent storage.

**Recommendation:** When LENS-008 (auth) is implemented, add structured security event logging. When CTX-012 (Postgres) ships, persist the audit log.

---

### F-007: Missing Security Headers [LOW]

**OWASP:** A05:2021 — Security Misconfiguration
**Location:** `src/api/server.py`
**Severity:** LOW

**Description:**
The FastAPI application does not set standard security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Strict-Transport-Security` (HSTS)
- `Content-Security-Policy`
- `Referrer-Policy`

These headers prevent common browser-based attacks (MIME sniffing, clickjacking, downgrade attacks).

**Impact:** Low — the API is not directly rendered in browsers. The frontend (Next.js) would need its own header configuration. But the API should still set them for defense-in-depth.

**Recommendation:** Add a simple middleware to set security headers. This is a small task (S) that could be bundled with LENS-008 or done as a standalone ticket.

---

## Clean Areas (No Findings)

### A03:2021 — Injection: PASS

- **YAML parsing:** Uses `yaml.safe_load()` exclusively (`server.py:80-82`). No `yaml.load()` or `yaml.unsafe_load()`.
- **No SQL/ORM:** All stores are in-memory Python dicts. No SQL queries constructed.
- **No eval/exec:** No `eval()`, `exec()`, `os.system()`, or `subprocess` calls anywhere in `src/`.
- **No template rendering:** API returns JSON only via Pydantic serialization. No server-side HTML rendering.
- **Pydantic validation:** All request bodies are validated through Pydantic models with typed fields before reaching business logic.

### A10:2021 — SSRF: PASS

- No endpoint accepts URLs or fetches external resources.
- File paths are hardcoded constants (`DATA_PATH`, `ONTOLOGY_PATH`) — not derived from user input.
- The `open()` calls in `server.py:79-82` use static `Path` objects, not user-supplied strings.

### A08:2021 — Software and Data Integrity: PASS

- No deserialization of untrusted data (no pickle, no marshal).
- YAML files are loaded at startup from known paths only.
- Delta `content` field is `Dict[str, Any]` but is only stored and serialized — never executed or interpreted as code.

### A02:2021 — Cryptographic Failures: N/A

- No passwords, tokens, or secrets stored in the codebase.
- No PII in the data model (SME IDs are explicitly "anonymized" per `reasoning_event.py:261`).
- No cryptographic operations performed.

### A06:2021 — Vulnerable Components: DEFERRED

- Dependency vulnerability scanning is SEN-010 scope (Sprint 10).
- Current stack: FastAPI 0.x, Pydantic 2.x, PyYAML, uvicorn. No known critical CVEs in these packages as of 2026-02-01, but automated scanning should verify.

---

## Recommended Remediation Tickets

| Priority | Ticket | Description | Addresses |
|---|---|---|---|
| P0 | LENS-008 (exists, Sprint 16) | RBAC Middleware + Auth Endpoints | F-001, F-003 |
| P1 | _New: SEN-XXX_ | Restrict CORS to frontend origin | F-002 |
| P2 | _New: SEN-XXX_ | Add pagination to all list endpoints | F-004 (partial) |
| P2 | _New: CTX-XXX_ | Add `max_items` constraints to Pydantic list fields | F-005 |
| P3 | _New: SEN-XXX_ | Add security headers middleware | F-007 |
| P3 | Bundled with CTX-012 | Persist audit log to database | F-006 |

**Pull-Forward Recommendation:** LENS-008 is scheduled for Sprint 16 but addresses the two HIGH findings. Consider pulling to Sprint 6-8 if the API will be exposed beyond localhost before then. If the API remains localhost-only through Phase 5, the current risk is acceptable (development context).

---

## Methodology

1. **Static code review** of all files in `src/api/` and `src/core/`
2. **Grep scan** for dangerous patterns: `eval`, `exec`, `os.system`, `subprocess`, `__import__`, `open(` with user input
3. **CORS configuration analysis** against OWASP CORS guidelines
4. **Pydantic schema review** for missing validation constraints
5. **Data flow analysis** from API input → store operations → response serialization
6. **OWASP Top 10 (2021)** checklist applied to all 18 API endpoints

---

_End of Security Review Report_
