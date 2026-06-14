"""C6 — annotations/comments store (governed discussion on an artifact)."""

from __future__ import annotations

from ontowiz_runtime import CommentStore


def test_add_and_list_in_order(tmp_path):
    store = CommentStore(tmp_path)
    store.add("commercial_analytics", "0.3.0", "rule_formulary_exclusion",
              author="Priya", role="sme", text="payer-driven, agreed", at="2026-06-14T10:00:00Z")
    store.add("commercial_analytics", "0.3.0", "rule_formulary_exclusion",
              author="Tom", role="curator", text="approved D-1182", at="2026-06-14T10:05:00Z")

    got = store.list("commercial_analytics", "0.3.0", "rule_formulary_exclusion")
    assert [c.author for c in got] == ["Priya", "Tom"]
    assert got[0].role == "sme" and got[0].text == "payer-driven, agreed"
    assert got[1].created_at == "2026-06-14T10:05:00Z"


def test_comments_are_scoped_per_artifact_and_version(tmp_path):
    store = CommentStore(tmp_path)
    store.add("p", "0.1.0", "a1", author="x", role="sme", text="one")
    assert store.list("p", "0.1.0", "a2") == []        # different artifact
    assert store.list("p", "0.2.0", "a1") == []        # different version
    assert len(store.list("p", "0.1.0", "a1")) == 1


def test_comments_persist_across_store_instances(tmp_path):
    CommentStore(tmp_path).add("p", "0.1.0", "a1", author="x", role="sme", text="durable")
    # a fresh store over the same root reads what the first persisted
    assert CommentStore(tmp_path).list("p", "0.1.0", "a1")[0].text == "durable"
