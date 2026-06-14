# GitLab CI (Example)

This is an example job that runs vendored CK from the repo root.

```yaml
ck:
  image: python:3.11
  script:
    - python -X utf8 cathedral-keeper/ck.py analyze --root . --mode diff
```
