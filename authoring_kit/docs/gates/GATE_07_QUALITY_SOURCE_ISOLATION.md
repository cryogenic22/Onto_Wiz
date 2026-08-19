# Gate 7 — quality and source isolation

Status: **PASS**

## Functional and adversarial suite

- Full suite: 261 passed, 2 capability skips.
- Gate 6 external-evaluation suite: 37 passed.
- Gate 5 independent adapter/explorer review: PASS.
- Gate 6 independent evaluation-firebreak review: PASS.
- Source-origin lock: `source-lock-ok`.
- Pinned vendor lock: `vendor-lock-ok`.

The two skips are OS-capability guards for symlink/junction creation and a
Windows handle-race variant. The repository includes a two-OS GitHub Actions
matrix (`ubuntu-latest`, `windows-latest`) so relevant path-security behavior is
exercised wherever the capability exists.

## Coverage

The first attempted local 90% overall gate failed transparently at 77.79% with
the byte-for-byte pinned v0.1 vendor namespace included. Revision 2 does not set
a numeric Python coverage threshold. An independent audit rejected a post-hoc
80% target and required a measured non-regression ratchet.

The settled gate:

- measures statements and branches under `src`;
- excludes exactly `src/ontowiz_spec/pinned_v0_1/*`;
- independently verifies that excluded namespace by path inventory, byte count,
  and SHA-256;
- uses two-decimal precision; and
- fails below the measured first-party baseline of 80.77%.

The final report passed at 80.77%: 4,667/5,516 statements and 1,334/1,914
branches were covered. This quantitative code ratchet is separate from the
Revision 2 domain evaluation coverage matrix.

## Static gates

- Explicit Ruff scope (`src tests examples adapters tools`): clean.
- Configured strict mypy: 20 source files clean.
- Generated schema equality and deterministic example/package checks: covered
  by the passing full suite.
- Codex skill validator: valid.

## Phase-one isolation

The source repository remained read-only. Its 11 recorded source/specification
inputs still match the pre-edit origin lock. The independent repository vendors
only the exact locked v0.1 schema namespace; all vNext-min changes live in this
repository.
