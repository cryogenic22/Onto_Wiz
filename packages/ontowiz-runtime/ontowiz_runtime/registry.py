"""Pack loading + registry (Tier A).

Reads a compiled Domain Pack back from disk into a LoadedPack (manifest + CTX L2
doc + reconstructed artifacts). The registry lists/loads packs by name@version.
Pure Tier A: ontowiz_spec + ontowiz_ctx only — never the factory that wrote them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from ontowiz_ctx.core.model import CTXDocument
from ontowiz_ctx.core.parser import parse
from ontowiz_spec import ARTIFACT_MODELS, ArtifactBase, ArtifactKind, PackManifest


@dataclass
class LoadedPack:
    """A pack loaded from disk, ready for get_context()."""

    manifest: PackManifest
    l2_doc: CTXDocument
    artifacts: list[ArtifactBase] = field(default_factory=list)


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def load_pack(pack_dir: str | Path) -> LoadedPack:
    """Load a compiled pack directory into a LoadedPack."""
    pack_dir = Path(pack_dir)
    manifest = PackManifest.model_validate(_read_yaml(pack_dir / "pack.yaml"))
    l2_doc = parse((pack_dir / manifest.ctx_l2_path).read_text(encoding="utf-8"), level=2)

    artifacts: list[ArtifactBase] = []
    artifacts_dir = pack_dir / "artifacts"
    if artifacts_dir.is_dir():
        for yaml_file in sorted(artifacts_dir.glob("*.yaml")):
            data = _read_yaml(yaml_file)
            model = ARTIFACT_MODELS[ArtifactKind(data["kind"])]
            artifacts.append(model.model_validate(data))
    return LoadedPack(manifest=manifest, l2_doc=l2_doc, artifacts=artifacts)


class PackRegistry:
    """A directory of compiled packs: packs_root/<name>/<version>/."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def list_manifests(self) -> list[PackManifest]:
        """Every pack manifest under the root, for the registry view."""
        return [
            PackManifest.model_validate(_read_yaml(pf))
            for pf in sorted(self.root.glob("*/*/pack.yaml"))
        ]

    def load(self, name: str, version: str) -> LoadedPack:
        """Load a specific pack by name and version.

        ``name``/``version`` are caller-controlled (REST/MCP), so the resolved
        target is confined to the registry root — a traversal attempt
        (``..``, absolute path) is treated as a missing pack, not an escape.
        """
        if not name or not version:
            raise FileNotFoundError(f"pack not found: {name}@{version}")
        base = self.root.resolve()
        target = (self.root / name / version).resolve()
        # must be a strict descendant of the root (target == base, '..', absolute
        # and UNC paths all escape the intended pack and are refused)
        if target == base or base not in target.parents:
            raise FileNotFoundError(f"pack not found: {name}@{version}")
        return load_pack(target)
