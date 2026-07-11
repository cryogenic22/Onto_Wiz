# Mini-spec — F0.4A: Managed parser boundary (parser IR: Source/Chunk/SourceSpan + registry) — v2

**Unit:** F0.4A · **Owner:** BE/KE · **Depends on:** none (0C: parallelizable — runs
alongside F0.2H) · **Blocks:** F0.4B → E1.1 → E1.2.
**Anchors:** BUILD_INSTRUCTION_SET §13 (F0.4A/B card, steps 1–7 + DoD), §12.2 (`EvidenceRef`
— the *served* evidence contract, owned later), §12.3 (415/413/422 semantics; logs never
contain source text), R5 (LLM only in structurer/eval — **parsers are model-free**), R6 (no
new speculative deps), R13 (access class). Status target: NOT READY → READY on acceptance.

> **Review response — REV pass 1 (F0.4A findings 4–9):**
> - **#4 spans:** a chunk carries **one or more `SourceSpan`s** over normalized `SourceUnit`s;
>   round-trip tests **reconstruct chunk text from spans**, not JSON echo.
> - **#5 identity vs instance:** content identity (`content_hash` + per-chunk content hashes)
>   is separated from the **ingestion instance** (`access_class`/`filename`/`captured_at`);
>   F0.4A **never reuses a prior `ParseResult`** across calls — identical bytes only guarantee
>   identical content ids; policy-aware persistent dedup is **E1.1**.
> - **#6 one quarantine contract:** quarantine is a **returned**
>   `ParseResult(status='quarantined', chunks=[])`; `QuarantinedSourceError` is removed. Only
>   pre-parse guard rejections (disallowed type / oversized) **raise** (→ 415 / 413).
> - **#7 not canonical:** these are explicitly **parser-local IR (Tier B)**; the shared served
>   Source/Chunk contract is **E1.1's** deliverable — there is no competing "canonical" shape.
> - **#8 deps + archives:** `packages/ontowiz-factory/pyproject.toml` is in the file list with
>   a Lead2Dev dep-approval note; concrete DOCX zip limits (members / per-member / total
>   expanded / ratio) + zip-bomb & path-entry tests.
> - **#9 PDF fixture:** a **reviewed minimal raw-PDF byte builder** emits genuinely extractable
>   text with no new dependency.
> - **#1 governance ancestry (cross-cutting):** this spec is parented on governance SHA
>   `2ba342b`, so §12/§13 resolve in-tree.

## 1. Objective & user-observable outcome

A single **model-free** parser boundary turns uploaded bytes into a `Source` (an ordered set
of **normalized `SourceUnit`s** — pages/paragraphs/cues) plus `Chunk[]`, where **each chunk
carries the `SourceSpan`s that reconstruct its exact text** against those units. Identical
bytes yield **identical content ids** (a dedup *signal* for E1.1, not a cache here); every
ingestion is a **fresh instance** carrying its own `access_class`/`filename`/`captured_at`;
and unsafe input (disallowed type, oversized, extension/content mismatch, encrypted,
malformed, archive-bomb, path-entry) is **quarantined whole** — never partially promoted.
This is **parser-local IR**, not the served contract; no LLM, no network, no serve surface.

## 2. Preconditions & pinned dependencies

- **Reuse-first (gate 1).** `src/knowledge/parsers/` already parses PDF (pypdf) and DOCX
  (python-docx) into sectioned text + tables, with `chunker.py` (`TextChunker`) and
  `type_detector.py`. F0.4A **ports** that extraction behind the new boundary — it does **not**
  re-implement it (provenance noted per file, §3). The chunker port is **adapted** to emit
  `SourceSpan`s (offset tracking) — the one non-trivial change.
