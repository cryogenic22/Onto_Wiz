/** Pack Explorer types (D1.0).
 *
 * Transcribed from a LIVE `ontowiz-serve` capture (2026-07-22), not hand-designed:
 *   GET  /v1/packs
 *   GET  /v1/packs/{name}/{version}/detail
 *   POST /v1/context
 *
 * Endpoint shapes are BE-owned (Tier A read API). This file mirrors them; it does not
 * propose them. Optional/nullable fields are nullable here because the live responses
 * genuinely return `null` for them on the seeded packs.
 */

/** Eval evidence attached to a compiled pack. */
export interface PackEvals {
  eval_cases: number;
  pass_rate: number;
  /** `null` when the pack has never been benchmarked (true of `@0.3.0` today). */
  agent_lift: number | null;
  last_run_at: string | null;
  gate_passed: boolean;
}

/** A row from `GET /v1/packs`. */
export interface PackSummary {
  name: string;
  version: string;
  description: string;
  domain: string;
  author: string;
  layers: string[];
  depends_on: string[];
  artifact_count: number;
  artifact_kinds: Record<string, number>;
  evals: PackEvals;
  coverage: number;
  freshness_days: number | null;
  compiled_at: string | null;
  compiler_version: string;
  /** SHA-256 integrity seal present — integrity, NOT PKI authorship (see PROJECT_STATUS). */
  signed: boolean;
  encrypted: boolean;
  license_id: string | null;
  ctx_l2_path: string;
  ctx_l3_path: string;
}

/** One artifact row inside `GET /v1/packs/{n}/{v}/detail`.
 *
 * NOTE (live-verified 2026-07-22): the detail endpoint carries **no provenance field**.
 * `sources` is declared optional-and-absent on purpose so the UI renders an honest
 * "no provenance recorded" rather than implying provenance it was never given.
 * Real lineage lives on `/v1/packs/{n}/{v}/explain` — out of scope for D1.0 (→ D0.14).
 */
export interface PackArtifact {
  id: string;
  kind: string;
  name: string;
  lifecycle: string;
  confidence: number;
  served: boolean;
  has_eval: boolean;
  sources?: string[];
}

/** `GET /v1/packs/{name}/{version}/detail`.
 *
 * Deliberately NOT `extends PackSummary`: the live detail response returns only these
 * nine keys — it omits `signed`/`author`/`domain`/`layers`/`compiled_at`/… that the list
 * endpoint carries. Typing it as a superset would have invented fields.
 */
export interface PackDetail {
  name: string;
  version: string;
  description: string;
  artifact_count: number;
  artifact_kinds: Record<string, number>;
  evals: PackEvals;
  coverage: number;
  artifacts: PackArtifact[];
  /** Served-but-untested artifact ids — the engine's own eval-coverage gap list. */
  gaps: string[];
}

/** The trust envelope returned alongside compiled context. */
export interface TrustEnvelope {
  /** `"name@version"`. */
  pack: string;
  confidence: number;
  lifecycle_floor: string;
  artifacts_used: string[];
}

/** `POST /v1/context` response. */
export interface ContextResponse {
  query: string;
  agent_type: string;
  system_prompt: string;
  /** Artifact ids that passed the relevance + lifecycle gate, most relevant first. */
  eligible: string[];
  trust: TrustEnvelope;
  tokens_estimate: number;
}

/** Request body for `POST /v1/context`. */
export interface ContextRequest {
  pack_name: string;
  pack_version: string;
  query: string;
  agent_type?: string;
}

/** True when a pack carries no eval evidence at all (invariant 5b). */
export function hasEvalEvidence(evals: PackEvals): boolean {
  return evals.eval_cases > 0;
}
