"""
Unit Tests for GraphStore and EvidenceStore

Tests the reasoning graph and evidence management.
"""

import pytest
from datetime import datetime, timedelta

from src.core import (
    # Graph
    GraphStore, GraphNode, GraphEdge, NodeType, EdgeType,
    # Evidence
    EvidenceStore, EvidenceItem, EvidencePointer, ExtractedClaim,
    EvidenceType, ReliabilityClass, SourceSystem,
)


# =============================================================================
# GRAPH STORE TESTS
# =============================================================================

class TestGraphStore:
    """Tests for the GraphStore."""
    
    def test_create_graph_store(self):
        """GraphStore should initialize empty."""
        store = GraphStore()
        stats = store.stats()
        
        assert stats["total_nodes"] == 0
        assert stats["total_edges"] == 0
    
    def test_add_node(self):
        """Should add nodes to the graph."""
        store = GraphStore()
        
        node = GraphNode(
            type=NodeType.HYPOTHESIS,
            label="Access_Friction",
            properties={"description": "Payer barriers"}
        )
        
        result = store.add_node(node)
        
        assert result.id == node.id
        assert store.get_node(node.id) is not None
    
    def test_get_node_by_label(self):
        """Should retrieve nodes by label."""
        store = GraphStore()
        store.add_node(GraphNode(type=NodeType.SIGNAL, label="TRx_Drop"))
        
        result = store.get_node_by_label("TRx_Drop")
        
        assert result is not None
        assert result.label == "TRx_Drop"
    
    def test_add_edge(self):
        """Should add edges between nodes."""
        store = GraphStore()
        
        signal = store.add_node(GraphNode(type=NodeType.SIGNAL, label="TRx_Drop"))
        hypothesis = store.add_node(GraphNode(type=NodeType.HYPOTHESIS, label="Access_Friction"))
        
        edge = GraphEdge(
            type=EdgeType.LEADS_TO,
            source_id=signal.id,
            target_id=hypothesis.id,
            confidence=0.75
        )
        
        result = store.add_edge(edge)
        
        assert result.id == edge.id
        assert store.get_edge(edge.id) is not None
    
    def test_edge_requires_valid_nodes(self):
        """Should fail if edge references non-existent nodes."""
        store = GraphStore()
        
        edge = GraphEdge(
            type=EdgeType.LEADS_TO,
            source_id="fake_source",
            target_id="fake_target"
        )
        
        with pytest.raises(ValueError):
            store.add_edge(edge)
    
    def test_get_neighbors(self):
        """Should find neighboring nodes."""
        store = GraphStore()
        
        signal = store.add_node(GraphNode(type=NodeType.SIGNAL, label="TRx_Drop"))
        hyp1 = store.add_node(GraphNode(type=NodeType.HYPOTHESIS, label="Access_Friction"))
        hyp2 = store.add_node(GraphNode(type=NodeType.HYPOTHESIS, label="Field_Gap"))
        
        store.add_edge(GraphEdge(type=EdgeType.LEADS_TO, source_id=signal.id, target_id=hyp1.id))
        store.add_edge(GraphEdge(type=EdgeType.LEADS_TO, source_id=signal.id, target_id=hyp2.id))
        
        neighbors = store.get_neighbors(signal.id, direction="out")
        
        assert len(neighbors) == 2
    
    def test_find_hypotheses_for_signal(self):
        """Should find ranked hypotheses for a signal."""
        store = GraphStore()
        
        signal = store.add_node(GraphNode(type=NodeType.SIGNAL, label="TRx_Drop"))
        hyp1 = store.add_node(GraphNode(type=NodeType.HYPOTHESIS, label="Access_Friction"))
        hyp2 = store.add_node(GraphNode(type=NodeType.HYPOTHESIS, label="Field_Gap"))
        
        store.add_edge(GraphEdge(type=EdgeType.LEADS_TO, source_id=signal.id, target_id=hyp1.id, confidence=0.8))
        store.add_edge(GraphEdge(type=EdgeType.LEADS_TO, source_id=signal.id, target_id=hyp2.id, confidence=0.5))
        
        hypotheses = store.find_hypotheses_for_signal(signal.id)
        
        assert len(hypotheses) == 2
        assert hypotheses[0][0].label == "Access_Friction"  # Higher confidence first
        assert hypotheses[0][1] == 0.8
    
    def test_seed_commercial_ontology(self):
        """Should seed with base commercial ontology."""
        store = GraphStore()
        store.seed_commercial_ontology()
        
        stats = store.stats()
        
        assert stats["total_nodes"] >= 15  # At least 10 hypotheses + signals
        assert stats["total_edges"] >= 10  # Multiple relationships
        
        # Check specific nodes exist
        assert store.get_node_by_label("Access_Friction") is not None
        assert store.get_node_by_label("TRx_Drop") is not None
    
    def test_subgraph_extraction(self):
        """Should extract subgraph around a center node."""
        store = GraphStore()
        store.seed_commercial_ontology()
        
        trx_drop = store.get_node_by_label("TRx_Drop")
        nodes, edges = store.get_subgraph(trx_drop.id, radius=1)
        
        assert len(nodes) > 1  # At least the center + neighbors
        assert len(edges) > 0  # At least one edge
    
    def test_find_path(self):
        """Should find path between nodes."""
        store = GraphStore()
        
        a = store.add_node(GraphNode(label="A"))
        b = store.add_node(GraphNode(label="B"))
        c = store.add_node(GraphNode(label="C"))
        
        store.add_edge(GraphEdge(source_id=a.id, target_id=b.id))
        store.add_edge(GraphEdge(source_id=b.id, target_id=c.id))
        
        path = store.find_path(a.id, c.id)
        
        assert path is not None
        assert len(path) == 3


