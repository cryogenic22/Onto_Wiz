"""The compiled Domain Pack manifest — the contract for the product.

A pack is the unit that crosses the Tier A / Tier B boundary. The compiler
(Tier B) emits it; the runtime (Tier A) consumes it. On disk a pack is:

    packs/<name>/<version>/
      ├── pack.yaml          # this manifest (PackManifest, serialised)
      ├── artifacts/*.yaml    # the governed artifact sources (YAML — the product)
      ├── context.ctx         # compiled CTX L2 layer (entities + sections)
      ├── index.l3.ctx        # compiled CTX L3 directory (system-prompt index)
      └── pack.sig            # detached signature over the above (IP protection)
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PackLayer(BaseModel):
    """One layer in the overlay stack, with its precedence."""

    id: str                      # e.g. "therapy-oncology"
    name: str
    precedence: int              # 1 = base, higher overrides lower
    extends: str | None = None
    tags: list[dict] = Field(default_factory=list)  # default tags for the layer


class PackEvalSummary(BaseModel):
    """The eval-gate verdict baked into the manifest at compile time."""

    eval_cases: int = 0
    pass_rate: float = 0.0
    agent_lift: float | None = None   # with-pack vs without-pack delta
    last_run_at: str | None = None
    gate_passed: bool = False


class PackManifest(BaseModel):
    """Everything a runtime needs to load, trust, and version a pack."""

    name: str
    version: str                         # semver, e.g. "1.3.0"
    description: str = ""
    domain: str = ""                     # e.g. "commercial" — the catalog grouping
    author: str = "ontowiz"

    # overlay stack (base → therapy → function → client → engagement)
    layers: list[PackLayer] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)  # "name@version" pins

    # counts for the registry view
    artifact_count: int = 0
    artifact_kinds: dict[str, int] = Field(default_factory=dict)

    # quality / freshness
    evals: PackEvalSummary = Field(default_factory=PackEvalSummary)
    coverage: float = 0.0                # codified-domain coverage estimate
    freshness_days: int | None = None  # age of the oldest active artifact

    # provenance & IP
    compiled_at: str | None = None
    compiler_version: str = "0.1.0"
    # IMPLEMENTED: pack.sig is a SHA-256 integrity seal (tamper-evident); set True
    # by write_pack, checked by verify_pack. It proves bytes-unchanged, not PKI
    # authorship — cryptographic authorship signing is roadmap.
    signed: bool = False
    # ROADMAP (not yet implemented): artifact sources currently ship as plaintext
    # YAML. Encryption-at-rest and per-client license binding are planned for the
    # embed/on-prem deployment modes; these fields are placeholders until then.
    encrypted: bool = False
    license_id: str | None = None

    # CTX context layer pointers (relative to the pack dir)
    ctx_l2_path: str = "context.ctx"
    ctx_l3_path: str = "index.l3.ctx"
