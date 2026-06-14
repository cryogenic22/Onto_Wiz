# EPIC-007: Document Ingestion Pipeline

## Epic Summary

**As a** knowledge manager or domain lead
**I want to** upload documents in various formats (PDF, CSV, JSON, YAML, SQL, Parquet, MD, TXT)
**So that** the system can extract entities, relationships, and knowledge to populate the ontology

## Business Value

- Unlocks existing organizational knowledge trapped in documents
- Reduces manual ontology population by 80%+
- Supports bulk onboarding of new therapeutic areas
- Enables continuous knowledge refresh from data exports
- Transforms "dark data" (field notes, reports, databases) into structured ontology artifacts

## Epic Scope

### In Scope
- File upload endpoint (single + batch)
- Format-specific parsers (PDF, CSV, JSON, YAML, SQL, Parquet, MD, TXT)
- Chunking and preprocessing pipeline
- Integration with Agentic AI extraction (EPIC-008)
- Review queue integration (extracted artifacts → DRAFT deltas)
- Upload progress tracking UI
- Ingestion audit trail

### Out of Scope (Future)
- Real-time streaming ingestion
- Database connector (live SQL queries)
- API-to-API integration (pull from external systems)
- OCR for scanned documents (Phase 7+)

---

## User Stories

### US-070: Upload Single Document
**As a** knowledge manager
**I want to** upload a document
**So that** the system can extract relevant knowledge

**Acceptance Criteria:**
- [ ] Upload endpoint accepts: PDF, CSV, JSON, YAML, SQL, Parquet, MD, TXT
- [ ] File size limit: 50MB per file
- [ ] Returns upload ID + processing status
- [ ] File stored temporarily for processing, then deleted
- [ ] Validates file type before processing

**Story Points:** 3

---

### US-071: Batch Upload
**As a** knowledge manager
**I want to** upload multiple documents at once
**So that** I can onboard a new domain efficiently

**Acceptance Criteria:**
- [ ] Accept up to 20 files per batch
- [ ] Each file processed independently
- [ ] Batch status endpoint shows per-file progress
- [ ] Failed files don't block successful ones
- [ ] Total batch size limit: 200MB

**Story Points:** 5

---

### US-072: Format-Specific Parsing
**As a** system
**I want to** parse each format correctly
**So that** structured data is preserved and unstructured data is chunked

**Acceptance Criteria:**
- [ ] PDF: Text extraction with page/section tracking
- [ ] CSV/Parquet: Column headers as entity attributes, rows as instances
- [ ] JSON/YAML: Schema-aware parsing, nested structure preservation
- [ ] SQL: DDL parsing for schema extraction, query results for data
- [ ] MD/TXT: Section-based chunking with header hierarchy
- [ ] Parser registry: pluggable, new formats addable without core changes

**Story Points:** 8

---

### US-073: Extraction Pipeline
**As a** system
**I want to** extract entities, relationships, and facts from parsed content
**So that** knowledge enters the delta pipeline

**Acceptance Criteria:**
- [ ] Each parsed chunk → entity extraction (via EPIC-008 Agentic AI)
- [ ] Extracted entities → relationship detection
- [ ] Results → PROPOSED_ENTITY, PROPOSED_EDGE, PROPOSED_PATTERN deltas
- [ ] Source tracking: every delta links back to source document + page/section
- [ ] Confidence scoring based on extraction certainty
- [ ] Duplicate detection against existing ontology

**Story Points:** 8

---

### US-074: Upload UI with Progress
**As a** knowledge manager
**I want to** see upload progress and extraction results
**So that** I know what was extracted and can review it

**Acceptance Criteria:**
- [ ] Drag-and-drop upload area
- [ ] File type icons and validation feedback
- [ ] Progress bar per file: uploading → parsing → extracting → done
- [ ] Results summary: N entities, N relationships, N patterns found
- [ ] Link to review queue to approve/reject extracted deltas
- [ ] Error display for failed files with reason

**Story Points:** 5

---

### US-075: Ingestion Configuration
**As a** curator
**I want to** configure extraction settings per upload
**So that** I can guide what the system looks for

**Acceptance Criteria:**
- [ ] Select target therapeutic area
- [ ] Select entity types to extract (or "all")
- [ ] Set confidence threshold for auto-proposals
- [ ] Optional: provide extraction hints (key terms, expected entities)
- [ ] Configuration saved as template for repeat uploads

**Story Points:** 3

---

## Technical Tasks

| Task | Story | Ticket | Team | Est |
|:---|:---|:---|:---|:---|
| File upload endpoint + parser registry | US-070, US-072 | CTX-030 | CORTEX | L |
| Document parser implementations | US-072 | CTX-031 | CORTEX | L |
| Extraction pipeline orchestrator | US-073 | CTX-032 | CORTEX | L |
| Upload UI + progress tracking | US-074 | LENS-028 | LENS | L |
| Ingestion prompt templates per TA | US-075 | ATL-023 | ATLAS | M |
| Batch upload API | US-071 | CTX-030 | CORTEX | (included) |

---

## Supported Formats

| Format | Parser Approach | Entity Extraction |
|:---|:---|:---|
| PDF | pdfplumber → text + tables | LLM-assisted (EPIC-008) |
| CSV | pandas/csv → structured rows | Column mapping + LLM for semantics |
| Parquet | pyarrow → structured rows | Column mapping + LLM for semantics |
| JSON | Schema-aware nested parsing | Direct mapping + LLM for unstructured fields |
| YAML | Schema-aware nested parsing | Direct mapping for ontology YAML |
| SQL | DDL → schema; DML → data | Schema as entities, data as instances |
| MD | Section-based chunking | LLM-assisted (same as free text) |
| TXT | Paragraph-based chunking | LLM-assisted |

---

## Dependencies

- **EPIC-008 (Agentic AI)** — Extraction uses LLM agents for entity/relationship detection
- **Delta Model (EPIC-002)** — Extracted knowledge enters as deltas (DONE)
- **HITL Routing (CTX-006)** — Extracted deltas route to review queue (DONE)
- **DEC-012 (proposed)** — New dependencies approved: pdfplumber, pyarrow

## Risks

| Risk | Mitigation |
|:---|:---|
| LLM extraction accuracy | Start with structured formats (CSV/JSON), add unstructured later |
| Large file processing time | Async processing, progress tracking |
| Cost of LLM calls per document | Batch chunking, cache entity lookups, use cheaper models for simple extraction |
| Sensitive data in uploads | Process in-memory, don't persist raw files, audit trail |
| Parser maintenance burden | Plugin architecture, community parsers where available |
