/** Catalog API types — mirror the ontowiz-runtime dataclasses (Tier A). */

export interface CatalogEntry {
  name: string;
  domain: string;
  description: string;
  latest_version: string;
  versions: string[];
  artifact_count: number;
  functions: Record<string, number>;
  signed: boolean;
  eval_cases: number;
  pass_rate: number;
  agent_lift: number | null;
  coverage: number;
}

export interface FunctionSlice {
  function: string;
  count: number;
  served_count: number;
  eval_count: number;
  slice_tokens: number;
  full_tokens: number;
}

export interface MatchedArtifact {
  id: string;
  name?: string;
  kind?: string;
}

export interface SearchHit {
  name: string;
  domain: string;
  latest_version: string;
  score: number;
  functions: Record<string, number>;
  matched_artifacts: MatchedArtifact[];
}

export interface ArtifactRow {
  id: string;
  name: string;
  kind: string;
  served: boolean;
  has_eval: boolean;
  lifecycle: string;
}

export interface PackDetail {
  name: string;
  version: string;
  description: string;
  artifact_count: number;
  artifact_kinds: Record<string, number>;
  evals: Record<string, unknown>;
  coverage: number;
  artifacts: ArtifactRow[];
  gaps: string[];
}

export interface AntiPattern {
  wrong_conclusion: string;
  why_wrong: string;
}

export interface GovernanceStep {
  to_state: string;
  changed_by: string;
  delta_id?: string | null;
}

export interface ArtifactTag {
  dimension: string;
  value: string;
}

export interface ArtifactView {
  id: string;
  kind: string;
  name: string;
  lifecycle: string;
  served: boolean;
  confidence: number;
  function: string | null;
  therapy: string | null;
  summary: string;
  content: Record<string, unknown>;
  anti_patterns: AntiPattern[];
  trigger_signals: Array<Record<string, unknown>>;
  sources: string[];
  governance: GovernanceStep[];
  has_eval: boolean;
  yaml: string;
  tags: ArtifactTag[];
}

export interface Comment {
  pack: string;
  version: string;
  artifact_id: string;
  author: string;
  role: string;
  text: string;
  created_at: string;
}

export interface DiffResult {
  name: string;
  from_version: string;
  to_version: string;
  added: string[];
  removed: string[];
  changed: string[];
  function_deltas: Record<string, { from: number; to: number; delta: number }>;
}

export interface PackUsage {
  pack: string;
  consults: number;
  hits: number;
  hit_rate: number;
  by_function: Record<string, number>;
}

/** Auth */
export interface LoginResponse {
  access_token: string;
  token_type: string;
  role: string;
  email: string;
}

export interface Principal {
  sub: string;
  role: string;
  email: string;
}

export type RoleCapabilities = Record<string, string[]>;
