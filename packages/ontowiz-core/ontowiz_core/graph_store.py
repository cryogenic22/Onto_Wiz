"""
Onto_Wiz Graph Store

The actual reasoning graph with typed nodes and edges.
This is where patterns, entities, and hypotheses live as a traversable structure.

Node Types:
- Entity: Brand, HCP, Payer, Account, Territory
- Metric: TRx, NBRx, Market_Share, etc.
- Signal: Observed changes in metrics
- Observation: Raw data points from sources
- Hypothesis: Potential drivers (Access_Friction, Field_Gap, etc.)
- Evidence: Supporting or contradicting evidence
- Constraint: Guardrails and policy limits
- Action: Recommended interventions

Edge Types:
- SUPPORTS: Evidence -> Hypothesis
- CONTRADICTS: Evidence -> Hypothesis
- REQUIRES_EVIDENCE: Hypothesis -> Evidence (what would confirm/deny)
- BLOCKED_BY: Action -> Constraint
- LEADS_TO: Signal -> Hypothesis, Hypothesis -> Action
- HAS_SOURCE: Signal -> Entity (contribution breakdown)
- TRIGGERS: Signal -> Pattern
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    nx = None


# =============================================================================
# NODE TYPES
# =============================================================================

class NodeType(str, Enum):
    """Types of nodes in the reasoning graph."""
    ENTITY = "entity"           # Brand, HCP, Payer, Account, Territory
    METRIC = "metric"           # TRx, NBRx, Market_Share
    SIGNAL = "signal"           # Observed change (TRx_Drop, PA_Edit)
    OBSERVATION = "observation" # Raw data point
    HYPOTHESIS = "hypothesis"   # Driver/cause (Access_Friction, Field_Gap)
    EVIDENCE = "evidence"       # Supporting/contradicting data
    CONSTRAINT = "constraint"   # Guardrail, policy limit
    ACTION = "action"           # Recommended intervention
    PATTERN = "pattern"         # Judgment pattern reference


class EdgeType(str, Enum):
    """Types of edges connecting nodes."""
    SUPPORTS = "supports"                   # Evidence -> Hypothesis
    CONTRADICTS = "contradicts"             # Evidence -> Hypothesis
    REQUIRES_EVIDENCE = "requires_evidence" # Hypothesis -> Evidence type needed
    BLOCKED_BY = "blocked_by"               # Action -> Constraint
    LEADS_TO = "leads_to"                   # Signal -> Hypothesis, Hypothesis -> Action
    HAS_SOURCE = "has_source"               # Signal -> Entity (contribution)
    TRIGGERS = "triggers"                   # Signal -> Pattern
    BELONGS_TO = "belongs_to"               # Entity -> Entity (hierarchy)
    MEASURES = "measures"                   # Metric -> Entity
    CAUSED_BY = "caused_by"                 # Signal -> Hypothesis (reverse of leads_to)


# =============================================================================
# NODE & EDGE DATA CLASSES
# =============================================================================

@dataclass
class GraphNode:
    """A node in the reasoning graph."""
    id: str = field(default_factory=lambda: str(uuid4()))
    type: NodeType = NodeType.ENTITY
    label: str = ""

    # Node-specific attributes
    properties: dict[str, Any] = field(default_factory=dict)

    # Governance
    source_delta_id: str | None = None  # Which delta created this
    created_at: datetime = field(default_factory=datetime.utcnow)
    confidence: float = 1.0

    # Scope (for filtering)
    geography: str | None = None
    lifecycle: str | None = None
    brand: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for NetworkX storage."""
        return {
            "id": self.id,
            "type": self.type.value,
            "label": self.label,
            "properties": self.properties,
            "source_delta_id": self.source_delta_id,
            "created_at": self.created_at.isoformat(),
            "confidence": self.confidence,
            "geography": self.geography,
            "lifecycle": self.lifecycle,
            "brand": self.brand,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GraphNode":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            type=NodeType(data["type"]),
            label=data["label"],
            properties=data.get("properties", {}),
            source_delta_id=data.get("source_delta_id"),
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data.get("created_at"), str) else data.get("created_at", datetime.utcnow()),
            confidence=data.get("confidence", 1.0),
            geography=data.get("geography"),
            lifecycle=data.get("lifecycle"),
            brand=data.get("brand"),
        )


