"""L2 — drop-a-file pack expansion: the seed merges multiple module YAMLs.

A function module is an ``ontology/commercial/<function>.yaml`` file that declares
its ``function`` once (the default for all its rules) and contributes inference
rules (and optionally entities). The seed reads the base ontology plus every
module in the directory and merges them into one pack.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from ontowiz_factory.seed import (
    artifacts_from_commercial_modules,
    build_commercial_pack,
)
from ontowiz_runtime.registry import load_pack
from ontowiz_spec import ArtifactKind, TagDimension

BASE = textwrap.dedent(
    """
    ontology:
      name: Base
      meta_model:
        entities:
          - name: Brand
            attributes: [therapeutic_area]
        relationships: []
      inference_rules:
        - id: rule_base_one
          function: base
          description: base rule
          conditions: []
          logic: x
          consequence: { verdict: "v" }
    """
)

MODULE = textwrap.dedent(
    """
    ontology:
      name: Forecasting
      function: forecasting
      meta_model:
        entities:
          - name: Forecast
            attributes: [horizon]
      inference_rules:
        - id: rule_loe_cliff
          description: loe erosion
          conditions: []
          logic: y
          consequence: { verdict: "w" }
    """
)


def _write_tree(root: Path) -> Path:
    base = root / "commercial.yaml"
    base.write_text(BASE, encoding="utf-8")
    modules = root / "commercial"
    modules.mkdir()
    (modules / "forecasting.yaml").write_text(MODULE, encoding="utf-8")
    return base


def test_modules_merge_into_one_artifact_set(tmp_path):
    base = _write_tree(tmp_path)
    arts = artifacts_from_commercial_modules(base, tmp_path / "commercial")
    by_id = {a.id: a for a in arts}
    # both the base rule and the module rule are present
    assert "rule_base_one" in by_id
    assert "rule_loe_cliff" in by_id

    def fns(a):
        return {t.value for t in a.tags if t.dimension == TagDimension.FUNCTION}

    # the module's declared function defaults onto its rules
    assert fns(by_id["rule_loe_cliff"]) == {"forecasting"}
    assert fns(by_id["rule_base_one"]) == {"base"}
    # entities from base and module are merged into a single registry
    registries = [a for a in arts if a.kind == ArtifactKind.ENTITY_REGISTRY]
    assert len(registries) == 1
    names = {e.name for e in registries[0].entities}
    assert {"Brand", "Forecast"} <= names


def test_build_pack_auto_includes_sibling_modules(tmp_path):
    # drop-a-file: build_commercial_pack picks up the sibling commercial/ dir
    base = _write_tree(tmp_path)
    pack_dir = build_commercial_pack(base, tmp_path / "out")
    loaded = load_pack(pack_dir)
    ids = {a.id for a in loaded.artifacts}
    assert "rule_loe_cliff" in ids  # the module rule shipped without changing the seed
