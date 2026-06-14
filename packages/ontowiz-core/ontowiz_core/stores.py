"""
Onto_Wiz Stores (Repositories)

In-memory stores for Delta, Judgment Artifacts, and Graph.
These will be replaced with persistent storage (Postgres, Neo4j) in production.

Design Principles:
1. All mutations go through stores (single source of truth)
2. Deltas are proposed, reviewed, then promoted
3. Promotion = update to the Reasoning Graph
"""

from collections import defaultdict
from collections.abc import Callable
from datetime import datetime
from typing import Any

from .models import (
    ActionTemplate,
    ArtifactStatus,
    AuditEntry,
    BlastRadius,
    ConflictResult,
    Contribution,
    Delta,
    DeltaStatus,
    DeltaType,
    DriverAttribution,
    Guardrail,
    GuardrailResult,
    JudgmentPattern,
    JudgmentType,
    RoutingDecision,
)

# =============================================================================
# HELPERS — Pattern consolidation (CTX-009)
# =============================================================================

def _merge_drivers(
    keep: list["DriverAttribution"], merge: list["DriverAttribution"],
) -> list["DriverAttribution"]:
    """Union drivers by name, keeping whichever has higher prior_confidence."""
    by_name: dict[str, DriverAttribution] = {}
    for d in keep:
        by_name[d.driver] = d
    for d in merge:
        existing = by_name.get(d.driver)
        if existing is None or d.prior_confidence > existing.prior_confidence:
            by_name[d.driver] = d
    return list(by_name.values())


def _bump_version(version: str) -> str:
    """Increment minor version: '1.0.0' -> '1.1.0'."""
    parts = version.split(".")
    if len(parts) != 3:
        return version
    return f"{parts[0]}.{int(parts[1]) + 1}.0"


# =============================================================================
# CLASSIFICATION - Judgment type derivation and approver routing
# =============================================================================

# Delta types that map directly to a fixed judgment classification
_FIXED_CLASSIFICATION = {
    DeltaType.PROPOSED_SYNONYM: JudgmentType.EMPIRICAL,
    DeltaType.PROPOSED_MAPPING: JudgmentType.EMPIRICAL,
    DeltaType.PROPOSED_PATTERN: JudgmentType.CAUSAL_HYPOTHESIS,
    DeltaType.PROPOSED_GUARDRAIL: JudgmentType.CAUSAL_HYPOTHESIS,
    DeltaType.PROPOSED_ACTION: JudgmentType.NORMATIVE,
}

# Blast-radius-based classification for EDGE and ENTITY types
_BLAST_TO_JUDGMENT = {
    BlastRadius.LOW: JudgmentType.EMPIRICAL,
    BlastRadius.MEDIUM: JudgmentType.CAUSAL_HYPOTHESIS,
    BlastRadius.HIGH: JudgmentType.NORMATIVE,
}

_APPROVER_MAP = {
    JudgmentType.EMPIRICAL: "system_auto",
    JudgmentType.CAUSAL_HYPOTHESIS: "domain_expert",
    JudgmentType.NORMATIVE: "governance_board",
}


def classify_delta(delta: Delta) -> JudgmentType:
    """Derive judgment classification from delta type and blast radius."""
    fixed = _FIXED_CLASSIFICATION.get(delta.type)
    if fixed is not None:
        return fixed
    return _BLAST_TO_JUDGMENT.get(delta.blast_radius, JudgmentType.CAUSAL_HYPOTHESIS)


def get_required_approver(delta: Delta) -> str:
    """Map delta's judgment classification to the required approver level."""
    return _APPROVER_MAP.get(delta.judgment_type, "domain_expert")


# =============================================================================
# HITL ROUTING - Queue assignment based on judgment type + blast radius
# =============================================================================

# (judgment_type, blast_radius) -> (queue, assigned_to, priority, sla_hours)
_ROUTING_TABLE: dict[tuple, tuple] = {
    (JudgmentType.EMPIRICAL, BlastRadius.LOW): ("auto", "system_auto", "low", 0),
    (JudgmentType.EMPIRICAL, BlastRadius.MEDIUM): ("standard", "domain_expert", "normal", 48),
    (JudgmentType.EMPIRICAL, BlastRadius.HIGH): ("standard", "domain_expert", "high", 24),
    (JudgmentType.CAUSAL_HYPOTHESIS, BlastRadius.LOW): ("standard", "domain_expert", "normal", 48),
    (JudgmentType.CAUSAL_HYPOTHESIS, BlastRadius.MEDIUM): ("standard", "domain_expert", "high", 24),
    (JudgmentType.CAUSAL_HYPOTHESIS, BlastRadius.HIGH): ("standard", "domain_expert", "high", 24),
    (JudgmentType.NORMATIVE, BlastRadius.LOW): ("escalated", "governance_board", "high", 12),
    (JudgmentType.NORMATIVE, BlastRadius.MEDIUM): ("escalated", "governance_board", "high", 12),
    (JudgmentType.NORMATIVE, BlastRadius.HIGH): ("escalated", "governance_board", "critical", 5),
}

