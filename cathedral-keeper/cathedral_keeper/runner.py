from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Tuple

from cathedral_keeper.config import CKConfig, load_config
from cathedral_keeper.git_utils import find_git_root, git_changed_files
from cathedral_keeper.integrations.registry import run_integration
from cathedral_keeper.integrations.types import IntegrationContext, parse_enabled_integrations
from cathedral_keeper.models import Finding, severity_rank
from cathedral_keeper.path_glob import filter_paths
from cathedral_keeper.policies.async_blocking import check_async_blocking
from cathedral_keeper.policies.boundaries import check_boundaries
from cathedral_keeper.policies.cycles import check_cycles
from cathedral_keeper.policies.requests_timeout import check_requests_timeouts
from cathedral_keeper.policies.syspath_hacks import check_syspath_hacks
from cathedral_keeper.python_imports import iter_python_files
from cathedral_keeper.reporting import build_report, write_json, write_markdown


@dataclass(frozen=True, slots=True)
class RunResult:
    exit_code: int
    report_md: Path
    report_json: Path


def run(args: Any) -> int:
    root = _resolve_root(args.root)
    cfg = load_config(root=root, config_path=args.config)
    files = _resolve_targets(
        root=root,
        cfg=cfg,
        mode=str(args.mode),
        base=str(args.base),
        paths_from=args.paths_from,
        verbose=bool(args.verbose),
    )
    target_paths_file, rels = _write_target_paths_file(root=root, files=files)
    ctx = IntegrationContext(root=root, target_paths_file=target_paths_file, target_rel_paths=rels)
    findings = _run_checks(ctx=ctx, cfg=cfg, files=files, disable_qg=bool(args.no_qg), verbose=bool(args.verbose))

    top_findings = int(args.top) if args.top is not None else int(cfg.reporting.get("top_findings", 50))
    out_md, out_json = _resolve_outputs(root, args)
    report = build_report(root=root, findings=findings)
    write_markdown(report, out_md, top_findings=top_findings)
    write_json(report, out_json)

    threshold = str(cfg.thresholds.get("fail_on_severity_at_or_above", "high"))
    return _exit_code(findings, threshold=threshold)


def _resolve_root(arg_root: Optional[Path]) -> Path:
    if arg_root:
        return Path(arg_root).resolve()
    git_root = find_git_root(Path.cwd())
    return git_root.resolve() if git_root else Path.cwd().resolve()


def _resolve_outputs(root: Path, args: Any) -> Tuple[Path, Path]:
    out_dir = root / ".quality-reports" / "cathedral-keeper"
    md = Path(args.out_md).resolve() if args.out_md else (out_dir / "report.md")
    js = Path(args.out_json).resolve() if args.out_json else (out_dir / "report.json")
    return md, js


def _resolve_targets(
    *,
    root: Path,
    cfg: CKConfig,
    mode: str,
    base: str,
    paths_from: Optional[Path],
    verbose: bool,
) -> List[Path]:
    include = list(cfg.paths.get("include", []) or [])
    exclude = list(cfg.paths.get("exclude", []) or [])
    exts = set([str(x).lower() for x in (cfg.paths.get("extensions", []) or [".py"])])

    if paths_from and paths_from.exists():
        items = [line.strip() for line in paths_from.read_text(encoding="utf-8", errors="ignore").splitlines()]
        files = [(root / line).resolve() for line in items if line]
        files = [p for p in files if p.exists() and p.is_file() and p.suffix.lower() in exts]
        return filter_paths(files, root=root, include=include, exclude=exclude)

    if mode == "diff":
        changed = git_changed_files(root=root, base=base)
        if changed is None:
            if verbose:
                print("[CK] git diff unavailable; falling back to repo scan for safety.")
            return _repo_targets(root=root, include=include, exclude=exclude, exts=exts)
        files = [(root / p).resolve() for p in changed]
        files = [p for p in files if p.exists() and p.is_file() and p.suffix.lower() in exts]
        return filter_paths(files, root=root, include=include, exclude=exclude)

    return _repo_targets(root=root, include=include, exclude=exclude, exts=exts)


def _repo_targets(*, root: Path, include: List[str], exclude: List[str], exts: set[str]) -> List[Path]:
    all_py = list(iter_python_files(root))
    all_py = [p for p in all_py if p.suffix.lower() in exts]
    return filter_paths(all_py, root=root, include=include, exclude=exclude)


def _run_checks(
    *,
    ctx: IntegrationContext,
    cfg: CKConfig,
    files: List[Path],
    disable_qg: bool,
    verbose: bool,
) -> List[Finding]:
    findings: List[Finding] = []
    findings.extend(_run_integrations(ctx=ctx, cfg=cfg, disable_quality_gate=disable_qg))
    findings.extend(_run_policies(root=ctx.root, cfg=cfg, files=files))
    if verbose:
        print(f"[CK] Files analyzed: {len(files)}")
        print(f"[CK] Findings: {len(findings)}")
    return findings


def _run_integrations(*, ctx: IntegrationContext, cfg: CKConfig, disable_quality_gate: bool) -> List[Finding]:
    enabled = parse_enabled_integrations(cfg.raw)
    findings: List[Finding] = []
    for integration_id, icfg in enabled.items():
        if disable_quality_gate and integration_id == "quality_gate":
            continue
        findings.extend(run_integration(ctx=ctx, integration_id=integration_id, cfg=icfg))
    return findings


def _run_policies(*, root: Path, cfg: CKConfig, files: List[Path]) -> List[Finding]:
    policies = cfg.policies
    findings: List[Finding] = []
    if _enabled(policies, "CK-PY-CYCLES"):
        findings.extend(check_cycles(root=root, cfg=policies.get("CK-PY-CYCLES") or {}, files=files))
    if _enabled(policies, "CK-PY-BOUNDARIES"):
        findings.extend(check_boundaries(root=root, cfg=policies.get("CK-PY-BOUNDARIES") or {}, files=files))
    if _enabled(policies, "CK-PY-ASYNC-BLOCKING"):
        findings.extend(check_async_blocking(root=root, cfg=policies.get("CK-PY-ASYNC-BLOCKING") or {}, files=files))
    if _enabled(policies, "CK-PY-REQUESTS-TIMEOUT"):
        findings.extend(check_requests_timeouts(root=root, cfg=policies.get("CK-PY-REQUESTS-TIMEOUT") or {}, files=files))
    if _enabled(policies, "CK-PY-SYSPATH"):
        findings.extend(check_syspath_hacks(root=root, cfg=policies.get("CK-PY-SYSPATH") or {}, files=files))
    return findings


def _enabled(policies: dict, pid: str) -> bool:
    p = policies.get(pid) or {}
    return bool(p.get("enabled", False))


def _exit_code(findings: List[Finding], *, threshold: str) -> int:
    thr = severity_rank(threshold)
    worst = 0
    for f in findings:
        worst = max(worst, severity_rank(f.severity))
    return 1 if worst >= thr and thr > 0 else 0


def _write_target_paths_file(*, root: Path, files: List[Path]) -> Tuple[Path, List[str]]:
    out_dir = root / ".quality-reports" / "cathedral-keeper"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "paths.txt"
    rels = [str(p.resolve().relative_to(root.resolve())).replace("\\", "/") for p in files if p.exists()]
    path.write_text("\n".join(rels) + "\n", encoding="utf-8")
    return path, rels
