# API Specification: Onto_Wiz

## Base URL

```
http://localhost:8000
```

---

## Delta Endpoints

### POST /deltas

Create a proposed delta.

**Request Body:**
```json
{
  "type": "PROPOSED_PATTERN",
  "content": {
    "pattern_id": "JP_REGIONAL_DIP_ONCO_GROW_V2601",
    "name": "regional_dip_access_pattern",
    "applies_when": {
      "signals": ["TRx_dip"],
      "context": ["regional_performance_dip"],
      "therapeutic_area": "oncology"
    },
    "typical_drivers": [
      {"driver_name": "access_friction", "prior_confidence": 0.7}
    ]
  },
  "confidence": 0.75,
  "source_type": "sme_game",
  "source_id": "event_123",
  "evidence_pointers": ["evidence_456"]
}
```

**Response:** `201 Created`
```json
{
  "id": "delta_789",
  "type": "PROPOSED_PATTERN",
  "status": "PROPOSED",
  "blast_radius": "MEDIUM",
  "created_at": "2026-01-31T12:00:00Z"
}
```

---

### GET /deltas

List deltas with optional filters.

**Query Parameters:**
| Parameter | Type | Description |
|:---|:---|:---|
| status | string | Filter by status (proposed, approved, rejected) |
| type | string | Filter by delta type |
| limit | int | Max results (default 100) |

**Response:** `200 OK`
```json
{
  "deltas": [
    {
      "id": "delta_789",
      "type": "PROPOSED_PATTERN",
      "status": "PROPOSED",
      "blast_radius": "MEDIUM",
      "created_at": "2026-01-31T12:00:00Z"
    }
  ],
  "total": 42
}
```

---

### POST /deltas/{id}/approve

Approve a delta.

**Request Body:**
```json
{
  "approver": "user@example.com",
  "notes": "Reviewed and looks correct"
}
```

**Response:** `200 OK`
```json
{
  "id": "delta_789",
  "status": "APPROVED",
  "approved_by": "user@example.com",
  "approved_at": "2026-01-31T12:05:00Z"
}
```

---

### POST /deltas/{id}/reject

Reject a delta with reason.

**Request Body:**
```json
{
  "reason": "Pattern too broad, needs TA scoping"
}
```

**Response:** `200 OK`
```json
{
  "id": "delta_789",
  "status": "REJECTED",
  "rejection_reason": "Pattern too broad, needs TA scoping"
}
```

---

### POST /deltas/promote

Promote all approved deltas to the reasoning graph.

**Response:** `200 OK`
```json
{
  "promoted_count": 5,
  "errors": []
}
```

---

## Intelligence Packet Endpoint

### POST /intelligence-packet

Generate an intelligence packet for a question.

**Request Body:**
```json
{
  "question": "Why did Brand X dip in Northeast?",
  "context": {
    "brand": "Brand X",
    "region": "Northeast",
    "time_period": "2026-Q1",
    "therapeutic_area": "oncology"
  },
  "traversal_policy": {
    "max_traversal_depth": 10,
    "min_confidence_threshold": 0.55,
    "only_approved_artifacts": true
  }
}
```

**Response:** `200 OK`
```json
{
  "question": "Why did Brand X dip in Northeast?",
  "drivers": [
    {
      "driver": "access_friction",
      "confidence": 0.72,
      "pattern_id": "JP_REGIONAL_DIP_ONCO_V2601",
      "evidence_used": ["payer_policy_change_123"]
    }
  ],
  "actions": [
    {
      "action": "Investigate PA edits in Northeast formularies",
      "priority": 1,
      "owner_function": "market_access"
    }
  ],
  "guardrails_hit": [],
  "trace": {
    "patterns_matched": ["JP_REGIONAL_DIP"],
    "edges_traversed": 4,
    "halted": false
  }
}
```

---

## Artifact Endpoints

### GET /artifacts

List active artifacts.

**Query Parameters:**
| Parameter | Type | Description |
|:---|:---|:---|
| type | string | pattern, guardrail, action |
| status | string | approved, deprecated |

**Response:** `200 OK`
```json
{
  "artifacts": [
    {
      "id": "pattern_123",
      "type": "pattern",
      "name": "regional_dip_access_pattern",
      "status": "approved"
    }
  ]
}
```

---

### GET /artifacts/{id}

Get artifact details.

**Response:** `200 OK`
```json
{
  "id": "pattern_123",
  "type": "pattern",
  "name": "regional_dip_access_pattern",
  "content": {
    "applies_when": {...},
    "typical_drivers": [...]
  },
  "governance": {
    "owner": "commercial_team",
    "status": "approved",
    "decay_until": "2026-07-31"
  }
}
```

---

## Evidence Endpoints

### POST /evidence

Create evidence item.

**Request Body:**
```json
{
  "type": "PAYER_DATA",
  "source_system": "IQVIA",
  "content": {
    "description": "PA reject rate increased 15%",
    "data_uri": "s3://data/payer/northeast_q1.csv"
  },
  "reliability_class": "HARD",
  "permission_tags": ["commercial", "market_access"]
}
```

**Response:** `201 Created`

---

### GET /evidence/{id}

Get evidence item.

**Response:** `200 OK`
```json
{
  "id": "evidence_456",
  "type": "PAYER_DATA",
  "reliability_class": "HARD",
  "source_system": "IQVIA",
  "captured_at": "2026-01-15T00:00:00Z"
}
```

---

## Health Check

### GET /health

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "version": "0.2.0",
  "components": {
    "delta_store": "ok",
    "judgment_store": "ok",
    "graph_store": "ok",
    "evidence_store": "ok"
  }
}
```

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "error": "VALIDATION_ERROR",
  "message": "Missing required field: type",
  "details": {...}
}
```

| Status Code | Error Type |
|:---|:---|
| 400 | VALIDATION_ERROR |
| 404 | NOT_FOUND |
| 409 | CONFLICT |
| 500 | INTERNAL_ERROR |

---

## Authentication (Planned)

Future endpoints will require:

```
Authorization: Bearer <token>
```

With claims for:
- `tenant_id`
- `role` (viewer, curator, approver, admin)
- `permissions` (list)
