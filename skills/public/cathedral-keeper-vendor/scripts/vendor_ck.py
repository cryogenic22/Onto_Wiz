from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def _require_exists(path: Path, what: str) -> None:
    if not path.exists():
        raise SystemExit(f"Missing {what}: {path}")


def _copytree_strict(src: Path, dst: Path, overwrite: bool) -> None:
    if dst.exists():
        if not overwrite:
            raise SystemExit(f"Target already exists (use --overwrite): {dst}")
        if dst.is_dir():
            shutil.rmtree(dst)
        else:
            dst.unlink()
    shutil.copytree(src, dst)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Vendor Cathedral Keeper into a target repo by copying cathedral-keeper/ and "
            ".cathedral-keeper.json from a source repo. This intentionally avoids runtime linking."
        )
    )
    parser.add_argument(
        "--source-root",
        required=True,
        help="Path to the source repo root containing cathedral-keeper/ and .cathedral-keeper.json.",
    )
    parser.add_argument(
        "--target-root",
        default=".",
        help="Path to the target repo root (default: current directory).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing cathedral-keeper/ or .cathedral-keeper.json in target.",
    )
    args = parser.parse_args()

    source_root = Path(args.source_root).expanduser().resolve()
    target_root = Path(args.target_root).expanduser().resolve()

    src_ck_dir = source_root / "cathedral-keeper"
    src_ck_entry = src_ck_dir / "ck.py"
    src_cfg = source_root / ".cathedral-keeper.json"
    _require_exists(src_ck_entry, "cathedral-keeper/ck.py")
    _require_exists(src_cfg, ".cathedral-keeper.json")

    dst_ck_dir = target_root / "cathedral-keeper"
    dst_cfg = target_root / ".cathedral-keeper.json"

    _copytree_strict(src_ck_dir, dst_ck_dir, overwrite=args.overwrite)
    shutil.copy2(src_cfg, dst_cfg)

    # Lightweight sanity check: config parses as JSON.
    try:
        json.loads(dst_cfg.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"Copied config is not valid JSON: {dst_cfg} ({e})")

    print("Vendored Cathedral Keeper:")
    print(f"- {dst_ck_dir}")
    print(f"- {dst_cfg}")
    print()
    print("Next:")
    print("- Edit .cathedral-keeper.json paths.include/paths.exclude for this repo.")
    print("- Run: python -X utf8 cathedral-keeper/ck.py analyze --root . --mode diff")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
