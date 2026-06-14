#!/usr/bin/env python3
"""
Slop Checker — Automated Anti-Slop Enforcement (SEN-002)
=========================================================
AST-based, stdlib-only checker that enforces anti_slop.md rules
not already covered by quality_gate.py's regex/heuristic approach.

Checks:
  1. function_size     — AST: function body > max_lines (from config.yaml)
  2. cyclomatic_complexity — AST: branches per function > max (from config.yaml)
  3. unused_imports    — AST: imported names not referenced in code
  4. commented_out_code — Regex: lines matching code-like comment patterns
  5. bare_except       — AST: ExceptHandler with no type, or body that is only `pass`

Usage:
    python quality/slop_checker.py                        # Check src/ and tests/
    python quality/slop_checker.py src/api/server.py      # Check specific file
    python quality/slop_checker.py --config quality/config.yaml

Exit codes:
    0 - No findings
    1 - Findings detected

Owner: Team SENTINEL
"""

from __future__ import annotations

import argparse
import ast
import re
from pathlib import Path
from typing import NamedTuple

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

EXCLUDE_DIRS = {
    "node_modules", "dist", "build", ".next", ".git", "__pycache__",
    ".pytest_cache", ".venv", "venv", "site-packages", "quality-gate",
    "cathedral-keeper", ".quality-reports",
}

# Defaults (overridden by config.yaml if provided)
DEFAULT_MAX_FUNCTION_LINES = 50
DEFAULT_MAX_COMPLEXITY = 10


class Finding(NamedTuple):
    file: str
    line: int
    rule: str
    message: str
    suggestion: str


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _load_config(config_path: str | None) -> dict:
    if not config_path or yaml is None:
        return {}
    p = Path(config_path)
    if not p.exists():
        return {}
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def _collect_files(root: Path, target: Path) -> list[Path]:
    if target.is_file() and target.suffix == ".py":
        return [target]
    files: list[Path] = []
    for p in target.rglob("*.py"):
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        if p.is_file():
            files.append(p)
    return sorted(files)


# ── Check 1: Function size (AST) ──────────────────────────────

def check_function_size(
    tree: ast.Module, rel: str, *, max_lines: int,
) -> list[Finding]:
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.body:
            continue
        start = node.body[0].lineno
        end = max(
            getattr(n, "end_lineno", getattr(n, "lineno", start))
            for n in ast.walk(node) if hasattr(n, "lineno")
        )
        body_lines = end - start + 1
        if body_lines > max_lines:
            findings.append(Finding(
                file=rel,
                line=node.lineno,
                rule="function_size",
                message=f"'{node.name}' is {body_lines} lines (max {max_lines})",
                suggestion="Extract helper functions to reduce size.",
            ))
    return findings


# ── Check 2: Cyclomatic complexity (AST) ──────────────────────

_BRANCH_TYPES = (
    ast.If, ast.For, ast.While, ast.ExceptHandler,
    ast.With, ast.Assert,
)


def _count_branches(node: ast.AST) -> int:
    count = 0
    for child in ast.walk(node):
        if isinstance(child, _BRANCH_TYPES):
            count += 1
        elif isinstance(child, ast.BoolOp):
            count += len(child.values) - 1
    return count


def check_cyclomatic_complexity(
    tree: ast.Module, rel: str, *, max_complexity: int,
) -> list[Finding]:
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        complexity = 1 + _count_branches(node)
        if complexity > max_complexity:
            findings.append(Finding(
                file=rel,
                line=node.lineno,
                rule="cyclomatic_complexity",
                message=f"'{node.name}' has complexity {complexity} (max {max_complexity})",
                suggestion="Simplify conditionals or extract logic into helper functions.",
            ))
    return findings


# ── Check 3: Unused imports (AST) ─────────────────────────────

