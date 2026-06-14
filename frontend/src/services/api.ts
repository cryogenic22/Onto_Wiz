/** Backend API wrapper. */

import type { Scenario, SessionResult, SessionDetail } from '@/types/api';
import type { GameResponses } from '@/types/game';
import type { ReviewQueueItem, QueueStatsResponse, AuditEntry, DeltaForReview } from '@/types/curator';
import type { ContributionStats, ContributorSummary, Contribution } from '@/types/sme';

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export async function fetchScenarios(): Promise<Scenario[]> {
  const res = await fetch(`${BASE_URL}/scenarios`);
  if (!res.ok) throw new Error(`Failed to fetch scenarios: ${res.status}`);
  return res.json();
}

export async function submitGameSession(
  scenarioId: string,
  responses: GameResponses,
): Promise<SessionResult> {
  const res = await fetch(`${BASE_URL}/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenarioId, ...responses }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const msg = body?.detail ?? body?.message ?? `Session submit failed: ${res.status}`;
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
  }
  return res.json();
}

export async function fetchSessionDetail(sessionId: string): Promise<SessionDetail> {
  const res = await fetch(`${BASE_URL}/sessions/${sessionId}`);
  if (!res.ok) throw new Error(`Failed to fetch session: ${res.status}`);
  return res.json();
}

// =============================================================================
// CURATOR DASHBOARD API
// =============================================================================

export async function fetchReviewQueue(
  role?: string,
  limit: number = 50,
): Promise<ReviewQueueItem[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (role) params.set('role', role);
  const res = await fetch(`${BASE_URL}/review-queue?${params}`);
  if (!res.ok) throw new Error(`Failed to fetch review queue: ${res.status}`);
  return res.json();
}

export async function fetchQueueStats(): Promise<QueueStatsResponse> {
  const res = await fetch(`${BASE_URL}/review-queue/stats`);
  if (!res.ok) throw new Error(`Failed to fetch queue stats: ${res.status}`);
  return res.json();
}

export async function approveDelta(
  deltaId: string,
  reviewer: string,
): Promise<DeltaForReview> {
  const res = await fetch(`${BASE_URL}/deltas/${deltaId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reviewer }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `Approve failed: ${res.status}`);
  }
  return res.json();
}

export async function rejectDelta(
  deltaId: string,
  reviewer: string,
  reason: string,
): Promise<DeltaForReview> {
  const res = await fetch(`${BASE_URL}/deltas/${deltaId}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reviewer, reason }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `Reject failed: ${res.status}`);
  }
  return res.json();
}

export async function escalateDelta(
  deltaId: string,
  reason: string,
): Promise<DeltaForReview> {
  const res = await fetch(`${BASE_URL}/deltas/${deltaId}/escalate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `Escalate failed: ${res.status}`);
  }
  return res.json();
}

export async function fetchAuditLog(
  limit: number = 50,
  store?: string,
): Promise<AuditEntry[]> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (store) params.set('store', store);
  const res = await fetch(`${BASE_URL}/audit-log?${params}`);
  if (!res.ok) throw new Error(`Failed to fetch audit log: ${res.status}`);
  return res.json();
}

export async function exportAuditLog(limit: number = 500): Promise<Blob> {
  const res = await fetch(`${BASE_URL}/audit-log/export?limit=${limit}`);
  if (!res.ok) throw new Error(`Failed to export audit log: ${res.status}`);
  return res.blob();
}

// =============================================================================
// SME IMPACT DASHBOARD API
// =============================================================================

export async function fetchContributionStats(): Promise<ContributionStats> {
  const res = await fetch(`${BASE_URL}/contributions/stats`);
  if (!res.ok) throw new Error(`Failed to fetch contribution stats: ${res.status}`);
  return res.json();
}

export async function fetchTopContributors(limit: number = 10): Promise<ContributorSummary[]> {
  const res = await fetch(`${BASE_URL}/contributors/top?limit=${limit}`);
  if (!res.ok) throw new Error(`Failed to fetch top contributors: ${res.status}`);
  return res.json();
}

export async function fetchContributorSummary(smeId: string): Promise<ContributorSummary> {
  const res = await fetch(`${BASE_URL}/contributors/${smeId}/summary`);
  if (!res.ok) throw new Error(`Failed to fetch contributor summary: ${res.status}`);
  return res.json();
}

export async function fetchSmeContributions(smeId: string, limit: number = 50): Promise<Contribution[]> {
  const res = await fetch(`${BASE_URL}/contributors/${smeId}/contributions?limit=${limit}`);
  if (!res.ok) throw new Error(`Failed to fetch SME contributions: ${res.status}`);
  return res.json();
}
