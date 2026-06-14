# EPIC-005: Production Hardening & Operations

## Epic Summary

**As a** operations team  
**I want to** run Onto_Wiz in production  
**So that** it can serve enterprise workloads reliably

## Business Value

- Enterprise-grade reliability
- Multi-tenant support for different clients
- Proper access control
- Performance monitoring and optimization

## Epic Scope

### In Scope
- Database persistence (Postgres, Neo4j)
- Multi-tenancy architecture
- RBAC/ABAC implementation
- Telemetry and monitoring
- Caching layer

### Out of Scope
- Kubernetes deployment (ops team)
- CI/CD pipeline (DevOps)

---

## User Stories

### US-050: Persist to Postgres
**As a** system  
**I want to** persist artifacts to Postgres  
**So that** data survives restarts

**Acceptance Criteria:**
- [ ] Deltas table with full schema
- [ ] Artifacts table (patterns, guardrails, actions)
- [ ] Audit logs table
- [ ] Evidence table with permissions

**Story Points:** 5

---

### US-051: Persist Graph to Neo4j
**As a** system  
**I want to** persist the reasoning graph to Neo4j  
**So that** graph queries are efficient

**Acceptance Criteria:**
- [ ] Nodes table with types
- [ ] Edges table with types and weights
- [ ] Support for traversal queries
- [ ] Sync with Postgres artifacts

**Story Points:** 5

---

### US-052: Implement Redis Cache
**As a** system  
**I want to** cache pattern matches in Redis  
**So that** repeated queries are fast

**Acceptance Criteria:**
- [ ] Pattern match results cached
- [ ] TTL based on pattern decay
- [ ] Invalidation on pattern update
- [ ] Cache hit rate telemetry

**Story Points:** 3

---

### US-053: Multi-Tenant Architecture
**As a** administrator  
**I want to** support multiple clients  
**So that** each has isolated data

**Acceptance Criteria:**
- [ ] Global "ZS pack" as base layer
- [ ] Client overlay on top of global
- [ ] Cross-client sharing policy
- [ ] Tenant isolation validation

**Story Points:** 8

---

### US-054: Implement RBAC
**As a** administrator  
**I want to** control access by role  
**So that** users see appropriate data

**Acceptance Criteria:**
- [ ] Roles: viewer, curator, approver, admin
- [ ] Permissions per artifact type
- [ ] Audit log access control
- [ ] API authorization checks

**Story Points:** 5

---

### US-055: Implement ABAC for Evidence
**As a** system  
**I want to** control evidence access by attributes  
**So that** sensitive data is protected

**Acceptance Criteria:**
- [ ] Permission tags on evidence
- [ ] Client-specific evidence
- [ ] Role-based evidence access
- [ ] Audit of evidence access

**Story Points:** 5

---

### US-056: Telemetry Dashboard
**As a** operator  
**I want to** monitor system health  
**So that** I can respond to issues

**Acceptance Criteria:**
- [ ] Time-to-diagnosis metric
- [ ] Refusal rate (confidence halts)
- [ ] Overclaim rate (post-hoc)
- [ ] Evidence sufficiency score
- [ ] Queue depth monitoring

**Story Points:** 5

---

### US-057: Performance Benchmarks
**As a** developer  
**I want to** establish performance baselines  
**So that** regressions are detected

**Acceptance Criteria:**
- [ ] Pattern match: < 50ms p95
- [ ] Delta creation: < 100ms p95
- [ ] Intelligence packet: < 500ms p95
- [ ] Graph traversal: < 200ms p95

**Story Points:** 3

---

## Technical Tasks

| Task | Story | Estimate | Status |
|:---|:---|:---|:---|
| Postgres schema design | US-050 | 1d | 🔲 |
| SQLAlchemy models | US-050 | 2d | 🔲 |
| Neo4j schema design | US-051 | 1d | 🔲 |
| Neo4j connector | US-051 | 2d | 🔲 |
| Redis integration | US-052 | 1d | 🔲 |
| Tenant context middleware | US-053 | 2d | 🔲 |
| Global/overlay merge logic | US-053 | 3d | 🔲 |
| RBAC decorator | US-054 | 2d | 🔲 |
| ABAC evidence filter | US-055 | 2d | 🔲 |
| Telemetry collectors | US-056 | 2d | 🔲 |
| Grafana dashboards | US-056 | 1d | 🔲 |
| Benchmark suite | US-057 | 1d | 🔲 |

---

## Database Schema (Postgres)

```sql
-- Deltas table
CREATE TABLE deltas (
    id UUID PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    content JSONB NOT NULL,
    confidence FLOAT,
    blast_radius VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100),
    approved_by VARCHAR(100),
    approved_at TIMESTAMP,
    tenant_id UUID NOT NULL
);

-- Artifacts table
CREATE TABLE artifacts (
    id UUID PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    name VARCHAR(200),
    content JSONB NOT NULL,
    status VARCHAR(20),
    owner VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    decay_until TIMESTAMP,
    tenant_id UUID NOT NULL
);

-- Evidence table
CREATE TABLE evidence (
    id UUID PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    content JSONB NOT NULL,
    reliability VARCHAR(20),
    source_system VARCHAR(50),
    permission_tags VARCHAR[] DEFAULT '{}',
    tenant_id UUID NOT NULL
);
```

---

## Multi-Tenant Model

```
┌─────────────────────────────────────────┐
│  Global Layer (ZS Pack)                 │
│  - Core patterns (commercial, etc.)     │
│  - Standard guardrails                  │
│  - Base ontology                        │
└────────────────┬────────────────────────┘
                 │ inherits
┌────────────────▼────────────────────────┐
│  Client Overlay                         │
│  - Client-specific patterns             │
│  - Custom guardrails                    │
│  - Private evidence                     │
│  - Override global where needed         │
└─────────────────────────────────────────┘
```

---

## Telemetry Metrics

| Metric | Description | Target |
|:---|:---|:---|
| time_to_diagnosis | Time from question to answer | < 2s |
| refusal_rate | % of requests that halt | < 30% |
| overclaim_rate | % of claims without evidence | < 5% |
| evidence_sufficiency | Avg evidence items per claim | > 2 |
| pattern_hit_rate | % of requests with pattern match | > 60% |
| queue_depth | Pending deltas in queue | < 100 |

---

## Dependencies

- **All previous epics** - Must be stable before production

## Risks

| Risk | Mitigation |
|:---|:---|
| Data migration complexity | Incremental migration, dual-write |
| Multi-tenant bugs | Comprehensive tenant isolation tests |
| Performance degradation | Caching, query optimization |
