"""Onto_Wiz API - Enterprise Judgment Layer"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional, Tuple
import yaml
import os
import uvicorn
from pathlib import Path
from datetime import datetime

from src.reasoning.engine import ReasoningEngine, ScenarioContext
from src.core import (
    Delta, DeltaType, DeltaStatus, BlastRadius,
    JudgmentPattern, Guardrail, ArtifactStatus, Governance, DriverAttribution,
    DeltaStore, JudgmentStore, PromotionPipeline,
    IntelligencePacket, DriverResult, ActionRecommendation,
    route_delta,
    ContributionStore,
)
from src.api.schemas import (
    DeltaCreate, DeltaResponse, DeltaApprove, DeltaReject, DeltaListResponse,
    JudgmentPatternCreate, JudgmentPatternResponse,
    GuardrailCreate, GuardrailResponse,
    IntelligencePacketRequest, IntelligencePacketResponse,
    DriverResultAPI, ActionRecommendationAPI,
    DriverAttributionAPI, StoreStats, HealthResponse,
    DeltaTypeAPI, DeltaStatusAPI, BlastRadiusAPI, ArtifactStatusAPI,
    LegacyReasonRequest, LegacyReasonResponse,
    GameSessionCreate, GameSessionResponse, GameSessionSummary, GameSessionDetail,
    ReviewQueueItem, QueueStatsResponse, EscalateRequest, AuditEntryResponse,
    ContributionResponse, ContributorSummaryResponse, ContributionStatsResponse,
)
from src.core.reasoning_event import (
    ReasoningEvent, BrandProfile, ScenarioContext as REScenarioContext,
    HypothesisCategory, HypothesisRanking, SignalPriority as RESignalPriority,
    DisconfirmingLogic, PatternRecognition, CommonMistake, RecommendedAction,
)
from src.core.delta_generator import process_sme_session
from src.core.semantic_store import SemanticStore
from src.core.graph_store import GraphStore
from src.knowledge.few_shot_store import FewShotStore
from src.knowledge.assembler import ContextAssembler
from src.knowledge.api_routes import router as knowledge_router, init_knowledge_routes

class ReasoningEventStore:
    """In-memory store for ReasoningEvents from game sessions."""

    def __init__(self):
        self._events: Dict[str, ReasoningEvent] = {}

    def add(self, event: ReasoningEvent) -> ReasoningEvent:
        self._events[event.id] = event
        return event

    def get(self, event_id: str) -> Optional[ReasoningEvent]:
        return self._events.get(event_id)

    def list_all(self) -> List[ReasoningEvent]:
        return list(self._events.values())


app = FastAPI(
    title="Onto_Wiz API",
    description="Enterprise Judgment Layer for Agentic AI",
    version="2.0.0"
)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_PATH = Path("ontology/synthetic_data/compellium_pharma.yaml")
ONTOLOGY_PATH = Path("ontology/commercial.yaml")

# Initialize Stores (singleton)
delta_store = DeltaStore()
judgment_store = JudgmentStore()
reasoning_event_store = ReasoningEventStore()
contribution_store = ContributionStore()
promotion_pipeline = PromotionPipeline(delta_store, judgment_store)

# Initialize Knowledge Module
semantic_store = SemanticStore()
semantic_store.seed_commercial_synonyms()

try:
    graph_store = GraphStore()
    graph_store.seed_commercial_ontology()
except ImportError:
    graph_store = None
    print("[WARN] NetworkX not available — GraphStore disabled")

FEW_SHOT_PATH = Path("knowledge_base/few_shots")
few_shot_store = FewShotStore(FEW_SHOT_PATH)
context_assembler = ContextAssembler(
    judgment_store=judgment_store,
    semantic_store=semantic_store,
    graph_store=graph_store,
    few_shot_store=few_shot_store,
)
init_knowledge_routes(context_assembler, few_shot_store, judgment_store)
app.include_router(knowledge_router)
print(f"[OK] Knowledge Module Initialized ({few_shot_store.stats()['total']} few-shots loaded)")

# Load Reasoning Engine
try:
    with open(ONTOLOGY_PATH, "r") as f:
        ontology = yaml.safe_load(f)
    with open(DATA_PATH, "r") as f:
        data = yaml.safe_load(f)
    engine = ReasoningEngine(ontology, data)
    print("[OK] Reasoning Engine Initialized")
except (FileNotFoundError, yaml.YAMLError, OSError) as e:
    print(f"Could not load ontology/data: {e}")
    ontology = {}
    data = {}
    engine = None


def delta_to_response(delta: Delta, auto_approved: bool = False) -> DeltaResponse:
    """Convert core Delta to API response."""
    return DeltaResponse(
        id=delta.id,
        type=DeltaTypeAPI(delta.type.value),
        status=DeltaStatusAPI(delta.status.value),
        content=delta.content,
        confidence=delta.confidence,
        blast_radius=BlastRadiusAPI(delta.blast_radius.value),
        evidence_pointers=delta.evidence_pointers,
        impacted_missions=delta.impacted_missions,
        impacted_personas=delta.impacted_personas,
        created_at=delta.created_at,
        reviewed_at=delta.reviewed_at,
        reviewed_by=delta.reviewed_by,
        rejection_reason=delta.rejection_reason,
        source_type=delta.source_type,
        auto_approved=auto_approved
    )


def pattern_to_response(pattern: JudgmentPattern) -> JudgmentPatternResponse:
    """Convert core JudgmentPattern to API response."""
    return JudgmentPatternResponse(
        id=pattern.id,
        status=ArtifactStatusAPI(pattern.status.value),
        applies_when_signals=pattern.applies_when_signals,
        applies_when_context=pattern.applies_when_context,
        typical_drivers=[
            DriverAttributionAPI(driver=d.driver, prior_confidence=d.prior_confidence)
            for d in pattern.typical_drivers
        ],
        disallowed_drivers=pattern.disallowed_drivers,
        owner=pattern.governance.owner,
        approver=pattern.governance.approver,
        created_at=pattern.created_at,
        is_active=pattern.is_active()
    )


def guardrail_to_response(g: Guardrail) -> GuardrailResponse:
    """Convert core Guardrail to API response."""
    return GuardrailResponse(
        id=g.id,
        status=ArtifactStatusAPI(g.status.value),
        blocks_action_types=g.blocks_action_types,
        blocks_drivers=g.blocks_drivers,
        unless_evidence=g.unless_evidence,
        applies_to_personas=g.applies_to_personas,
        owner=g.governance.owner,
        is_active=g.status == ArtifactStatus.APPROVED,
    )


@app.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    """Health check with store status."""
    pending = len(delta_store.get_pending_review())
    return HealthResponse(
        status="active",
        engine_loaded=engine is not None,
        stores_initialized=True,
        pending_reviews=pending
    )


@app.get("/stats", response_model=StoreStats, tags=["System"])
def get_stats():
    """Get statistics about all stores."""
    delta_stats = delta_store.stats()
    judgment_stats = judgment_store.stats()
    
    return StoreStats(
        deltas=delta_stats,
        patterns=judgment_stats.get("patterns", {}),
        guardrails=judgment_stats.get("guardrails", {}),
        action_templates=judgment_stats.get("action_templates", {})
    )


@app.post("/deltas", response_model=DeltaResponse, tags=["Deltas"])
def create_delta(request: DeltaCreate):
    """Create a new delta. Level 1 (low risk, high confidence) auto-approves."""
    delta = Delta(
        type=DeltaType(request.type.value),
        content=request.content,
        confidence=request.confidence,
        blast_radius=BlastRadius(request.blast_radius.value),
        evidence_pointers=request.evidence_pointers,
        source_type=request.source_type,
        source_id=request.source_id
    )
    
    was_auto_approvable = delta.is_auto_approvable()
    result = delta_store.propose(delta)
    
    return delta_to_response(result, auto_approved=was_auto_approvable and result.status == DeltaStatus.APPROVED)


@app.get("/deltas", response_model=DeltaListResponse, tags=["Deltas"])
def list_deltas(
    status: Optional[DeltaStatusAPI] = None,
    limit: int = Query(default=50, le=100),
):
    """List deltas with optional status filter."""
    if status == DeltaStatusAPI.PROPOSED:
        deltas = delta_store.get_pending_review(limit=limit)
    elif status:
        deltas = [
            d for d in delta_store._deltas.values()
            if d.status.value == status.value
        ][:limit]
    else:
        deltas = list(delta_store._deltas.values())[:limit]
    
    stats = delta_store.stats()
    
    return DeltaListResponse(
        deltas=[delta_to_response(d) for d in deltas],
        total=stats["total"],
        pending=stats["proposed"]
    )


@app.get("/deltas/{delta_id}", response_model=DeltaResponse, tags=["Deltas"])
def get_delta(delta_id: str):
    """Get a specific delta by ID."""
    delta = delta_store.get(delta_id)
    if not delta:
        raise HTTPException(status_code=404, detail="Delta not found")
    return delta_to_response(delta)


@app.post("/deltas/{delta_id}/approve", response_model=DeltaResponse, tags=["Deltas"])
def approve_delta(delta_id: str, request: DeltaApprove):
    """Approve a pending delta."""
    delta = delta_store.approve(delta_id, request.reviewer)
    if not delta:
        raise HTTPException(
            status_code=400,
            detail="Delta not found or not in pending status"
        )
    return delta_to_response(delta)


@app.post("/deltas/{delta_id}/reject", response_model=DeltaResponse, tags=["Deltas"])
def reject_delta(delta_id: str, request: DeltaReject):
    """Reject a pending delta with a reason."""
    delta = delta_store.reject(delta_id, request.reviewer, request.reason)
    if not delta:
        raise HTTPException(
            status_code=400,
            detail="Delta not found or not in pending status"
        )
    return delta_to_response(delta)


@app.post("/deltas/promote", tags=["Deltas"])
def promote_approved_deltas():
    """Promote all approved deltas to the reasoning graph."""
    result = promotion_pipeline.promote_all_approved()
    return {
        "promoted": result,
        "message": f"Promoted {sum(result.values())} deltas"
    }


@app.post("/patterns", response_model=JudgmentPatternResponse, tags=["Patterns"])
def create_pattern(request: JudgmentPatternCreate):
    """Create a new judgment pattern (starts as draft)."""
    pattern = JudgmentPattern(
        applies_when_signals=request.applies_when_signals,
        applies_when_context=request.applies_when_context,
        typical_drivers=[
            DriverAttribution(driver=d.driver, prior_confidence=d.prior_confidence)
            for d in request.typical_drivers
        ],
        disallowed_drivers=request.disallowed_drivers,
        governance=Governance(owner=request.owner)
    )
    
    result = judgment_store.add_pattern(pattern)
    return pattern_to_response(result)


@app.get("/patterns", response_model=List[JudgmentPatternResponse], tags=["Patterns"])
def list_patterns(active_only: bool = False):
    """List all patterns or only active ones."""
    if active_only:
        patterns = judgment_store.get_active_patterns()
    else:
        patterns = list(judgment_store._patterns.values())
    
    return [pattern_to_response(p) for p in patterns]


@app.post("/patterns/{pattern_id}/approve", response_model=JudgmentPatternResponse, tags=["Patterns"])
def approve_pattern(pattern_id: str, approver: str = Query(...)):
    """Approve a pattern for production use."""
    pattern = judgment_store.approve_pattern(pattern_id, approver)
    if not pattern:
        raise HTTPException(status_code=404, detail="Pattern not found")
    return pattern_to_response(pattern)


@app.post("/guardrails", response_model=GuardrailResponse, tags=["Guardrails"])
def create_guardrail(request: GuardrailCreate):
    """Create a new guardrail (starts as draft)."""
    guardrail = Guardrail(
        blocks_action_types=request.blocks_action_types,
        blocks_drivers=request.blocks_drivers,
        unless_evidence=request.unless_evidence,
        applies_to_personas=request.applies_to_personas,
        excludes_personas=request.excludes_personas,
        governance=Governance(owner=request.owner)
    )
    
    result = judgment_store.add_guardrail(guardrail)
    return guardrail_to_response(result)


@app.get("/guardrails", response_model=List[GuardrailResponse], tags=["Guardrails"])
def list_guardrails(active_only: bool = False):
    """List all guardrails or only active ones."""
    if active_only:
        guardrails = judgment_store.get_active_guardrails()
    else:
        guardrails = list(judgment_store._guardrails.values())
    
    return [guardrail_to_response(g) for g in guardrails]


@app.post("/guardrails/{guardrail_id}/approve", response_model=GuardrailResponse, tags=["Guardrails"])
def approve_guardrail(guardrail_id: str, approver: str = Query(...)):
    """Approve a guardrail for enforcement."""
    guardrail = judgment_store.approve_guardrail(guardrail_id, approver)
    if not guardrail:
        raise HTTPException(status_code=404, detail="Guardrail not found")
    return guardrail_to_response(guardrail)


@app.get("/review-queue", response_model=List[ReviewQueueItem], tags=["HITL"])
def get_review_queue(
    role: Optional[str] = None,
    limit: int = Query(default=50, le=200),
):
    """Get pending deltas for review, optionally filtered by reviewer role."""
    if role:
        deltas = delta_store.get_pending_for_role(role, limit=limit)
    else:
        deltas = delta_store.get_pending_review(limit=limit)
    items: List[ReviewQueueItem] = []
    for d in deltas:
        routing = route_delta(d)
        items.append(ReviewQueueItem(
            delta=delta_to_response(d),
            queue=routing.queue,
            assigned_to=routing.assigned_to,
            priority=routing.priority,
            sla_hours=routing.sla_hours,
            reason=routing.reason,
            judgment_type=d.judgment_type.value,
        ))
    return items


@app.get("/review-queue/stats", response_model=QueueStatsResponse, tags=["HITL"])
def get_queue_stats():
    """Get counts of pending deltas per review queue."""
    stats = delta_store.get_queue_stats()
    total = sum(stats.values())
    return QueueStatsResponse(
        auto=stats.get("auto", 0),
        standard=stats.get("standard", 0),
        escalated=stats.get("escalated", 0),
        total_pending=total,
    )


@app.post("/deltas/{delta_id}/escalate", response_model=DeltaResponse, tags=["HITL"])
def escalate_delta(delta_id: str, request: EscalateRequest):
    """Escalate a pending delta to the next review level."""
    delta = delta_store.escalate(delta_id, request.reason)
    if not delta:
        raise HTTPException(
            status_code=400,
            detail="Delta not found, not pending, or already at highest level",
        )
    return delta_to_response(delta)


@app.get("/audit-log", response_model=List[AuditEntryResponse], tags=["Audit"])
def get_audit_log(
    limit: int = Query(default=100, le=500),
    store: Optional[str] = Query(default=None, description="Filter: 'deltas' or 'judgments'"),
):
    """Get audit log entries from delta and/or judgment stores."""
    entries = []
    if store != "judgments":
        entries.extend(delta_store.get_audit_log(limit=limit))
    if store != "deltas":
        entries.extend(judgment_store.get_audit_log(limit=limit))
    entries.sort(key=lambda e: e.timestamp, reverse=True)
    return [
        AuditEntryResponse(
            id=e.id, timestamp=e.timestamp, actor=e.actor,
            action=e.action, artifact_id=e.artifact_id, details=e.details,
        )
        for e in entries[:limit]
    ]


@app.get("/audit-log/export", tags=["Audit"])
def export_audit_log(
    limit: int = Query(default=500, le=5000),
):
    """Export full audit log as JSON array."""
    entries = delta_store.get_audit_log(limit=limit) + judgment_store.get_audit_log(limit=limit)
    entries.sort(key=lambda e: e.timestamp, reverse=True)
    return [
        {
            "id": e.id, "timestamp": e.timestamp.isoformat(),
            "actor": e.actor, "action": e.action,
            "artifact_id": e.artifact_id, "details": e.details,
        }
        for e in entries[:limit]
    ]


@app.get("/contributions/stats", response_model=ContributionStatsResponse, tags=["Contributions"])
def get_contribution_stats():
    """Get store-level contribution statistics."""
    s = contribution_store.stats()
    return ContributionStatsResponse(**s)


@app.get("/contributors/top", response_model=List[ContributorSummaryResponse], tags=["Contributions"])
def get_top_contributors(limit: int = Query(default=10, le=50)):
    """Get top contributors ranked by total deltas generated."""
    return [ContributorSummaryResponse(**c) for c in contribution_store.get_top_contributors(limit)]


@app.get("/contributors/{sme_id}/summary", response_model=ContributorSummaryResponse, tags=["Contributions"])
def get_contributor_summary(sme_id: str):
    """Get aggregated contribution summary for an SME."""
    return ContributorSummaryResponse(**contribution_store.get_contributor_summary(sme_id))


@app.get("/contributors/{sme_id}/contributions", response_model=List[ContributionResponse], tags=["Contributions"])
def get_sme_contributions(sme_id: str, limit: int = Query(default=50, le=200)):
    """Get contribution history for a specific SME."""
    contributions = contribution_store.get_by_sme(sme_id, limit=limit)
    return [
        ContributionResponse(
            id=c.id, reasoning_event_id=c.reasoning_event_id,
            sme_id=c.sme_id, sme_persona=c.sme_persona,
            delta_ids=c.delta_ids, contributed_at=c.contributed_at,
            therapeutic_area=c.therapeutic_area, scenario_type=c.scenario_type,
            sme_confidence=c.sme_confidence,
        )
        for c in contributions
    ]


def _collect_drivers_from_patterns(
    matches: List[Tuple[JudgmentPattern, float]],
) -> Tuple[List[DriverResult], List[str]]:
    """Extract drivers and pattern IDs from ranked pattern matches."""
    drivers: List[DriverResult] = []
    patterns_used: List[str] = []
    for pattern, _score in matches:
        patterns_used.append(pattern.id)
        for attr in pattern.typical_drivers:
            drivers.append(DriverResult(
                driver=attr.driver,
                confidence=attr.prior_confidence,
                evidence=[],
                pattern_id=pattern.id,
            ))
    if not drivers:
        drivers.append(DriverResult(
            driver="Unknown",
            confidence=0.3,
            evidence=["No matching patterns - requires SME input"],
        ))
    return drivers, patterns_used


def _build_recommendations(top_driver: DriverResult) -> List[ActionRecommendation]:
    """Generate placeholder recommendations from the top driver."""
    if top_driver.driver == "Unknown":
        return []
    return [
        ActionRecommendation(
            function="brand",
            action=f"Investigate {top_driver.driver} impact",
            priority="high",
        ),
        ActionRecommendation(
            function="field",
            action="Gather supporting evidence from accounts",
            priority="medium",
        ),
    ]


def _packet_to_response(packet: IntelligencePacket) -> IntelligencePacketResponse:
    """Convert core IntelligencePacket to API response."""
    return IntelligencePacketResponse(
        id=packet.id,
        signal=packet.signal,
        signal_metric=packet.signal_metric,
        signal_change=packet.signal_change,
        sources=[],
        drivers=[
            DriverResultAPI(
                driver=d.driver, confidence=d.confidence,
                evidence=d.evidence, pattern_id=d.pattern_id,
            )
            for d in packet.drivers
        ],
        implication=packet.implication,
        recommendations=[
            ActionRecommendationAPI(
                function=r.function, action=r.action,
                priority=r.priority, expected_impact=r.expected_impact,
            )
            for r in packet.recommendations
        ],
        confidence=packet.confidence,
        guardrails_applied=packet.guardrails_applied,
        evidence_trace=packet.evidence_trace,
        patterns_used=packet.patterns_used,
        created_at=packet.created_at,
        time_to_generate_ms=packet.time_to_generate_ms,
    )


@app.post("/intelligence-packet", response_model=IntelligencePacketResponse, tags=["Intelligence"])
def generate_intelligence_packet(request: IntelligencePacketRequest):
    """Generate an Intelligence Packet for a given signal."""
    start_time = datetime.utcnow()

    matches = judgment_store.find_matching_patterns(
        [request.signal_metric], request.context,
    )
    drivers, patterns_used = _collect_drivers_from_patterns(matches)
    guardrails_applied = [g.id for g in judgment_store.get_active_guardrails()]

    top_driver = max(drivers, key=lambda d: d.confidence)
    implication = (
        f"Signal likely driven by {top_driver.driver} "
        f"(confidence: {top_driver.confidence:.0%})"
    )
    recommendations = _build_recommendations(top_driver)

    end_time = datetime.utcnow()
    generation_ms = int((end_time - start_time).total_seconds() * 1000)

    packet = IntelligencePacket(
        signal=request.signal,
        signal_metric=request.signal_metric,
        signal_change=request.signal_change,
        sources=[],
        drivers=drivers,
        implication=implication,
        recommendations=recommendations,
        confidence=top_driver.confidence,
        mission_id=request.mission_id,
        persona=request.persona,
        guardrails_applied=guardrails_applied,
        evidence_trace=[],
        patterns_used=patterns_used,
        time_to_generate_ms=generation_ms,
    )
    return _packet_to_response(packet)


def _map_hypothesis(session: GameSessionCreate) -> HypothesisRanking:
    """Map frontend hypothesis input to HypothesisRanking dataclass."""
    return HypothesisRanking(
        category=HypothesisCategory(session.hypothesis.category),
        specific_driver=session.hypothesis.specific_driver or None,
        confidence=session.hypothesis.confidence,
        reasoning=session.hypothesis.reasoning or None,
    )


def _map_disconfirming(session: GameSessionCreate) -> list:
    """Map frontend disconfirm input to DisconfirmingLogic list."""
    if not session.disconfirm or not session.disconfirm.condition:
        return []
    return [DisconfirmingLogic(
        condition=session.disconfirm.condition,
        would_suggest=session.disconfirm.would_suggest,
        would_rule_out=session.disconfirm.would_rule_out or None,
    )]


def _map_pattern(session: GameSessionCreate) -> Optional[PatternRecognition]:
    """Map frontend pattern input to PatternRecognition dataclass."""
    if not session.pattern:
        return None
    return PatternRecognition(
        frequency=session.pattern.frequency,
        typical_outcome=session.pattern.typical_outcome or None,
        time_to_resolution=session.pattern.time_to_resolution or None,
    )


def _map_session_to_event(session: GameSessionCreate) -> ReasoningEvent:
    """Map frontend game session payload to a ReasoningEvent dataclass."""
    signals = [
        RESignalPriority(
            signal_name=s.signal_name, role=s.role, priority_rank=s.priority_rank,
        )
        for s in session.signals
    ]
    mistakes = [
        CommonMistake(
            wrong_conclusion=m.wrong_conclusion,
            why_wrong=m.why_wrong or None,
            unless_evidence=m.unless_evidence or None,
        )
        for m in session.mistakes
    ]
    actions = [
        RecommendedAction(
            action=a.action, action_type=a.action_type,
            priority=a.priority, owner_function=a.owner_function or None,
        )
        for a in session.actions
    ]
    confidence = session.hypothesis.confidence
    if session.confidence:
        confidence = session.confidence.final_confidence

    return ReasoningEvent(
        session_id=session.scenario_id,
        scenario=REScenarioContext(brand=BrandProfile(brand_name="Unknown")),
        scenario_type="game_session",
        primary_hypothesis=_map_hypothesis(session),
        signal_priorities=signals,
        disconfirming_logic=_map_disconfirming(session),
        pattern_recognition=_map_pattern(session),
        common_mistakes=mistakes,
        recommended_actions=actions,
        sme_confidence=confidence,
    )


@app.post("/sessions", response_model=GameSessionResponse, status_code=201, tags=["Sessions"])
def create_session(request: GameSessionCreate):
    """Accept a game session, create ReasoningEvent, generate Deltas."""
    event = _map_session_to_event(request)
    deltas = process_sme_session(event)

    # Store generated deltas
    for delta in deltas:
        delta_store.propose(delta)

    # Store the reasoning event
    reasoning_event_store.add(event)

    # Record contribution for SME impact tracking
    delta_ids = [d.id for d in deltas]
    contribution_store.record(event, delta_ids)

    return GameSessionResponse(
        session_id=event.session_id,
        deltas_generated=len(deltas),
        delta_ids=delta_ids,
        reasoning_event_id=event.id,
    )


@app.get("/sessions", response_model=List[GameSessionSummary], tags=["Sessions"])
def list_sessions():
    """List all stored game sessions."""
    return [
        GameSessionSummary(
            id=e.id,
            scenario_id=e.session_id,
            started_at=e.captured_at,
            deltas_generated=len(e.deltas_generated),
        )
        for e in reasoning_event_store.list_all()
    ]


@app.get("/sessions/{session_id}", response_model=GameSessionDetail, tags=["Sessions"])
def get_session(session_id: str):
    """Get full detail of a stored game session."""
    event = reasoning_event_store.get(session_id)
    if not event:
        raise HTTPException(status_code=404, detail="Session not found")
    return GameSessionDetail(
        id=event.id,
        scenario_id=event.session_id,
        started_at=event.captured_at,
        deltas_generated=len(event.deltas_generated),
        delta_ids=event.deltas_generated,
        hypothesis_category=event.primary_hypothesis.category.value if event.primary_hypothesis else None,
        sme_confidence=event.sme_confidence,
        processed=event.processed,
    )


@app.post("/reason", response_model=LegacyReasonResponse, tags=["Legacy"])
def get_reasoning(request: LegacyReasonRequest):
    """Legacy reasoning endpoint for backward compatibility."""
    if not engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    
    context = ScenarioContext(
        account_id=request.account_id,
        brand_id=request.brand_id
    )
    
    response = engine.reason(request.question, context)
    
    return LegacyReasonResponse(
        verdict=response.verdict,
        confidence_score=response.confidence_score,
        risks=response.identified_risks,
        evidence=response.supporting_evidence_tags
    )


SCENARIOS_DIR = Path("ontology/scenarios")


def _load_yaml_scenarios() -> list:
    """Load all YAML scenarios from ontology/scenarios/, normalizing schema differences.

    Two schema variants exist:
      ONC-series (ONC-001..010): trigger_signal=string, molecular_context, channel, simple drivers
      Numbered series (01..05):  trigger_signal=object, molecular_subtype, asset_class, richer contexts
    We normalize both into a single flat shape for the frontend.
    """
    scenarios = []
    for path in sorted(SCENARIOS_DIR.glob("*.yaml")):
        try:
            with open(path, "r") as f:
                raw = yaml.safe_load(f)
            if not raw or not isinstance(raw, dict):
                continue

            # --- trigger_signal: object → descriptive string ---
            trigger = raw.get("trigger_signal", "")
            if isinstance(trigger, dict):
                parts = []
                if trigger.get("description"):
                    parts.append(trigger["description"])
                if trigger.get("metric") and trigger.get("direction"):
                    mag = trigger.get("magnitude")
                    mag_str = f" ({mag:+.0%})" if isinstance(mag, (int, float)) else ""
                    parts.append(f"{trigger['metric']} {trigger['direction']}{mag_str}")
                trigger = " — ".join(parts) if parts else str(trigger)

            # --- brand_context: merge both schema variants ---
            brand_raw = raw.get("brand_context") or {}
            brand_context = {
                "brand": brand_raw.get("brand", ""),
                "lifecycle": brand_raw.get("lifecycle", ""),
                "channel": brand_raw.get("channel") or brand_raw.get("asset_class") or None,
                "biomarkers_required": brand_raw.get("biomarkers_required") or None,
                "companion_diagnostic": brand_raw.get("companion_diagnostic") or None,
            }

            # --- account_context: merge both schema variants ---
            acct_raw = raw.get("account_context") or {}
            account_context = {
                "type": acct_raw.get("type", ""),
                "biomarker_testing": (
                    acct_raw.get("biomarker_testing")
                    or acct_raw.get("testing_infrastructure")
                    or None
                ),
                "potential": acct_raw.get("potential") or None,
                "access_status": acct_raw.get("access_status") or None,
                "payer_mix": acct_raw.get("payer_mix") or None,
                "tumor_board_influence": acct_raw.get("tumor_board_influence") or None,
            }

            scenarios.append({
                "id": raw.get("id", path.stem),
                "name": raw.get("name", path.stem),
                "description": raw.get("description", "").strip(),
                "therapeutic_area": raw.get("therapeutic_area", ""),
                "indication": raw.get("indication", ""),
                "molecular_context": raw.get("molecular_context") or raw.get("molecular_subtype") or None,
                "line_of_therapy": raw.get("line_of_therapy") or None,
                "brand_context": brand_context,
                "account_context": account_context,
                "trigger_signal": trigger,
                "complexity_level": raw.get("complexity_level", "medium"),
                "expected_hypothesis": raw.get("expected_hypothesis", ""),
            })
        except (yaml.YAMLError, OSError) as e:
            print(f"[WARN] Skipping {path.name}: {e}")
    return scenarios


@app.get("/scenarios", tags=["Game"])
def list_scenarios():
    """Returns all scenarios loaded from YAML files."""
    return _load_yaml_scenarios()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8098))
    uvicorn.run(app, host="0.0.0.0", port=port)
