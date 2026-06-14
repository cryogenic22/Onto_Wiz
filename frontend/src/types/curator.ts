/** Curator Dashboard types — mirrors backend HITL + Audit schemas. */

export interface DeltaForReview {
  id: string;
  type: string;
  status: string;
  content: Record<string, unknown>;
  confidence: number;
  blast_radius: string;
  evidence_pointers: string[];
  impacted_missions: string[];
  impacted_personas: string[];
  created_at: string;
  reviewed_at: string | null;
  reviewed_by: string | null;
  rejection_reason: string | null;
  source_type: string;
  auto_approved: boolean;
}

export interface ReviewQueueItem {
  delta: DeltaForReview;
  queue: string;
  assigned_to: string;
  priority: string;
  sla_hours: number;
  reason: string;
  judgment_type: string;
}

export interface QueueStatsResponse {
  auto: number;
  standard: number;
  escalated: number;
  total_pending: number;
}

export interface AuditEntry {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  artifact_id: string;
  details: Record<string, unknown>;
}