_ESCALATION_PATH = {
    "system_auto": "domain_expert",
    "domain_expert": "governance_board",
}


def route_delta(delta: Delta) -> RoutingDecision:
    """Determine review queue and assignee from judgment type + blast radius."""
    key = (delta.judgment_type, delta.blast_radius)
    entry = _ROUTING_TABLE.get(key)
    if entry is None:
        return RoutingDecision(
            assigned_to="domain_expert", queue="standard",
            priority="normal", sla_hours=48,
            reason=f"Default routing for {delta.judgment_type.value}/{delta.blast_radius.value}",
        )
    queue, assigned_to, priority, sla_hours = entry
    return RoutingDecision(
        assigned_to=assigned_to, queue=queue,
        priority=priority, sla_hours=sla_hours,
        reason=f"{delta.judgment_type.value} + {delta.blast_radius.value} blast",
    )


# =============================================================================
# DELTA STORE - Proposals, Reviews, Promotions
# =============================================================================

class DeltaStore:
    """
    Store for all proposed changes (deltas).

    This is the foundation of the self-healing loop:
    1. Agents/uploads propose deltas
    2. Reviewers approve/reject
    3. Approved deltas are promoted to the graph
    """

    def __init__(self):
        self._deltas: dict[str, Delta] = {}
        self._by_status: dict[DeltaStatus, list[str]] = defaultdict(list)
        self._by_type: dict[DeltaType, list[str]] = defaultdict(list)
        self._audit_log: list[AuditEntry] = []

    def propose(self, delta: Delta) -> Delta:
        """
        Add a new proposed delta.

        Auto-approve Level 1 deltas (low blast radius, high confidence).
        """
        delta.status = DeltaStatus.PROPOSED
        delta.created_at = datetime.utcnow()
        delta.judgment_type = classify_delta(delta)
        routing = route_delta(delta)
        delta.assigned_to = routing.assigned_to

        self._deltas[delta.id] = delta
        self._by_status[DeltaStatus.PROPOSED].append(delta.id)
        self._by_type[delta.type].append(delta.id)

        # Auto-approve if Level 1
        if delta.is_auto_approvable():
            self.approve(delta.id, reviewer="system_auto")

        self._log_audit(
            "propose", delta.id, {"type": delta.type.value},
            actor=delta.owner, category="create",
            after={"status": delta.status.value, "type": delta.type.value},
        )
        return delta

    def approve(self, delta_id: str, reviewer: str) -> Delta | None:
        """Approve a delta for promotion."""
        delta = self._deltas.get(delta_id)
        if not delta or delta.status != DeltaStatus.PROPOSED:
            return None

        before_status = delta.status.value
        delta.approve(reviewer)

        # Update indexes
        self._by_status[DeltaStatus.PROPOSED].remove(delta_id)
        self._by_status[DeltaStatus.APPROVED].append(delta_id)

        self._log_audit(
            "approve", delta_id, {"reviewer": reviewer},
            actor=reviewer, category="approve",
            before={"status": before_status}, after={"status": delta.status.value},
        )
        return delta

    def reject(self, delta_id: str, reviewer: str, reason: str) -> Delta | None:
        """Reject a delta with a reason."""
        delta = self._deltas.get(delta_id)
        if not delta or delta.status != DeltaStatus.PROPOSED:
            return None

        before_status = delta.status.value
        delta.reject(reviewer, reason)

        # Update indexes
        self._by_status[DeltaStatus.PROPOSED].remove(delta_id)
        self._by_status[DeltaStatus.REJECTED].append(delta_id)

        self._log_audit(
            "reject", delta_id, {"reviewer": reviewer, "reason": reason},
            actor=reviewer, category="reject",
            before={"status": before_status}, after={"status": delta.status.value},
        )
        return delta

    def mark_merged(self, delta_id: str) -> Delta | None:
        """Mark a delta as merged into the graph."""
        delta = self._deltas.get(delta_id)
        if not delta or delta.status != DeltaStatus.APPROVED:
            return None

        before_status = delta.status.value
        delta.status = DeltaStatus.MERGED
        self._by_status[DeltaStatus.APPROVED].remove(delta_id)
        self._by_status[DeltaStatus.MERGED].append(delta_id)

        self._log_audit(
            "merge", delta_id, {},
            category="merge",
            before={"status": before_status}, after={"status": delta.status.value},
        )
        return delta

    def get_pending_review(self, limit: int = 50) -> list[Delta]:
        """Get deltas pending human review, sorted by blast radius (highest first)."""
        pending_ids = self._by_status.get(DeltaStatus.PROPOSED, [])
        pending = [self._deltas[did] for did in pending_ids if did in self._deltas]

        # Sort by blast radius (HIGH > MEDIUM > LOW), then by created_at
        priority = {BlastRadius.HIGH: 0, BlastRadius.MEDIUM: 1, BlastRadius.LOW: 2}
        pending.sort(key=lambda d: (priority.get(d.blast_radius, 2), d.created_at))

        return pending[:limit]

    def get_pending_for_role(self, role: str, limit: int = 50) -> list[Delta]:
        """Get pending deltas assigned to a specific reviewer role."""
        all_pending = self.get_pending_review(limit=9999)
        filtered = [d for d in all_pending if d.assigned_to == role]
        return filtered[:limit] if limit else filtered

    def escalate(self, delta_id: str, reason: str) -> Delta | None:
        """Promote a delta to the next review level."""
        delta = self._deltas.get(delta_id)
        if not delta or delta.status != DeltaStatus.PROPOSED:
            return None
        next_role = _ESCALATION_PATH.get(delta.assigned_to)
        if next_role is None:
            return None
        prev_role = delta.assigned_to
        delta.assigned_to = next_role
        self._log_audit(
            "escalate", delta_id,
            {"from": prev_role, "to": next_role, "reason": reason},
            category="escalate",
            before={"assigned_to": prev_role}, after={"assigned_to": next_role},
        )
        return delta

    def get_queue_stats(self) -> dict[str, int]:
        """Count pending deltas per queue (auto, standard, escalated)."""
        stats: dict[str, int] = {"auto": 0, "standard": 0, "escalated": 0}
        for delta in self.get_pending_review(limit=9999):
            decision = route_delta(delta)
            stats[decision.queue] = stats.get(decision.queue, 0) + 1
        return stats

    def get_approved_unmerged(self) -> list[Delta]:
        """Get approved deltas ready for promotion."""
        approved_ids = self._by_status.get(DeltaStatus.APPROVED, [])
        return [self._deltas[did] for did in approved_ids if did in self._deltas]

    def get(self, delta_id: str) -> Delta | None:
        """Get a specific delta by ID."""
        return self._deltas.get(delta_id)

    def find_conflicts(self, delta: Delta) -> list[ConflictResult]:
        """
        Find deltas that conflict with this one (US-025).

        Detects: canonical ID collisions, scope overlap, edge contradictions.
        Skips REJECTED and MERGED deltas.
        """
        conflicts: list[ConflictResult] = []
        for other in self._deltas.values():
            if other.id == delta.id:
                continue
            if other.status in [DeltaStatus.REJECTED, DeltaStatus.MERGED]:
                continue
            if other.type != delta.type:
                continue
            for checker in (
                self._check_canonical_collision,
                self._check_scope_overlap,
                self._check_edge_contradiction,
            ):
                result = checker(delta, other)
                if result is not None:
                    conflicts.append(result)
        return conflicts

    def _check_canonical_collision(
        self, a: Delta, b: Delta
    ) -> ConflictResult | None:
        """Detect synonym/mapping/entity deltas targeting the same canonical ID."""
        id_types = (
            DeltaType.PROPOSED_SYNONYM,
            DeltaType.PROPOSED_MAPPING,
            DeltaType.PROPOSED_ENTITY,
        )
        if a.type not in id_types:
            return None
        for key in ("canonical_id", "entity_id", "term"):
            val = a.content.get(key)
            if val and val == b.content.get(key):
                return ConflictResult(
                    delta_id=b.id,
                    conflict_type="canonical_id_collision",
                    description=f"Both deltas target {key}='{val}'",
                    severity="blocker",
                )
        return None

    def _check_scope_overlap(
        self, a: Delta, b: Delta
    ) -> ConflictResult | None:
        """Detect pattern deltas with overlapping signals and scope."""
        if a.type != DeltaType.PROPOSED_PATTERN:
            return None
        a_signals = set(a.content.get("applies_when_signals", []))
        b_signals = set(b.content.get("applies_when_signals", []))
        overlap = a_signals & b_signals
        if not overlap:
            return None
        return ConflictResult(
            delta_id=b.id,
            conflict_type="scope_overlap",
            description=f"Overlapping signals: {sorted(overlap)}",
            severity="warning",
        )

    def _check_edge_contradiction(
        self, a: Delta, b: Delta
    ) -> ConflictResult | None:
        """Detect edge deltas with same source+target but different relationship."""
        if a.type != DeltaType.PROPOSED_EDGE:
            return None
        ac, bc = a.content, b.content
        if ac.get("source") != bc.get("source"):
            return None
        if ac.get("target") != bc.get("target"):
            return None
        if not ac.get("source"):
            return None
        a_rel = ac.get("relationship", ac.get("label", ""))
        b_rel = bc.get("relationship", bc.get("label", ""))
        if a_rel != b_rel:
            return ConflictResult(
                delta_id=b.id,
                conflict_type="edge_contradiction",
                description=(
                    f"Same edge {ac['source']}->{ac['target']} "
                    f"but different relationships: '{a_rel}' vs '{b_rel}'"
                ),
                severity="blocker",
            )
        return ConflictResult(
            delta_id=b.id,
            conflict_type="edge_contradiction",
            description=f"Duplicate edge {ac['source']}->{ac['target']}",
            severity="warning",
        )

    def _log_audit(
        self, action: str, artifact_id: str, details: dict,
        actor: str = "", category: str = "",
        before: dict | None = None, after: dict | None = None,
    ):
        """Log an audit entry with enhanced context."""
        self._audit_log.append(AuditEntry(
            actor=actor, action=action, artifact_id=artifact_id,
            details=details, store_type="delta", action_category=category,
            before_snapshot=before or {}, after_snapshot=after or {},
        ))

    def get_audit_log(self, limit: int = 100, action: str | None = None) -> list[AuditEntry]:
        """Get recent audit entries, optionally filtered by action."""
        entries = self._audit_log
        if action:
            entries = [e for e in entries if e.action == action]
        return entries[-limit:]

    def stats(self) -> dict[str, Any]:
        """Get store statistics."""
        return {
            "total": len(self._deltas),
            "proposed": len(self._by_status.get(DeltaStatus.PROPOSED, [])),
            "approved": len(self._by_status.get(DeltaStatus.APPROVED, [])),
            "rejected": len(self._by_status.get(DeltaStatus.REJECTED, [])),
            "merged": len(self._by_status.get(DeltaStatus.MERGED, [])),
        }


