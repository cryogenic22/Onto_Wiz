# OntoWiz Authoring Kit

An independent, framework-neutral authoring kit for manufacturing governed
**candidate** context packs. The kit turns source evidence and SME decisions
into portable `.owworkspace` checkpoints and candidate-only `.owpack` bundles.

Phase one is intentionally separate from the Onto_Wiz platform repository. It
does not approve, activate, release, or serve a pack.

## Safety invariants

- Candidate output only: no `verified` or `active` artifacts.
- Validation fails closed on missing sources, evidence, applicability,
  disconfirming conditions, exceptions, ownership, or abstention rules.
- Protected held-out evaluations never enter this repository, a workspace, or a
  candidate package.
- The Codex and Claude adapters are thin surfaces over one deterministic,
  provider-neutral `AdapterSession`.
- Explorer output is generated and disposable; canonical files remain truth.
- Evaluation receipts are external and immutable; evaluation never edits a
  candidate package.

See `docs/IMPLEMENTATION_PLAN.md` for the gated build sequence and
`docs/CONTRACT_DECISIONS.md` for the format and lifecycle contracts.


## Install and start

Requires Python 3.11 or newer:

```shell
python -m pip install -e ".[dev]"
owak workspace init my-workspace --workspace-id my-workspace --owner-role steward --archetype enterprise_core
owak workspace validate my-workspace
```

Codex uses `adapters/codex/skills/ontowiz-authoring`; Claude uses
`adapters/claude/CLAUDE.md`. Both call the same `AdapterSession` intent,
proposal, confirmation, validation, and packaging protocol. External trust
credentials never enter adapter JSON or workspace files.

## Portable outputs

- `.owworkspace` is a deterministic, adapter-neutral authoring checkpoint. It
  includes governed session/proposal/source state and may embed raw source
  material only when the source transfer contract permits it.
- `.owpack` is a deterministic candidate distribution. It excludes raw sources,
  protected evaluations, adapter state, runtime state, generated explorer
  files, and private receipts.

Use `ontowiz_authoring.archive.verify_archive` before importing or evaluating
either format.

## Evaluation boundary

`ontowiz_evaluator` supplies strict contracts and a coordinator for an external
held-out custodian, isolated per-envelope worker broker, private scorer, and
atomic append-only receipt store. It intentionally supplies none of those
protected provider implementations. The reviewed pre-registration is still a
draft, so real held-out execution remains unauthorized and must fail closed
until an approved signed record and independently administered providers exist.

## Verify

```shell
python -m pytest --cov=src --cov-branch --cov-report=term-missing -p no:cacheprovider
python -m ruff check src tests examples adapters tools
python -m mypy
python tools/verify_vendor_lock.py
```

The local phase-one source-origin check additionally runs
`python tools/verify_source_lock.py` on the machine that holds the read-only
Onto_Wiz source repository.