@dataclass
class GraphEdge:
    """An edge in the reasoning graph."""
    id: str = field(default_factory=lambda: str(uuid4()))
    type: EdgeType = EdgeType.LEADS_TO
    source_id: str = ""
    target_id: str = ""

    # Edge-specific attributes
    properties: dict[str, Any] = field(default_factory=dict)

    # Confidence and evidence
    confidence: float = 1.0
    evidence_ids: list[str] = field(default_factory=list)

    # Governance
    source_delta_id: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for NetworkX storage."""
        return {
            "id": self.id,
            "type": self.type.value,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "properties": self.properties,
            "confidence": self.confidence,
            "evidence_ids": self.evidence_ids,
            "source_delta_id": self.source_delta_id,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GraphEdge":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            type=EdgeType(data["type"]),
            source_id=data["source_id"],
            target_id=data["target_id"],
            properties=data.get("properties", {}),
            confidence=data.get("confidence", 1.0),
            evidence_ids=data.get("evidence_ids", []),
            source_delta_id=data.get("source_delta_id"),
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data.get("created_at"), str) else data.get("created_at", datetime.utcnow()),
        )


# =============================================================================
# GRAPH STORE
# =============================================================================

class GraphStore:
    """
    In-memory graph store using NetworkX.

    This is the actual reasoning graph where:
    - Patterns link to hypotheses
    - Evidence supports/contradicts hypotheses
    - Signals trigger patterns
    - Actions are blocked by constraints
    """

    def __init__(self):
        if not HAS_NETWORKX:
            raise ImportError("NetworkX is required for GraphStore. Install with: pip install networkx")

        self._graph = nx.DiGraph()
        self._nodes: dict[str, GraphNode] = {}
        self._edges: dict[str, GraphEdge] = {}
        self._by_type: dict[NodeType, set[str]] = {t: set() for t in NodeType}
        self._by_label: dict[str, str] = {}  # label -> id (for quick lookup)

    # -------------------------------------------------------------------------
    # Node Operations
    # -------------------------------------------------------------------------

    def add_node(self, node: GraphNode) -> GraphNode:
        """Add a node to the graph."""
        self._nodes[node.id] = node
        self._by_type[node.type].add(node.id)
        if node.label:
            self._by_label[node.label] = node.id

        self._graph.add_node(node.id, **node.to_dict())
        return node

    def get_node(self, node_id: str) -> GraphNode | None:
        """Get a node by ID."""
        return self._nodes.get(node_id)

    def get_node_by_label(self, label: str) -> GraphNode | None:
        """Get a node by label."""
        node_id = self._by_label.get(label)
        return self._nodes.get(node_id) if node_id else None

    def get_nodes_by_type(self, node_type: NodeType) -> list[GraphNode]:
        """Get all nodes of a specific type."""
        return [self._nodes[nid] for nid in self._by_type.get(node_type, set())]

    def update_node(self, node_id: str, **kwargs) -> GraphNode | None:
        """Update node properties."""
        node = self._nodes.get(node_id)
        if not node:
            return None

        for key, value in kwargs.items():
            if hasattr(node, key):
                setattr(node, key, value)

        self._graph.nodes[node_id].update(node.to_dict())
        return node

    def remove_node(self, node_id: str) -> bool:
        """Remove a node and all its edges."""
        node = self._nodes.get(node_id)
        if not node:
            return False

        # Remove from indexes
        self._by_type[node.type].discard(node_id)
        if node.label in self._by_label:
            del self._by_label[node.label]

        # Remove edges connected to this node
        edges_to_remove = [
            eid for eid, edge in self._edges.items()
            if edge.source_id == node_id or edge.target_id == node_id
        ]
        for eid in edges_to_remove:
            del self._edges[eid]

        # Remove from graph
        self._graph.remove_node(node_id)
        del self._nodes[node_id]

        return True

    # -------------------------------------------------------------------------
    # Edge Operations
    # -------------------------------------------------------------------------

    def add_edge(self, edge: GraphEdge) -> GraphEdge:
        """Add an edge to the graph."""
        if edge.source_id not in self._nodes or edge.target_id not in self._nodes:
            raise ValueError(f"Source or target node not found: {edge.source_id} -> {edge.target_id}")

        self._edges[edge.id] = edge
        self._graph.add_edge(
            edge.source_id,
            edge.target_id,
            key=edge.id,
            **edge.to_dict()
        )
        return edge

    def get_edge(self, edge_id: str) -> GraphEdge | None:
        """Get an edge by ID."""
        return self._edges.get(edge_id)

    def get_edges_from(self, node_id: str, edge_type: EdgeType | None = None) -> list[GraphEdge]:
        """Get all outgoing edges from a node."""
        edges = [e for e in self._edges.values() if e.source_id == node_id]
        if edge_type:
            edges = [e for e in edges if e.type == edge_type]
        return edges

    def get_edges_to(self, node_id: str, edge_type: EdgeType | None = None) -> list[GraphEdge]:
        """Get all incoming edges to a node."""
        edges = [e for e in self._edges.values() if e.target_id == node_id]
        if edge_type:
            edges = [e for e in edges if e.type == edge_type]
        return edges

    def remove_edge(self, edge_id: str) -> bool:
        """Remove an edge."""
        edge = self._edges.get(edge_id)
        if not edge:
            return False

        self._graph.remove_edge(edge.source_id, edge.target_id, key=edge_id)
        del self._edges[edge_id]
        return True

    # -------------------------------------------------------------------------
    # Traversal Operations
    # -------------------------------------------------------------------------

    def get_neighbors(
        self,
        node_id: str,
        direction: str = "out",  # "in", "out", "both"
        edge_types: list[EdgeType] | None = None
    ) -> list[GraphNode]:
        """Get neighboring nodes."""
        neighbors = set()

        if direction in ("out", "both"):
            for edge in self.get_edges_from(node_id, None):
                if edge_types is None or edge.type in edge_types:
                    neighbors.add(edge.target_id)

        if direction in ("in", "both"):
            for edge in self.get_edges_to(node_id, None):
                if edge_types is None or edge.type in edge_types:
                    neighbors.add(edge.source_id)

        return [self._nodes[nid] for nid in neighbors if nid in self._nodes]

    def find_path(
        self,
        start_id: str,
        end_id: str,
        max_depth: int = 5
    ) -> list[GraphNode] | None:
        """Find a path between two nodes."""
        try:
            path_ids = nx.shortest_path(self._graph, start_id, end_id)
            if len(path_ids) > max_depth:
                return None
            return [self._nodes[nid] for nid in path_ids]
        except nx.NetworkXNoPath:
            return None

    def get_subgraph(
        self,
        center_id: str,
        radius: int = 2
    ) -> tuple[list[GraphNode], list[GraphEdge]]:
        """Get a subgraph around a center node."""
        visited = set()
        frontier = {center_id}

        for _ in range(radius):
            new_frontier = set()
            for nid in frontier:
                if nid not in visited:
                    visited.add(nid)
                    neighbors = self.get_neighbors(nid, direction="both")
                    new_frontier.update(n.id for n in neighbors)
            frontier = new_frontier

        visited.update(frontier)

        nodes = [self._nodes[nid] for nid in visited if nid in self._nodes]
        edges = [
            e for e in self._edges.values()
            if e.source_id in visited and e.target_id in visited
        ]

        return nodes, edges

    # -------------------------------------------------------------------------
    # Query Operations
    # -------------------------------------------------------------------------

    def find_hypotheses_for_signal(self, signal_id: str) -> list[tuple[GraphNode, float]]:
        """
        Find hypotheses (drivers) that could explain a signal.
        Returns list of (hypothesis, confidence) tuples.
        """
        hypotheses = []

        # Direct edges: Signal -> Hypothesis via LEADS_TO or CAUSED_BY
        for edge in self.get_edges_from(signal_id):
            if edge.type in (EdgeType.LEADS_TO, EdgeType.CAUSED_BY):
                target = self.get_node(edge.target_id)
                if target and target.type == NodeType.HYPOTHESIS:
                    hypotheses.append((target, edge.confidence))

        return sorted(hypotheses, key=lambda x: x[1], reverse=True)

    def find_evidence_for_hypothesis(self, hypothesis_id: str) -> dict[str, list[GraphNode]]:
        """
        Find evidence supporting or contradicting a hypothesis.
        Returns {"supporting": [...], "contradicting": [...]}.
        """
        result = {"supporting": [], "contradicting": []}

        for edge in self.get_edges_to(hypothesis_id):
            source = self.get_node(edge.source_id)
            if source and source.type == NodeType.EVIDENCE:
                if edge.type == EdgeType.SUPPORTS:
                    result["supporting"].append(source)
                elif edge.type == EdgeType.CONTRADICTS:
                    result["contradicting"].append(source)

        return result

    def find_actions_for_hypothesis(self, hypothesis_id: str) -> list[GraphNode]:
        """Find recommended actions for a hypothesis."""
        actions = []
        for edge in self.get_edges_from(hypothesis_id, EdgeType.LEADS_TO):
            target = self.get_node(edge.target_id)
            if target and target.type == NodeType.ACTION:
                actions.append(target)
        return actions

    def find_constraints_for_action(self, action_id: str) -> list[GraphNode]:
        """Find constraints/guardrails blocking an action."""
        constraints = []
        for edge in self.get_edges_from(action_id, EdgeType.BLOCKED_BY):
            target = self.get_node(edge.target_id)
            if target and target.type == NodeType.CONSTRAINT:
                constraints.append(target)
        return constraints

    # -------------------------------------------------------------------------
    # Stats & Export
    # -------------------------------------------------------------------------

    def stats(self) -> dict[str, Any]:
        """Get graph statistics."""
        return {
            "total_nodes": len(self._nodes),
            "total_edges": len(self._edges),
            "nodes_by_type": {t.value: len(ids) for t, ids in self._by_type.items()},
            "is_dag": nx.is_directed_acyclic_graph(self._graph) if self._graph.number_of_nodes() > 0 else True,
        }

    def export_to_dict(self) -> dict[str, Any]:
        """Export entire graph to dictionary."""
        return {
            "nodes": [n.to_dict() for n in self._nodes.values()],
            "edges": [e.to_dict() for e in self._edges.values()],
        }

    def import_from_dict(self, data: dict[str, Any]) -> None:
        """Import graph from dictionary."""
        for node_data in data.get("nodes", []):
            node = GraphNode.from_dict(node_data)
            self.add_node(node)

        for edge_data in data.get("edges", []):
            edge = GraphEdge.from_dict(edge_data)
            self.add_edge(edge)

    # -------------------------------------------------------------------------
    # Seed with Base Ontology
    # -------------------------------------------------------------------------

    def seed_commercial_ontology(self) -> None:
        """
        Seed the graph with core commercial pharma ontology.
        This creates the base structure that patterns attach to.
        """
        # Core Hypotheses (Drivers)
        drivers = [
            ("Access_Friction", "Payer/formulary barriers limiting patient access"),
            ("Field_Execution_Gap", "Sales force coverage or messaging issues"),
            ("Demand_Erosion", "Market/competitive pressure reducing demand"),
            ("Competitor_Displacement", "Competitor taking share"),
            ("Pricing_Pressure", "Price-driven barriers"),
            ("Supply_Disruption", "Distribution or inventory issues"),
            ("Safety_Signal", "Emerging safety concerns"),
            ("Efficacy_Perception", "HCP perception of efficacy vs alternatives"),
            ("Market_Dynamics", "Macro market changes"),
            ("Seasonal_Pattern", "Expected seasonal variation"),
        ]

        for label, description in drivers:
            self.add_node(GraphNode(
                type=NodeType.HYPOTHESIS,
                label=label,
                properties={"description": description},
                confidence=1.0,
            ))

        # Core Signals
        signals = [
            ("TRx_Drop", "Total prescriptions decline"),
            ("NBRx_Drop", "New prescriptions decline"),
            ("Market_Share_Loss", "Declining market share"),
            ("PA_Edit_Increase", "Prior authorization edits increasing"),
            ("Abandonment_Rate_Up", "Prescription abandonment increasing"),
            ("Fill_Rate_Down", "Fill rate declining"),
            ("Call_Activity_Low", "Field sales activity below target"),
            ("Win_Rate_Down", "Competitive win rate declining"),
        ]

        for label, description in signals:
            self.add_node(GraphNode(
                type=NodeType.SIGNAL,
                label=label,
                properties={"description": description},
            ))

        # Core Signal -> Hypothesis edges (common relationships)
        common_relationships = [
            ("TRx_Drop", "Access_Friction", 0.7),
            ("TRx_Drop", "Field_Execution_Gap", 0.5),
            ("TRx_Drop", "Competitor_Displacement", 0.6),
            ("NBRx_Drop", "Field_Execution_Gap", 0.7),
            ("NBRx_Drop", "Demand_Erosion", 0.5),
            ("PA_Edit_Increase", "Access_Friction", 0.9),
            ("Abandonment_Rate_Up", "Access_Friction", 0.8),
            ("Abandonment_Rate_Up", "Pricing_Pressure", 0.7),
            ("Market_Share_Loss", "Competitor_Displacement", 0.8),
            ("Market_Share_Loss", "Efficacy_Perception", 0.5),
            ("Call_Activity_Low", "Field_Execution_Gap", 0.9),
            ("Win_Rate_Down", "Competitor_Displacement", 0.7),
            ("Win_Rate_Down", "Efficacy_Perception", 0.6),
        ]

        for signal_label, hypothesis_label, confidence in common_relationships:
            signal = self.get_node_by_label(signal_label)
            hypothesis = self.get_node_by_label(hypothesis_label)
            if signal and hypothesis:
                self.add_edge(GraphEdge(
                    type=EdgeType.LEADS_TO,
                    source_id=signal.id,
                    target_id=hypothesis.id,
                    confidence=confidence,
                ))

        print(f"Seeded graph with {len(drivers)} hypotheses, {len(signals)} signals, {len(common_relationships)} edges")
