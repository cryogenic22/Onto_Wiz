from __future__ import annotations

import json
from pathlib import Path

from ontowiz_spec.schema_export import schema_documents


def main() -> None:
    root = Path(__file__).parents[1]
    destination = root / "schemas"
    destination.mkdir(exist_ok=True)
    for filename, schema in schema_documents().items():
        (destination / filename).write_text(
            json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )


if __name__ == "__main__":
    main()