# =============================================================================
# EVIDENCE STORE TESTS
# =============================================================================

class TestEvidenceStore:
    """Tests for the EvidenceStore."""
    
    def test_create_evidence_store(self):
        """EvidenceStore should initialize empty."""
        store = EvidenceStore()
        stats = store.stats()
        
        assert stats["total"] == 0
    
    def test_add_evidence(self):
        """Should add evidence items."""
        store = EvidenceStore()
        
        evidence = EvidenceItem(
            type=EvidenceType.DOCUMENT,
            reliability=ReliabilityClass.SOFT,
            source_system=SourceSystem.FIELD_NOTES,
            content="HCP mentioned budget constraints",
            entity_refs=["University_Hospital_Bonn"]
        )
        
        result = store.add(evidence)
        
        assert result.id == evidence.id
        assert store.get(evidence.id) is not None
    
    def test_deduplication_by_hash(self):
        """Should deduplicate evidence by content hash."""
        store = EvidenceStore()
        
        ev1 = EvidenceItem(content="Same content here")
        ev2 = EvidenceItem(content="Same content here")
        
        result1 = store.add(ev1)
        result2 = store.add(ev2)
        
        # Should return the same evidence (deduped)
        assert result1.id == result2.id
        assert store.stats()["total"] == 1
    
    def test_reliability_weight(self):
        """Should return correct reliability weights."""
        hard = EvidenceItem(reliability=ReliabilityClass.HARD)
        soft = EvidenceItem(reliability=ReliabilityClass.SOFT)
        rumor = EvidenceItem(reliability=ReliabilityClass.RUMOR)
        
        assert hard.reliability_weight() == 1.0
        assert soft.reliability_weight() == 0.6
        assert rumor.reliability_weight() == 0.2
    
    def test_find_by_type(self):
        """Should find evidence by type."""
        store = EvidenceStore()
        
        store.add(EvidenceItem(type=EvidenceType.METRIC, content="TRx: 100"))
        store.add(EvidenceItem(type=EvidenceType.METRIC, content="NBRx: 50"))
        store.add(EvidenceItem(type=EvidenceType.DOCUMENT, content="Field note"))
        
        metrics = store.find_by_type(EvidenceType.METRIC)
        
        assert len(metrics) == 2
    
    def test_find_by_reliability(self):
        """Should find evidence by reliability class."""
        store = EvidenceStore()
        
        store.add(EvidenceItem(reliability=ReliabilityClass.HARD, content="Claims data"))
        store.add(EvidenceItem(reliability=ReliabilityClass.SOFT, content="Field note"))
        store.add(EvidenceItem(reliability=ReliabilityClass.RUMOR, content="Competitor intel"))
        
        hard = store.find_hard_evidence()
        
        assert len(hard) == 1
    
    def test_find_by_entity(self):
        """Should find evidence by entity reference."""
        store = EvidenceStore()
        
        store.add(EvidenceItem(content="Note 1", entity_refs=["Hospital_A", "Hospital_B"]))
        store.add(EvidenceItem(content="Note 2", entity_refs=["Hospital_A"]))
        store.add(EvidenceItem(content="Note 3", entity_refs=["Hospital_C"]))
        
        results = store.find_by_entity("Hospital_A")
        
        assert len(results) == 2
    
    def test_evidence_pointer(self):
        """Should create valid evidence pointers."""
        evidence = EvidenceItem(
            reliability=ReliabilityClass.HARD,
            content="TRx declined 6%"
        )
        evidence.add_claim("TRx declined 6% in Q4", claim_type="assertion")
        
        pointer = evidence.get_pointer(claim_id=evidence.claims[0].id)
        
        assert pointer.evidence_id == evidence.id
        assert pointer.claim_id == evidence.claims[0].id
        assert pointer.confidence == 1.0  # HARD reliability
    
    def test_add_metric_helper(self):
        """Should add metric evidence via helper."""
        store = EvidenceStore()
        
        result = store.add_metric_evidence(
            metric="TRx",
            value=-0.06,
            time_period="2026-Q1",
            entity_refs=["Brand_X", "Midwest_Region"]
        )
        
        assert result.type == EvidenceType.METRIC
        assert result.reliability == ReliabilityClass.HARD
        assert "TRx" in result.metric_refs
    
    def test_add_field_note_helper(self):
        """Should add field note via helper."""
        store = EvidenceStore()
        
        result = store.add_field_note(
            content="HCP mentioned budget concerns",
            collected_by="rep_123",
            entity_refs=["Dr_Smith"],
            brand="Oncovance"
        )
        
        assert result.type == EvidenceType.DOCUMENT
        assert result.reliability == ReliabilityClass.SOFT
        assert result.brand == "Oncovance"
    
    def test_add_competitor_intel_helper(self):
        """Should add competitor intel as RUMOR."""
        store = EvidenceStore()
        
        result = store.add_competitor_intel(
            content="Competitor may be offering discounts",
            source_uri="internal_memo"
        )
        
        assert result.reliability == ReliabilityClass.RUMOR
        assert result.source_system == SourceSystem.COMPETITOR_INTEL
    
    def test_permission_filtering(self):
        """Should filter evidence by permissions."""
        store = EvidenceStore()
        
        store.add(EvidenceItem(content="Public data", permission_tags=["public"]))
        store.add(EvidenceItem(content="Team only", permission_tags=["team_alpha"]))
        store.add(EvidenceItem(content="Exec only", permission_tags=["executive"]))
        
        team_results = store.find_with_permissions(required_tags=["public", "team_alpha"])
        
        assert len(team_results) == 2  # Public + team_alpha


