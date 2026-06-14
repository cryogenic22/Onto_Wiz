# Azure Pipelines (Example)

This is an example step that runs vendored CK from the repo root.

```yaml
steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: "3.11"
  - script: python -X utf8 cathedral-keeper/ck.py analyze --root . --mode diff
    displayName: Run Cathedral Keeper (diff)
```
