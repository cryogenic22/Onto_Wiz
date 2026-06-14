"""Tests for FewShotStore."""

import tempfile
from pathlib import Path

import pytest
import yaml

from src.core.models import ArtifactStatus
from src.knowledge.models import FewShotExample
from src.knowledge.few_shot_store import FewShotStore


@pytest.fixture
def tmp_dir(tmp_path):
    return tmp_path / "few_shots"


@pytest.fixture
def store_with_examples(tmp_dir):
    """Create a store with pre-seeded YAML examples."""
    tmp_dir.mkdir(parents=True, exist_ok=True)

    examples = [
        {
            "id": "ex-001",
            "task_type": "driver_attribution",
            "input_text": "NBRx drop in oncology",
            "output_text": "Driver: Access_Friction",
            "tags": {"therapeutic_area": ["oncology"], "signal_type": ["NBRx_Drop"]},
            "quality_score": 0.95,
            "status": "approved",
            "created_at": "2025-11-15T10:00:00",
            "version": "1.0.0",
        },
        {
            "id": "ex-002",
            "task_type": "driver_attribution",
            "input_text": "TRx decline in immunology",
            "output_text": "Driver: Field_Gap",
            "tags": {"therapeutic_area": ["immunology"], "signal_type": ["TRx_Drop"]},
            "quality_score": 0.80,
            "status": "approved",
            "created_at": "2025-11-20T10:00:00",
            "version": "1.0.0",
        },
        {
            "id": "ex-003",
            "task_type": "signal_interpretation",
            "input_text": "PA edit increase",
            "output_text": "Signal: PA_Edit_Increase",
            "tags": {"signal_type": ["PA_Edit_Increase"]},
            "quality_score": 0.90,
            "status": "draft",
            "created_at": "2025-12-01T10:00:00",
            "version": "1.0.0",
        },
    ]

    with open(tmp_dir / "test_examples.yaml", "w") as f:
        yaml.dump(examples, f)

    return FewShotStore(tmp_dir)


class TestFewShotStore:
    def test_load_all_from_yaml(self, store_with_examples):
        """Should load all examples from YAML files."""
        assert len(store_with_examples.get_all()) == 3

    def test_empty_dir(self, tmp_dir):
        """Empty directory should produce empty store."""
        tmp_dir.mkdir(parents=True, exist_ok=True)
        store = FewShotStore(tmp_dir)
        assert store.get_all() == []

    def test_nonexistent_dir(self, tmp_path):
        """Non-existent directory should produce empty store without error."""
        store = FewShotStore(tmp_path / "does_not_exist")
        assert store.get_all() == []

    def test_malformed_yaml_skipped(self, tmp_dir):
        """Malformed YAML should be skipped with a warning."""
        tmp_dir.mkdir(parents=True, exist_ok=True)
        with open(tmp_dir / "bad.yaml", "w") as f:
            f.write("{{{{invalid yaml")
        store = FewShotStore(tmp_dir)
        assert store.get_all() == []

    def test_find_by_task_type(self, store_with_examples):
        """Should find examples by task type, only APPROVED."""
        results = store_with_examples.find_by_task_type("driver_attribution")
        assert len(results) == 2
        # Sorted by quality_score descending
        assert results[0].id == "ex-001"
        assert results[1].id == "ex-002"

    def test_find_by_task_type_case_insensitive(self, store_with_examples):
        results = store_with_examples.find_by_task_type("DRIVER_ATTRIBUTION")
        assert len(results) == 2

    def test_find_by_task_type_excludes_drafts(self, store_with_examples):
        """Draft examples should be excluded by default."""
        results = store_with_examples.find_by_task_type("signal_interpretation")
        assert len(results) == 0

    def test_find_by_task_type_include_non_approved(self, store_with_examples):
        results = store_with_examples.find_by_task_type(
            "signal_interpretation", include_non_approved=True
        )
        assert len(results) == 1

    def test_find_by_tags(self, store_with_examples):
        """Should match examples with overlapping tag values."""
        results = store_with_examples.find_by_tags(
            {"therapeutic_area": ["oncology"]}
        )
        assert len(results) == 1
        assert results[0].id == "ex-001"

    def test_find_by_tags_case_insensitive(self, store_with_examples):
        results = store_with_examples.find_by_tags(
            {"therapeutic_area": ["ONCOLOGY"]}
        )
        assert len(results) == 1

    def test_find_by_tags_empty(self, store_with_examples):
        """Empty tags dict should return empty list."""
        results = store_with_examples.find_by_tags({})
        assert results == []

    def test_find_by_tags_limit(self, store_with_examples):
        results = store_with_examples.find_by_tags(
            {"signal_type": ["NBRx_Drop", "TRx_Drop"]}, limit=1
        )
        assert len(results) <= 1

    def test_add_and_persist(self, tmp_dir):
        """Adding an example should persist it to YAML."""
        tmp_dir.mkdir(parents=True, exist_ok=True)
        store = FewShotStore(tmp_dir)

        example = FewShotExample(
            id="new-001",
            task_type="test_task",
            input_text="test input",
            output_text="test output",
            quality_score=0.9,
            status=ArtifactStatus.APPROVED,
        )
        store.add(example)

        assert store.get("new-001") is not None
        # Verify file was created
        assert (tmp_dir / "new-001.yaml").exists()

        # Reload and verify persistence
        store2 = FewShotStore(tmp_dir)
        assert store2.get("new-001") is not None

    def test_stats(self, store_with_examples):
        stats = store_with_examples.stats()
        assert stats["total"] == 3
        assert stats.get("approved", 0) == 2
        assert stats.get("draft", 0) == 1