def _gather_imported_names(tree: ast.Module) -> list[tuple[str, int]]:
    names: list[tuple[str, int]] = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                used_name = alias.asname if alias.asname else alias.name.split(".")[0]
                names.append((used_name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("__future__"):
                continue
            for alias in node.names:
                if alias.name == "*":
                    continue
                used_name = alias.asname if alias.asname else alias.name
                names.append((used_name, node.lineno))
    return names


def _gather_referenced_names(tree: ast.Module) -> set[str]:
    refs: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            refs.add(node.id)
        elif isinstance(node, ast.Attribute):
            base = node
            while isinstance(base, ast.Attribute):
                refs.add(base.attr)
                base = base.value
            if isinstance(base, ast.Name):
                refs.add(base.id)
    return refs


def _gather_all_exports(tree: ast.Module) -> set[str]:
    """Collect names listed in __all__ so they aren't flagged as unused."""
    exports: set[str] = set()
    for node in ast.iter_child_nodes(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__all__":
                if isinstance(node.value, (ast.List, ast.Tuple)):
                    for elt in node.value.elts:
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            exports.add(elt.value)
    return exports


def check_unused_imports(tree: ast.Module, rel: str) -> list[Finding]:
    imported = _gather_imported_names(tree)
    referenced = _gather_referenced_names(tree) | _gather_all_exports(tree)

    findings: list[Finding] = []
    for name, lineno in imported:
        if name not in referenced:
            findings.append(Finding(
                file=rel,
                line=lineno,
                rule="unused_import",
                message=f"'{name}' imported but not used",
                suggestion=f"Remove unused import '{name}'.",
            ))
    return findings


# ── Check 4: Commented-out code ───────────────────────────────

_COMMENT_CODE_RE = re.compile(
    r"^\s*#\s*("
    r"def\s|class\s|import\s|from\s\S+\simport\s|"
    r"return\s|yield\s|raise\s|"
    r"if\s|elif\s|else:|for\s|while\s|"
    r"try:|except\s|finally:|"
    r"\w+\s*=\s*|"
    r"\w+\.\w+\("
    r")"
)


_COMMENT_SKIP_PREFIXES = ("#!", "# ---", "# ===", "# type:")


def _is_code_comment(stripped: str) -> bool:
    if not stripped.startswith("#"):
        return False
    if any(stripped.startswith(p) for p in _COMMENT_SKIP_PREFIXES):
        return False
    return _COMMENT_CODE_RE.match(stripped) is not None


def _make_commented_code_finding(rel: str, start: int, length: int) -> Finding:
    return Finding(
        file=rel,
        line=start + 1,
        rule="commented_code",
        message=f"{length} consecutive lines of commented-out code",
        suggestion="Remove dead code. Use version control to recover it.",
    )


def check_commented_code(lines: list[str], rel: str) -> list[Finding]:
    findings: list[Finding] = []
    run_start = -1
    run_length = 0

    for i, raw in enumerate(lines):
        if _is_code_comment(raw.strip()):
            if run_start < 0:
                run_start = i
            run_length += 1
        else:
            if run_length >= 3:
                findings.append(_make_commented_code_finding(rel, run_start, run_length))
            run_start = -1
            run_length = 0

    if run_length >= 3:
        findings.append(_make_commented_code_finding(rel, run_start, run_length))
    return findings


# ── Check 5: Bare except / except-pass ────────────────────────

def check_bare_except(tree: ast.Module, rel: str) -> list[Finding]:
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        if node.type is None:
            findings.append(Finding(
                file=rel,
                line=node.lineno,
                rule="bare_except",
                message="Bare `except:` catches all exceptions including SystemExit/KeyboardInterrupt",
                suggestion="Catch a specific exception type.",
            ))
        elif (
            len(node.body) == 1
            and isinstance(node.body[0], ast.Pass)
        ):
            findings.append(Finding(
                file=rel,
                line=node.lineno,
                rule="bare_except",
                message="`except ... : pass` silently swallows errors",
                suggestion="Log the error, re-raise, or handle explicitly.",
            ))
    return findings


# ── Orchestrator ──────────────────────────────────────────────

def check_file(
    file_path: Path,
    root: Path,
    *,
    max_lines: int,
    max_complexity: int,
) -> list[Finding]:
    rel = _rel(file_path, root)
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    lines = content.splitlines()
    findings: list[Finding] = []

    # AST-based checks
    try:
        tree = ast.parse(content, filename=rel)
    except SyntaxError:
        return findings

    findings.extend(check_function_size(tree, rel, max_lines=max_lines))
    findings.extend(check_cyclomatic_complexity(tree, rel, max_complexity=max_complexity))
    findings.extend(check_unused_imports(tree, rel))
    findings.extend(check_commented_code(lines, rel))
    findings.extend(check_bare_except(tree, rel))

    return findings


def run(
    root: Path,
    target: Path,
    *,
    max_lines: int,
    max_complexity: int,
) -> list[Finding]:
    files = _collect_files(root, target)
    all_findings: list[Finding] = []
    for f in files:
        all_findings.extend(check_file(
            f, root,
            max_lines=max_lines,
            max_complexity=max_complexity,
        ))
    return all_findings


def _print_report(findings: list[Finding], total_files: int) -> None:
    if not findings:
        print(f"[SlopChecker] PASSED — {total_files} files, no slop detected.")
        return

    by_file: dict[str, list[Finding]] = {}
    for f in findings:
        by_file.setdefault(f.file, []).append(f)

    print(f"\n{'=' * 60}")
    print(f"SLOP CHECKER — {len(findings)} finding(s) in {len(by_file)} file(s)")
    print(f"{'=' * 60}")

    for file, fs in sorted(by_file.items()):
        print(f"\n{file}:")
        for f in sorted(fs, key=lambda x: x.line):
            print(f"  [E] Line {f.line}: [{f.rule}] {f.message}")
            print(f"      Fix: {f.suggestion}")

    print(f"\n{'-' * 60}")
    print(f"[FAILED] {len(findings)} slop finding(s)")
    print(f"{'-' * 60}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Slop Checker — Anti-Slop Enforcement")
    parser.add_argument("paths", nargs="*", help="Files or directories to check (default: src/ tests/)")
    parser.add_argument("--config", default=None, help="Path to config.yaml")
    parser.add_argument("--root", default=".", help="Project root directory")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()

    # Load config
    cfg = _load_config(args.config)
    max_lines = int(
        cfg.get("function_size", {}).get("max_lines", DEFAULT_MAX_FUNCTION_LINES)
    )
    max_complexity = int(
        cfg.get("complexity", {}).get("max_cyclomatic", DEFAULT_MAX_COMPLEXITY)
    )

    # Determine targets
    targets: list[Path] = []
    if args.paths:
        for p in args.paths:
            t = Path(p)
            if not t.is_absolute():
                t = (root / t).resolve()
            targets.append(t)
    else:
        for subdir in ["src", "tests"]:
            t = root / subdir
            if t.is_dir():
                targets.append(t)

    if not targets:
        print("[SlopChecker] No targets found.")
        return 0

    all_findings: list[Finding] = []
    total_files = 0
    for target in targets:
        files = _collect_files(root, target)
        total_files += len(files)
        all_findings.extend(run(
            root, target,
            max_lines=max_lines,
            max_complexity=max_complexity,
        ))

    _print_report(all_findings, total_files)
    return 1 if all_findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
