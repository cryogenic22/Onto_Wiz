"""
YAML-backed few-shot example store.

Loads/saves FewShotExample instances from knowledge_base/few_shots/*.yaml.
Follows the JudgmentStore find/rank pattern from src/core/stores.py.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from src.core.models import ArtifactStatus

from .models import FewShotExample

logger = logging.getLogger(__name__)


class FewShotStore:
    """Repository for curated few-shot examples, backed by YAML files."""

    def __init__(self, base_path: Path) -> None:
        self._base_path = base_path
        self._examples: Dict[str, FewShotExample] = {}
        self.load_all()

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_all(self) -> None:
        """Load all YAML files from base_path. Malformed files are skipped with a warning."""
        self._examples.clear()
        if not self._base_path.exists():
            logger.warning("Few-shot directory does not exist: %s", self._base_path)
            return

        for yaml_path in sorted(self._base_path.glob("*.yaml")):
            try:
                with open(yaml_path, "r", encoding="utf-8") as f:
                    raw = yaml.safe_load(f)
                if raw is None:
                    continue
                # Support both single-example and list-of-examples YAML files
                items = raw if isinstance(raw, list) else [raw]
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    example = FewShotExample.from_dict(item)
                    self._examples[example.id] = example
            except (yaml.YAMLError, OSError, TypeError, ValueError) as exc:
                logger.warning("Skipping malformed YAML %s: %s", yaml_path.name, exc)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add(self, example: FewShotExample) -> FewShotExample:
        """Add an example to the in-memory store and persist to YAML."""
        self._examples[example.id] = example
        self._persist(example)
        return example

    def get(self, example_id: str) -> Optional[FewShotExample]:
        """Get example by ID."""
        return self._examples.get(example_id)

    def get_all(self) -> List[FewShotExample]:
        """Return all loaded examples."""
        return list(self._examples.values())

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def find_by_task_type(
        self,
        task_type: str,
        limit: int = 5,
        include_non_approved: bool = False,
    ) -> List[FewShotExample]:
        """Find examples by task type, ranked by quality_score descending."""
        matches = [
            ex
            for ex in self._examples.values()
            if ex.task_type.lower() == task_type.lower()
            and (include_non_approved or ex.status == ArtifactStatus.APPROVED)
        ]
        matches.sort(key=lambda ex: ex.quality_score, reverse=True)
        return matches[:limit]

    def find_by_tags(
        self,
        tags: Dict[str, List[str]],
        limit: int = 5,
        include_non_approved: bool = False,
    ) -> List[FewShotExample]:
        """
        Find examples matching tags. Case-insensitive tag matching.

        An example matches if for every requested tag key, it has at least one
        overlapping value.
        """
        if not tags:
            return []

        def _matches(example: FewShotExample) -> bool:
            if not include_non_approved and example.status != ArtifactStatus.APPROVED:
                return False
            for key, values in tags.items():
                ex_values = example.tags.get(key, [])
                ex_lower = {v.lower() for v in ex_values}
                req_lower = {v.lower() for v in values}
                if not ex_lower & req_lower:
                    return False
            return True

        matches = [ex for ex in self._examples.values() if _matches(ex)]
        matches.sort(key=lambda ex: ex.quality_score, reverse=True)
        return matches[:limit]

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> Dict[str, int]:
        """Return store statistics."""
        by_status: Dict[str, int] = {}
        for ex in self._examples.values():
            by_status[ex.status.value] = by_status.get(ex.status.value, 0) + 1
        return {
            "total": len(self._examples),
            **by_status,
        }

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _persist(self, example: FewShotExample) -> None:
        """Save a single example to its own YAML file."""
        self._base_path.mkdir(parents=True, exist_ok=True)
        filename = f"{example.id}.yaml"
        filepath = self._base_path / filename
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(example.to_dict(), f, default_flow_style=False, sort_keys=False)