# =============================================================================
# JUDGMENT STORE - Patterns, Guardrails, Actions
# =============================================================================

class JudgmentStore:
    """
    Store for governed judgment artifacts.

    All artifacts follow lifecycle: draft → approved → deprecated
    Only approved artifacts are used in traversal.
    """

    def __init__(self):
        self._patterns: dict[str, JudgmentPattern] = {}
        self._guardrails: dict[str, Guardrail] = {}
        self._action_templates: dict[str, ActionTemplate] = {}
        self._audit_log: list[AuditEntry] = []

    # -------------------------------------------------------------------------
    # Patterns
    # -------------------------------------------------------------------------

    def add_pattern(self, pattern: JudgmentPattern) -> JudgmentPattern:
        """Add a new judgment pattern (starts as draft)."""
        pattern.status = ArtifactStatus.DRAFT
        pattern.created_at = datetime.utcnow()
        self._patterns[pattern.id] = pattern
        self._log_audit(
            "add_pattern", pattern.id, {"version": pattern.version},
            category="create",
            after={"status": pattern.status.value},
        )
        return pattern

    def approve_pattern(self, pattern_id: str, approver: str) -> JudgmentPattern | None:
        """Approve a pattern for production use."""
        pattern = self._patterns.get(pattern_id)
        if not pattern:
            return None

        before_status = pattern.status.value
        pattern.status = ArtifactStatus.APPROVED
        pattern.governance.approver = approver
        pattern.governance.approved_on = datetime.utcnow()

        self._log_audit(
            "approve_pattern", pattern_id, {"approver": approver},
            actor=approver, category="approve",
            before={"status": before_status}, after={"status": pattern.status.value},
        )
        return pattern

    def deprecate_pattern(self, pattern_id: str) -> JudgmentPattern | None:
        """Deprecate a pattern (no longer used in traversal)."""
        pattern = self._patterns.get(pattern_id)
        if not pattern:
            return None

        before_status = pattern.status.value
        pattern.status = ArtifactStatus.DEPRECATED
        self._log_audit(
            "deprecate_pattern", pattern_id, {},
            category="reject",
            before={"status": before_status}, after={"status": pattern.status.value},
        )
        return pattern

    def get_active_patterns(self) -> list[JudgmentPattern]:
        """Get all patterns that are active (approved and not stale)."""
        return [p for p in self._patterns.values() if p.is_active()]

    def find_matching_patterns(
        self,
        signals: list[str],
        context: dict[str, Any],
        min_score: float = 0.3,
    ) -> list[tuple[JudgmentPattern, float]]:
        """Find active patterns ranked by match_score, filtered by min_score."""
        results: list[tuple[JudgmentPattern, float]] = []
        for pattern in self.get_active_patterns():
            score = pattern.match_score(signals, context)
            if score >= min_score:
                results.append((pattern, score))
        results.sort(key=lambda pair: pair[1], reverse=True)
        return results

    def get_pattern(self, pattern_id: str) -> JudgmentPattern | None:
        """Get a specific pattern by ID."""
        return self._patterns.get(pattern_id)

    # -------------------------------------------------------------------------
    # Guardrails
    # -------------------------------------------------------------------------

    def add_guardrail(self, guardrail: Guardrail) -> Guardrail:
        """Add a new guardrail (starts as draft)."""
        guardrail.status = ArtifactStatus.DRAFT
        self._guardrails[guardrail.id] = guardrail
        self._log_audit(
            "add_guardrail", guardrail.id, {},
            category="create", after={"status": guardrail.status.value},
        )
        return guardrail

    def approve_guardrail(self, guardrail_id: str, approver: str) -> Guardrail | None:
        """Approve a guardrail."""
        guardrail = self._guardrails.get(guardrail_id)
        if not guardrail:
            return None

        before_status = guardrail.status.value
        guardrail.status = ArtifactStatus.APPROVED
        guardrail.governance.approver = approver
        guardrail.governance.approved_on = datetime.utcnow()

        self._log_audit(
            "approve_guardrail", guardrail_id, {"approver": approver},
            actor=approver, category="approve",
            before={"status": before_status}, after={"status": guardrail.status.value},
        )
        return guardrail

    def get_active_guardrails(self) -> list[Guardrail]:
        """Get all approved guardrails."""
        return [g for g in self._guardrails.values() if g.status == ArtifactStatus.APPROVED]

    def check_violations(
        self,
        action_type: str,
        evidence: list[str],
        persona: str
    ) -> list[Guardrail]:
        """Find all guardrails that would be violated."""
        violations = []
        for guardrail in self.get_active_guardrails():
            if guardrail.is_violated(action_type, evidence, persona):
                violations.append(guardrail)
        return violations

    def check_driver_guardrails(
        self,
        drivers: list[str],
        evidence: list[str],
    ) -> list[GuardrailResult]:
        """Evaluate all active guardrails against proposed drivers."""
        results: list[GuardrailResult] = []
        for guardrail in self.get_active_guardrails():
            result = guardrail.evaluate_drivers(drivers, evidence)
            if result.is_blocked:
                results.append(result)
        return results

    # -------------------------------------------------------------------------
    # Action Templates
    # -------------------------------------------------------------------------

    def add_action_template(self, template: ActionTemplate) -> ActionTemplate:
        """Add a new action template (starts as draft)."""
        template.status = ArtifactStatus.DRAFT
        self._action_templates[template.id] = template
        self._log_audit(
            "add_action_template", template.id, {},
            category="create", after={"status": template.status.value},
        )
        return template

    def approve_action_template(
        self,
        template_id: str,
        approver: str,
    ) -> ActionTemplate | None:
        """Approve an action template."""
        template = self._action_templates.get(template_id)
        if not template:
            return None

        before_status = template.status.value
        template.status = ArtifactStatus.APPROVED
        template.governance.approver = approver
        template.governance.approved_on = datetime.utcnow()

        self._log_audit(
            "approve_action_template", template_id, {"approver": approver},
            actor=approver, category="approve",
            before={"status": before_status}, after={"status": template.status.value},
        )
        return template

    def get_template_for_pattern(self, pattern_id: str) -> ActionTemplate | None:
        """Get the action template triggered by a pattern."""
        for template in self._action_templates.values():
            if (
                template.status == ArtifactStatus.APPROVED
                and template.trigger_pattern_id == pattern_id
            ):
                return template
        return None

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------

    def _log_audit(
        self, action: str, artifact_id: str, details: dict,
        actor: str = "", category: str = "",
        before: dict | None = None, after: dict | None = None,
    ):
        """Log an audit entry with enhanced context."""
        self._audit_log.append(AuditEntry(
            actor=actor, action=action, artifact_id=artifact_id,
            details=details, store_type="judgment", action_category=category,
            before_snapshot=before or {}, after_snapshot=after or {},
        ))

    def get_audit_log(self, limit: int = 100, action: str | None = None) -> list[AuditEntry]:
        """Return the most recent audit entries, optionally filtered by action."""
        entries = self._audit_log
        if action:
            entries = [e for e in entries if e.action == action]
        return entries[-limit:]

    def get_stale_patterns(self) -> list[JudgmentPattern]:
        """Get patterns that have decayed past their validity period."""
        stale = []
        for pattern in self._patterns.values():
            if pattern.status == ArtifactStatus.APPROVED and pattern.decay.is_stale(
                pattern.created_at
            ):
                stale.append(pattern)
        return stale

    # --- Review cycle enforcement (CTX-007) ---

    def get_patterns_due_for_review(self, include_upcoming_days: int = 0) -> list[JudgmentPattern]:
        """Return approved patterns where governance review is due or upcoming."""
        result = []
        for p in self._patterns.values():
            if p.status != ArtifactStatus.APPROVED:
                continue
            remaining = p.governance.days_until_review()
            if remaining is not None and remaining <= include_upcoming_days:
                result.append(p)
        return result

    def get_guardrails_due_for_review(self, include_upcoming_days: int = 0) -> list[Guardrail]:
        """Return approved guardrails where governance review is due or upcoming."""
        result = []
        for g in self._guardrails.values():
            if g.status != ArtifactStatus.APPROVED:
                continue
            remaining = g.governance.days_until_review()
            if remaining is not None and remaining <= include_upcoming_days:
                result.append(g)
        return result

    def get_review_summary(self) -> dict[str, Any]:
        """Counts and IDs of artifacts overdue for governance review."""
        overdue_p = self.get_patterns_due_for_review()
        overdue_g = self.get_guardrails_due_for_review()
        overdue_t = [
            t for t in self._action_templates.values()
            if t.status == ArtifactStatus.APPROVED and t.governance.is_review_due()
        ]
        return {
            "patterns_overdue": len(overdue_p),
            "pattern_ids": [p.id for p in overdue_p],
            "guardrails_overdue": len(overdue_g),
            "guardrail_ids": [g.id for g in overdue_g],
            "action_templates_overdue": len(overdue_t),
            "action_template_ids": [t.id for t in overdue_t],
        }

    # --- Pattern consolidation / reconciler (CTX-009) ---

    def compute_pattern_similarity(self, a_id: str, b_id: str) -> float:
        """Jaccard similarity of applies_when_signals between two patterns."""
        a, b = self._patterns.get(a_id), self._patterns.get(b_id)
        if not a or not b:
            return 0.0
        set_a, set_b = set(a.applies_when_signals), set(b.applies_when_signals)
        union = set_a | set_b
        if not union:
            return 0.0
        return len(set_a & set_b) / len(union)

    def find_overlapping_patterns(
        self, min_similarity: float = 0.5,
    ) -> list[tuple[str, str, float]]:
        """Pairwise scan of active patterns returning pairs above threshold."""
        active = self.get_active_patterns()
        results: list[tuple[str, str, float]] = []
        for i, a in enumerate(active):
            for b in active[i + 1:]:
                sim = self.compute_pattern_similarity(a.id, b.id)
                if sim >= min_similarity:
                    results.append((a.id, b.id, sim))
        results.sort(key=lambda t: t[2], reverse=True)
        return results

    def consolidate_patterns(
        self, keep_id: str, merge_id: str, actor: str,
    ) -> JudgmentPattern | None:
        """Merge merge_id into keep_id, deprecate merge_id with lineage."""
        keep = self._patterns.get(keep_id)
        merge = self._patterns.get(merge_id)
        if not keep or not merge:
            return None
        if keep.status != ArtifactStatus.APPROVED or merge.status != ArtifactStatus.APPROVED:
            return None

        # Union signals, context, scenarios, disallowed_drivers
        keep.applies_when_signals = sorted(set(keep.applies_when_signals) | set(merge.applies_when_signals))
        keep.applies_when_context = sorted(set(keep.applies_when_context) | set(merge.applies_when_context))
        keep.trained_from_scenarios = sorted(set(keep.trained_from_scenarios) | set(merge.trained_from_scenarios))
        keep.disallowed_drivers = sorted(set(keep.disallowed_drivers) | set(merge.disallowed_drivers))
        keep.typical_drivers = _merge_drivers(keep.typical_drivers, merge.typical_drivers)
        keep.version = _bump_version(keep.version)

        # Deprecate merge_id with lineage
        self.deprecate_pattern(merge_id)
        merge.superseded_by = keep_id

        self._log_audit(
            "consolidate_patterns", keep_id,
            {"merged_from": merge_id, "actor": actor},
            actor=actor, category="merge",
            after={"version": keep.version, "signals": keep.applies_when_signals},
        )
        return keep

    def get_consolidation_candidates(
        self, min_similarity: float = 0.5,
    ) -> list[dict[str, Any]]:
        """User-friendly report of pattern pairs that may warrant consolidation."""
        pairs = self.find_overlapping_patterns(min_similarity)
        results: list[dict[str, Any]] = []
        for a_id, b_id, sim in pairs:
            a, b = self._patterns[a_id], self._patterns[b_id]
            shared = sorted(set(a.applies_when_signals) & set(b.applies_when_signals))
            results.append({
                "pattern_a_id": a_id, "pattern_b_id": b_id,
                "similarity": round(sim, 3), "shared_signals": shared,
                "total_signals_a": len(a.applies_when_signals),
                "total_signals_b": len(b.applies_when_signals),
            })
        return results

    # --- Semantic search (CTX-019) ---

    @staticmethod
    def expand_signals(signals: list[str], semantic_store) -> list[str]:
        """Expand signal names through SemanticStore synonyms/aliases.

        For each signal: resolve to canonical, then gather all variants.
        Unknown terms pass through unchanged.
        """
        expanded: set = set()
        for sig in signals:
            expanded.add(sig)
            canonical = semantic_store.resolve_to_canonical(sig)
            if canonical:
                expanded.add(canonical.term)
                variants = semantic_store.get_all_variants(canonical.id)
                expanded.update(variants)
        return sorted(expanded)

    def semantic_find_patterns(
        self,
        query_terms: list[str],
        context: dict[str, Any],
        semantic_store,
        min_score: float = 0.3,
    ) -> list[tuple[JudgmentPattern, float]]:
        """Find patterns using semantically expanded query terms."""
        expanded = self.expand_signals(query_terms, semantic_store)
        return self.find_matching_patterns(expanded, context, min_score)

    def stats(self) -> dict[str, Any]:
        """Get store statistics."""
        return {
            "patterns": {
                "total": len(self._patterns),
                "active": len(self.get_active_patterns()),
                "stale": len(self.get_stale_patterns()),
            },
            "guardrails": {
                "total": len(self._guardrails),
                "active": len(self.get_active_guardrails()),
            },
            "action_templates": {
                "total": len(self._action_templates),
                "approved": len([t for t in self._action_templates.values()
                                if t.status == ArtifactStatus.APPROVED]),
            },
        }


