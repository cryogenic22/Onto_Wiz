# GitHub Actions (Example)

This is an example workflow job that runs vendored CK from the repo root.

Adjust triggers, Python version, and checkout depth to match your repo.

```yaml
name: cathedral-keeper

on:
  pull_request:
  push:
    branches: [main]

jobs:
  ck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Run Cathedral Keeper (diff)
        run: python -X utf8 cathedral-keeper/ck.py analyze --root . --mode diff
```
