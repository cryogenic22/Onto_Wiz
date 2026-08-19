# Gate 2 — adapter-neutral workspace

Status: **PASS**

Closed on: 2026-07-25

## Vertical slice

- Transactional, non-overwriting workspace initialization.
- Complete 23-directory Revision 2 scaffold.
- Canonical `workspace.yaml`, source register, durable session state,
  candidate-only `pack.yaml`, and scaffold inventory.
- Strict open/load, status, and validate operations.
- Technical CLI commands: `workspace init`, `workspace status`, and
  `workspace validate`.
- Required scaffold entries plus narrowly allowlisted dynamic source,
  session, proposal, DDR, pack, report, build, and distribution paths.
- Portable-path, case-fold collision, symlink/reparse, unknown-entry,
  protected-evaluation, manifest-drift, and identity-drift refusal.

## Automated evidence

- Authoring tests passed; two symlink tests skipped because the current Windows
  principal lacks symlink-creation privilege.
- Contract regression suite passed.
- Ruff passed.
- Strict mypy passed.
- Source-origin and vendor-origin locks passed.

## Adversarial finding resolved

The first implementation required the live tree to equal the five-file seed
inventory, making any real source extract, proposal, session, or pack artifact
invalidate the workspace. The final design treats the scaffold as required
and all authoring payloads as dynamic but explicitly allowlisted. Positive
tests populate every Revision 2 area and reopen successfully; negative tests
reject unknown names, extensions, nesting, and nonportable paths.

## Independent verdict

Portability/workspace reviewer: **PASS**.

Gate 3 was not opened until this verdict was received.