# =============================================================================
# PROMOTION PIPELINE - Delta → Graph Updates
# =============================================================================

class PromotionPipeline:
    """
    Handles promotion of approved deltas to the reasoning graph.

    This is the bridge between the review queue and the live system.
    """

    def __init__(self, delta_store: DeltaStore, judgment_store: JudgmentStore):
        self.delta_store = delta_store
        self.judgment_store = judgment_store
        self._promotion_handlers: dict[DeltaType, Callable] = {}
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register handlers for each delta type."""
        self._promotion_handlers[DeltaType.PROPOSED_PATTERN] = self._promote_pattern
        self._promotion_handlers[DeltaType.PROPOSED_GUARDRAIL] = self._promote_guardrail
        self._promotion_handlers[DeltaType.PROPOSED_ACTION] = self._promote_action

    def promote_all_approved(self) -> dict[str, int]:
        """Promote all approved deltas to the graph."""
        promoted = defaultdict(int)

        for delta in self.delta_store.get_approved_unmerged():
            handler = self._promotion_handlers.get(delta.type)
            if handler:
                success = handler(delta)
                if success:
                    self.delta_store.mark_merged(delta.id)
                    promoted[delta.type.value] += 1

        return dict(promoted)

    def _promote_pattern(self, delta: Delta) -> bool:
        """Promote a pattern delta to the judgment store."""
        content = delta.content
        pattern = JudgmentPattern(
            applies_when_signals=content.get("applies_when_signals", []),
            applies_when_context=content.get("applies_when_context", []),
            trained_from_scenarios=content.get("trained_from_scenarios", []),
        )
        # Add driver attributions
        for driver_data in content.get("typical_drivers", []):
            from .models import DriverAttribution
            pattern.typical_drivers.append(DriverAttribution(
                driver=driver_data.get("driver"),
                prior_confidence=driver_data.get("prior_confidence", 0.5)
            ))
        pattern.disallowed_drivers = content.get("disallowed_drivers", [])

        self.judgment_store.add_pattern(pattern)
        # Auto-approve since delta was already approved
        self.judgment_store.approve_pattern(pattern.id, delta.reviewed_by or "system")
        return True

    def _promote_guardrail(self, delta: Delta) -> bool:
        """Promote a guardrail delta to the judgment store."""
        content = delta.content
        guardrail = Guardrail(
            blocks_action_types=content.get("blocks_action_types", []),
            blocks_drivers=content.get("blocks_drivers", []),
            unless_evidence=content.get("unless_evidence", []),
            applies_to_personas=content.get("applies_to_personas", []),
        )

        self.judgment_store.add_guardrail(guardrail)
        self.judgment_store.approve_guardrail(guardrail.id, delta.reviewed_by or "system")
        return True

    def _promote_action(self, delta: Delta) -> bool:
        """Promote an action template delta to the judgment store."""
        content = delta.content
        from .models import FunctionAction

        template = ActionTemplate(
            trigger_pattern_id=content.get("trigger_pattern_id", ""),
            expected_impact_metric=content.get("expected_impact_metric", ""),
            expected_impact_timeframe=content.get("expected_impact_timeframe", ""),
        )

        # Add actions for each function
        for action_data in content.get("brand_actions", []):
            template.brand_actions.append(FunctionAction(
                action=action_data.get("action"),
                priority=action_data.get("priority", "medium")
            ))
        for action_data in content.get("field_actions", []):
            template.field_actions.append(FunctionAction(
                action=action_data.get("action"),
                priority=action_data.get("priority", "medium")
            ))
        for action_data in content.get("access_actions", []):
            template.access_actions.append(FunctionAction(
                action=action_data.get("action"),
                priority=action_data.get("priority", "medium")
            ))

        self.judgment_store.add_action_template(template)
        self.judgment_store.approve_action_template(template.id, delta.reviewed_by or "system")
        return True


# =============================================================================
# CONTRIBUTION STORE
# =============================================================================

class ContributionStore:
    """Tracks SME contributions from game sessions."""

    def __init__(self):
        self._contributions: dict[str, Contribution] = {}
        self._by_sme_id: dict[str, list[str]] = defaultdict(list)
        self._by_therapeutic_area: dict[str, list[str]] = defaultdict(list)
        self._audit_log: list[AuditEntry] = []

    def record(self, event, delta_ids: list[str]) -> Contribution:
        """Create a contribution record from a ReasoningEvent."""
        ta = event.scenario.brand.therapeutic_area.value if event.scenario else ""
        contribution = Contribution(
            reasoning_event_id=event.id,
            sme_id=event.sme_id,
            sme_persona=event.sme_persona,
            delta_ids=list(delta_ids),
            contributed_at=event.captured_at,
            therapeutic_area=ta,
            scenario_type=event.scenario_type,
            sme_confidence=event.sme_confidence,
        )
        self._contributions[contribution.id] = contribution
        self._by_sme_id[contribution.sme_id].append(contribution.id)
        self._by_therapeutic_area[contribution.therapeutic_area].append(contribution.id)
        self._log_audit(
            "record", contribution.id,
            {"sme_id": contribution.sme_id, "deltas": len(delta_ids)},
            actor=contribution.sme_id, category="record",
        )
        return contribution

    def get_by_sme(self, sme_id: str, limit: int = 50) -> list[Contribution]:
        """Get contributions by SME, newest first."""
        ids = self._by_sme_id.get(sme_id, [])
        contribs = [self._contributions[cid] for cid in ids if cid in self._contributions]
        contribs.sort(key=lambda c: c.contributed_at, reverse=True)
        return contribs[:limit] if limit else contribs

    def get_contributor_summary(self, sme_id: str) -> dict[str, Any]:
        """Aggregated stats for a single SME."""
        contribs = self.get_by_sme(sme_id, limit=0)
        if not contribs:
            return {
                "sme_id": sme_id, "total_contributions": 0,
                "total_deltas": 0, "domains": {},
                "avg_confidence": 0.0, "last_contributed": None,
            }
        domains: dict[str, int] = defaultdict(int)
        total_deltas = 0
        conf_sum = 0.0
        for c in contribs:
            total_deltas += len(c.delta_ids)
            conf_sum += c.sme_confidence
            if c.therapeutic_area:
                domains[c.therapeutic_area] += 1
        return {
            "sme_id": sme_id,
            "total_contributions": len(contribs),
            "total_deltas": total_deltas,
            "domains": dict(domains),
            "avg_confidence": round(conf_sum / len(contribs), 3),
            "last_contributed": contribs[0].contributed_at,
        }

    def get_top_contributors(self, limit: int = 10) -> list[dict[str, Any]]:
        """Leaderboard ranked by total deltas generated."""
        sme_ids = list(self._by_sme_id.keys())
        summaries = [self.get_contributor_summary(sid) for sid in sme_ids]
        summaries.sort(key=lambda s: s["total_deltas"], reverse=True)
        return summaries[:limit]

    def stats(self) -> dict[str, Any]:
        """Store-level totals."""
        total_deltas = sum(len(c.delta_ids) for c in self._contributions.values())
        return {
            "total_contributions": len(self._contributions),
            "unique_smes": len(self._by_sme_id),
            "total_deltas": total_deltas,
        }

    def get_audit_log(self, limit: int = 100, action: str | None = None) -> list[AuditEntry]:
        """Return recent audit entries, optionally filtered by action."""
        entries = self._audit_log
        if action:
            entries = [e for e in entries if e.action == action]
        return list(reversed(entries[-limit:]))

    def _log_audit(
        self, action: str, artifact_id: str, details: dict,
        actor: str = "", category: str = "",
    ):
        """Record an audit entry with enhanced context."""
        self._audit_log.append(AuditEntry(
            actor=actor, action=action, artifact_id=artifact_id,
            details=details, store_type="contribution", action_category=category,
        ))


# =============================================================================
# UNIFIED AUDIT QUERY
# =============================================================================

def get_combined_audit_log(
    stores: list,
    limit: int = 100,
    action: str | None = None,
    actor: str | None = None,
    store_type: str | None = None,
) -> list[AuditEntry]:
    """Merge audit logs from multiple stores, sorted newest first."""
    all_entries: list[AuditEntry] = []
    for store in stores:
        all_entries.extend(store.get_audit_log(limit=9999))
    if action:
        all_entries = [e for e in all_entries if e.action == action]
    if actor:
        all_entries = [e for e in all_entries if e.actor == actor]
    if store_type:
        all_entries = [e for e in all_entries if e.store_type == store_type]
    all_entries.sort(key=lambda e: e.timestamp, reverse=True)
    return all_entries[:limit]
