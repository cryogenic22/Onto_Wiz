# Lead2Dev / Agent Instructions (Paste-Ready)

```
- Install CK (vendor it):
    - Copy medcontent-ai-platform/cathedral-keeper/ into the new repo as cathedral-keeper/.
    - Copy /.cathedral-keeper.json (from this repo) into the new repo root and edit paths.include/exclude for that repo.
- Run locally (before committing):
    - python -X utf8 cathedral-keeper/ck.py analyze --root . --mode diff
    - If fixing systemic drift: python -X utf8 cathedral-keeper/ck.py analyze --root . --mode repo
- Hard rule for agents:
    - Any severity=high finding in the changed files must be fixed or explicitly suppressed via repo policy (no ignore it).
- Optional integration (not required):
    - If the repo also has a gate tool, configure CK integration in /.cathedral-keeper.json; otherwise run CK standalone with --no-qg.
```
