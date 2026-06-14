---
name: cathedral-keeper-vendor
description: Vendor (copy) Cathedral Keeper (cathedral-keeper/) into a target repo and add repo-root CK config (.cathedral-keeper.json) without runtime linking. Use when asked to "install CK", "vendor cathedral-keeper", "add Cathedral Keeper", "run ck.py analyze", or to enforce fixing/suppressing severity=high findings in changed files.
---

# Cathedral Keeper Vendor

## Overview

Make CK portable and stable by vendoring it into the target repo (copy the whole `cathedral-keeper/` folder) and adding a repo-root `.cathedral-keeper.json`. Run CK locally before committing and treat `severity=high` findings as must-fix (or explicitly suppress via repo policy).

## Workflow

### 0) Confirm the source

- Prefer vendoring from a known-good internal source repo that already contains `cathedral-keeper/` and `/.cathedral-keeper.json` (example: `medcontent-ai-platform/`).
- If you can't find those in the current workspace, ask the user for the source path/repo before proceeding (do not invent CK contents or config schema).

### 1) Install CK (vendor it)

- Copy `<source-repo>/cathedral-keeper/` into the target repo root as `cathedral-keeper/` (copy, don't link).
- Copy `<source-repo>/.cathedral-keeper.json` into the target repo root as `.cathedral-keeper.json`.
- Hard rule: do not add runtime links (no submodules, no pip/npm dependency pointing back at the source repo). CK must be a copy that travels with the repo.

Optional helper script (portable): run `scripts/vendor_ck.py` from this skill's folder if you want a safer copy with checks.

### 2) Edit `.cathedral-keeper.json` for the target repo

- Update `paths.include` / `paths.exclude` to match the target repo layout.
- Prefer discovery over guessing: inspect the repo tree and existing ignore patterns; avoid including generated folders (e.g., `node_modules/`, build outputs, caches) unless intentionally scanned.

### 3) Run locally (before committing)

Run CK from the target repo root:

- Diff mode (for PR-style changes): `python -X utf8 cathedral-keeper/ck.py analyze --root . --mode diff`
- Repo mode (when fixing systemic drift): `python -X utf8 cathedral-keeper/ck.py analyze --root . --mode repo`

If the repo has no quality-gate integration, run CK standalone with `--no-qg` (only if supported by that vendored CK version; verify via `python -X utf8 cathedral-keeper/ck.py analyze --help`).

### 4) Hard rule for findings

- Any `severity=high` finding in changed files must be fixed or explicitly suppressed via repo policy. Do not ignore it.
- If a suppression is needed, make it intentional, specific, and reviewable (policy-based), not a blanket ignore.

## Paste-Ready Agent Instructions

For a paste-ready block suitable for "Lead2Dev/agent instructions", read `references/lead2dev-agent-instructions.md`.

## Optional: Replication Packet

If the user wants a single "replication packet" (folder + config template + CI snippet), ask for:

- Target stack: Python-only vs Python+TS
- CI system: GitHub Actions vs GitLab CI vs Azure Pipelines

CI snippet references (examples; adjust to the repo):

- GitHub Actions: `references/ci-github-actions.md`
- GitLab CI: `references/ci-gitlab.md`
- Azure Pipelines: `references/ci-azure.md`