# =============================================================================
# CTX-019: SEMANTIC EVIDENCE SEARCH TESTS
# =============================================================================

class TestSemanticEvidenceSearch:
    """Tests for semantic search over evidence (CTX-019)."""

    def _seeded_semantic_store(self):
        """Create a SemanticStore with a few synonyms for testing."""
        from src.core.semantic_store import SemanticStore, CanonicalTerm, FunctionalDomain
        ss = SemanticStore()
        pa = ss.add_canonical_term(CanonicalTerm(
            term="Prior_Authorization",
            domains=[FunctionalDomain.COMMERCIAL],
        ))
        ss.add_synonym("PA", pa.id)
        ss.add_synonym("Prior Auth", pa.id)
        return ss

    def test_search_by_text_title(self):
        """search_by_text should match title substring."""
        store = EvidenceStore()
        e = store.add(EvidenceItem(
            title="Prior Authorization delays in Q1",
            content="Patients waiting 7+ days for PA.",
        ))
        results = store.search_by_text("Prior Authorization")
        assert len(results) == 1
        assert results[0].id == e.id

    def test_search_by_text_content(self):
        """search_by_text should match content substring."""
        store = EvidenceStore()
        store.add(EvidenceItem(
            title="Field Report",
            content="Noticed increased prior authorization friction.",
        ))
        results = store.search_by_text("prior authorization")
        assert len(results) == 1

    def test_search_by_text_no_match(self):
        """search_by_text should return empty for no match."""
        store = EvidenceStore()
        store.add(EvidenceItem(title="Report", content="Nothing relevant"))
        results = store.search_by_text("biosimilar")
        assert len(results) == 0

    def test_semantic_find_evidence_via_synonym(self):
        """Semantic search for 'PA' should find evidence with 'Prior_Authorization' entity ref."""
        ss = self._seeded_semantic_store()
        store = EvidenceStore()
        store.add(EvidenceItem(
            title="Access Report",
            content="Access barriers detected",
            entity_refs=["Prior_Authorization"],
            reliability=ReliabilityClass.HARD,
        ))
        results = store.semantic_find_evidence("PA", ss)
        assert len(results) == 1

    def test_semantic_find_evidence_via_text(self):
        """Semantic search should find evidence by expanded term in content."""
        ss = self._seeded_semantic_store()
        store = EvidenceStore()
        store.add(EvidenceItem(
            title="Field Note",
            content="Prior Auth is causing delays in oncology.",
            reliability=ReliabilityClass.SOFT,
        ))
        # Search with canonical term — "Prior Auth" is a variant
        results = store.semantic_find_evidence("Prior_Authorization", ss)
        assert len(results) == 1

    def test_semantic_find_evidence_no_false_positives(self):
        """Unrelated terms should not match after expansion."""
        ss = self._seeded_semantic_store()
        store = EvidenceStore()
        store.add(EvidenceItem(
            title="Supply Report",
            content="Shipment delays at warehouse.",
            entity_refs=["Supply_Chain"],
        ))
        results = store.semantic_find_evidence("PA", ss)
        assert len(results) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