- **Deps (R6 / ADR-006, #8).** `pypdf` + `python-docx` are declared on `ontowiz-factory`
  (`pyproject.toml`, in the file list). **Pre-existing** in `src/` (lazily imported today),
  **relocated not new**; the heavy `unstructured` primary path is **dropped** (pypdf's
  deterministic text suffices for golden parity, far lighter). TXT/VTT and the archive guard
  use **stdlib only** (`zipfile`). A Lead2Dev dep-approval note is logged (ADR-017 pattern).
- Contracts: this unit produces the **source/chunk/span substrate**; the *served* `EvidenceRef`
  (§12.2) and the shared managed Source/Chunk contract are **E1.1's**, referencing this
  substrate by **hash + span primitives** (§10, #7).

## 3. Files & ownership paths (BE/KE, `packages/ontowiz-factory/` — Tier B build worker)

Parsing is **private build-worker** work (Tier B), where the deps and format quirks live; the
public serve plane never imports it. New subpackage `ontowiz_factory/parsers/`:

- **new** `parsers/models.py` — **parser IR** (not canonical): `SourceUnit`, `SourceSpan`,
  `Source`, `Chunk`, `ParseResult`; typed **raise** errors `UnsupportedSourceError` (→415),
  `SourceTooLargeError` (→413). Quarantine is a **status**, never an exception. Pure data,
  zero parser deps, model-free.
- **new** `parsers/registry.py` — `Parser` `Protocol` + `ParserRegistry`: allowlist,
  extension/content agreement, raw-size + archive bounds, dispatch, quarantine-as-return,
  deterministic content ids.
- **new** `parsers/archive.py` — stdlib `zipfile` bounds + zip-slip guard for zip formats
  (DOCX now; reused by F0.4B PPTX/XLSX).
- **port** `parsers/pdf.py` — from `src/knowledge/parsers/pdf_parser.py`, **pypdf path only**
  (drop `unstructured`); `page` units.
- **port** `parsers/docx.py` — from `src/knowledge/parsers/docx_parser.py`; `paragraph` units
  + heading context; runs behind the archive guard.
- **new** `parsers/text.py` — TXT (stdlib): `char_span` units.
- **new** `parsers/vtt.py` — WebVTT (stdlib regex): `timestamp` cue units.
- **port+adapt** `parsers/chunking.py` — from `src/knowledge/parsers/chunker.py`, adapted to
  attach `SourceSpan`s (tracks unit char offsets, incl. overlap).
- **modify** `ontowiz_factory/__init__.py` — export the boundary.
- **modify** `packages/ontowiz-factory/pyproject.toml` — declare `pypdf`, `python-docx` (#8).
- **modify** `docs/Lead2Dev.md` — dep-approval note for the two relocated deps (#8).
- **new** `tests/test_parsers.py` + `tests/fixtures/parsers/` — golden / malformed / oversized
  / span-reconstruction / archive-bomb / path-entry fixtures + the reviewed minimal-PDF byte
  builder (#9).

`src/knowledge/parsers/` is **left intact** (F0.5 owns legacy deletion). No files outside
`ontowiz-factory/` + `docs/Lead2Dev.md` + this spec.

## 4. Parser IR (the data — parser-local, **not** canonical; #7)

```
LocatorKind = page | paragraph | char_span | timestamp        # F0.4B: + slide | cell | message_part
SourceUnit(kind: LocatorKind, ref: str, text: str)            # normalized atomic unit ("p.3" / "¶12" / cue ts), ordered in Source
SourceSpan(unit_ref: str, start: int, end: int)               # half-open char range within a unit's normalized text
Source(content_hash, filename, media_type, byte_size, units: list[SourceUnit],
       access_class, captured_at, parser, parser_version, status, warnings[])
Chunk(content_id, ordinal, text, spans: list[SourceSpan], heading_context, token_estimate)
ParseResult(source, chunks)
```

- **Content identity vs ingestion instance (#5).** `content_hash = sha256(bytes)` and
  `Chunk.content_id = sha256(normalized chunk text)` are **pure content** — identical bytes ⇒
  identical ids on every call and machine. `access_class` / `filename` / `captured_at` are
  **ingestion-instance** fields, caller-supplied, and are **not** deduplicated. F0.4A returns a
  **fresh** `Source` per call (**no cache, no cross-call reuse**); persistent, policy-aware
  dedup/reuse is **E1.1** — so a restricted upload can never inherit a prior, less-restricted
  caller's metadata.
- **Spans reconstruct chunk text (#4).** Each `SourceUnit.text` is NFC + whitespace-normalized;
  a `Chunk` is composed from `SourceSpan`s over those units, so
  `"".join(units[s.unit_ref].text[s.start:s.end] for s in chunk.spans) == chunk.text`. A chunk
  may span **several** units (multi-paragraph / multi-cue), and spans may **overlap between
  adjacent chunks** (chunker overlap window). Reconstruction is exact against the normalized
  units — the tests resolve spans, not just serialize/deserialize.
- `access_class` (R13) is caller-supplied, never inferred; `captured_at` is passed in
  (deterministic tests), never read from the clock here. All ids are hash-derived (no
  wall-clock / random) → deterministic across runs.

## 5. Parser protocol, registry & the guarded pipeline

`Parser` `Protocol`: `media_types: frozenset[str]`; `parse(raw: bytes, filename: str,
access_class: str, captured_at: str) -> ParseResult`. `ParserRegistry.parse(...)` runs, in order:

1. **Allowlist** — `media_type ∈ {application/pdf, …wordprocessingml.document, text/plain,
   text/vtt}` else **raise** `UnsupportedSourceError` (→ 415).
2. **Raw-size guard** — `byte_size ≤ MAX_SOURCE_BYTES` else **raise** `SourceTooLargeError` (→ 413).
3. **Extension/content agreement** — magic-byte sniff; if declared type, extension and sniffed
   signature disagree → **quarantine (returned)**.
4. **Safe filename** — path-traversal / reserved-name reject (reuse the round-2 red-team validator).
5. **Archive guard** (zip formats, DOCX) — pre-open `zipfile` inspection: `members ≤
   MAX_ZIP_MEMBERS`, each `≤ MAX_MEMBER_BYTES`, total expanded `≤ MAX_TOTAL_EXPANDED_BYTES`,
   ratio `≤ MAX_COMPRESSION_RATIO`, and **no absolute / `..` member paths** (zip-slip); any
   breach → **quarantine (returned)**.
6. **Dispatch** — encrypted / malformed → **quarantine (returned)**.

**Single quarantine contract (#6):** quarantine is *always* a returned
`ParseResult(source.status='quarantined', chunks=[])` (never partial). The **only** exceptions
are the pre-parse guards in steps 1–2 (415 / 413), which are caller errors. Determinism
invariant: same bytes + declared type ⇒ byte-identical `content_hash`, `content_id`s, units and
spans across runs.

**Bounds** (config constants; no new infra): `MAX_SOURCE_BYTES = 25 MiB`, `MAX_UNITS = 5000`,
`MAX_ZIP_MEMBERS = 1024`, `MAX_MEMBER_BYTES = 32 MiB`, `MAX_TOTAL_EXPANDED_BYTES = 64 MiB`,
`MAX_COMPRESSION_RATIO = 100`.

## 6. Threat & data-egress delta

- **Model-free (R5):** no parser opens a socket or reads an LLM key; a parse succeeds with
  `ANTHROPIC_API_KEY` unset (test-enforced).
- **No source text in logs (§12.3/R13):** warnings live on the `Source`; logs carry
  ids/sizes/timing only.
- **Untrusted-input containment:** allowlist (415), raw-size (413), extension/content agreement,
  safe filename, **archive bounds + zip-slip** (DOCX now; PPTX/XLSX in F0.4B), whole-source
  quarantine for encrypted/malformed. Unsafe input cannot escape storage or exhaust configured
  bounds (DoD).
- **No metadata reuse across ingestions (#5):** a restricted upload never receives a prior
  caller's access class/filename/capture time.

## 7. Tests mapped 1:1 to acceptance

| Acceptance (DoD / finding) | Test |
|---|---|
| one interface, all four formats parse | `test_registry_parses_pdf_docx_txt_vtt` |
| **#5** identical bytes → same content ids, **fresh instance** (no metadata reuse) | `test_identical_bytes_same_content_ids_fresh_instance` |
| **#4** chunk text reconstructs from spans over units | `test_chunk_text_reconstructs_from_spans` |
| **#4** a multi-unit chunk carries multiple spans | `test_multi_unit_chunk_has_multiple_spans` |
| **#4** overlap window → spans overlap between adjacent chunks, both reconstruct | `test_overlap_spans_reconstruct_both_chunks` |
| page / paragraph / char / timestamp unit kinds | `test_unit_kind_per_format` |
| golden text + units per format | `test_golden_{pdf,docx,txt,vtt}` |
| **#6** malformed → **returned** quarantined result, no chunks | `test_malformed_returns_quarantined_result` |
| **#6** encrypted PDF → quarantined result | `test_encrypted_pdf_quarantined_result` |
| extension/content mismatch → quarantined result | `test_extension_content_mismatch_quarantined` |
| **#8** DOCX zip-bomb (ratio / expanded over limit) → quarantined | `test_docx_zip_bomb_quarantined` |
| **#8** DOCX zip-slip member path → quarantined | `test_docx_path_entry_quarantined` |
| oversized raw → **raise** 413 | `test_oversized_raw_raises` |
| disallowed type → **raise** 415 | `test_unsupported_media_type_raises` |
| **R5** model-free (no key) | `test_parse_succeeds_without_api_key` |
| no source text in logs (§12.3) | `test_logs_exclude_source_text` |
| **#9** minimal PDF fixture yields extractable text | `test_minimal_pdf_builder_is_extractable` |

**Fixtures.** **#9** a reviewed ~25-line **raw-PDF byte builder** emits a valid single-page PDF
with a `BT … Tj ET` text object → pypdf extracts the known string (no new dependency); DOCX via
python-docx; TXT/VTT literals; zip-bomb / path-entry fixtures built with stdlib `zipfile`.
Coverage ≥85% on `parsers/`; branch + negative (quarantine/limits) + span-reconstruction covered.

## 8. Migration, rollback & recovery

No schema/data migration (new code; `src/knowledge/parsers` untouched — F0.5 deletes it).
Rollback = drop the `parsers/` subpackage; no persisted state, no consumers yet. Recovery N/A
(pure function of bytes).

## 9. Telemetry & operational failure behaviour

Pre-parse guards raise typed errors (`UnsupportedSourceError`→415, `SourceTooLargeError`→413);
quarantine is a recorded status (F0.3/E1 map to HTTP). Warnings accumulate on the `Source`,
never logged with content.

## 10. Out of scope & residual risk

- **PPTX/XLSX/EML** + their locators (slide/cell/message-part) and bounds → **F0.4B**
  (`LocatorKind` reserves those kinds; `archive.py` is reused).
- **Managed persistence + the shared *served* Source/Chunk contract → E1.1.** F0.4A models are
  explicitly **parser-local IR**, not the canonical served shape (#7); E1.1 defines the one
  shared contract and maps IR → managed store (content hashes are the join key). There is no
  duplicate "canonical" shape.
- pypdf yields page-accurate spans (char offsets within extracted page text), **not**
  bbox-accurate geometry — sufficient until a highlight-on-PDF FE need appears.

## 11. Dependency change

`pypdf` + `python-docx` added to `ontowiz-factory/pyproject.toml` (pre-existing in `src/`;
relocated, not new — Lead2Dev dep note per ADR-006/ADR-017). `unstructured` **not** carried
over. TXT/VTT, the registry, models and the archive guard (`zipfile`) are **stdlib only**. No
serve/Tier-A dependency added.
