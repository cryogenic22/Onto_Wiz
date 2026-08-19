export type ArtifactKind =
  | 'claim'
  | 'risk_bundle'
  | 'business_rule'
  | 'metric'
  | 'table_contract'
  | 'governed_join'
  | 'ontology_entity'
  | 'evaluation';

export type ArtifactStatus =
  | 'released'
  | 'candidate'
  | 'review_required'
  | 'stale'
  | 'rejected';

export type Severity = 'critical' | 'high' | 'medium' | 'low';

export interface WorkspaceContext {
  client: string;
  pack: string;
  market: string;
  environment: 'candidate';
  currentRelease: string;
  candidateRelease: string;
  refreshedAt: string;
}

export interface DomainSummary {
  id: string;
  name: string;
  description: string;
  artifactCount: number;
  evalCoverage: number;
  health: 'healthy' | 'at_risk' | 'building';
}

export interface ArtifactSummary {
  id: string;
  name: string;
  kind: ArtifactKind;
  domain: string;
  version: string;
  status: ArtifactStatus;
  owner: string;
  lastReviewed: string;
  nextReview: string;
  evalPassed: number;
  evalTotal: number;
  shortDefinition: string;
  tags: string[];
}

export interface EvidenceSpan {
  sourceId: string;
  sourceName: string;
  authority: 'authoritative' | 'governed' | 'supporting';
  locator: string;
  excerpt: string;
  version: string;
}

export interface Relationship {
  predicate: string;
  targetId: string;
  targetName: string;
}

export interface LineageStep {
  stage: string;
  artifact: string;
  receipt: string;
  at: string;
}

export interface ArtifactDetail extends ArtifactSummary {
  semanticDefinition: string;
  applicability: string[];
  prohibitedUses: string[];
  fields: Array<{ label: string; value: string }>;
  evidence: EvidenceSpan[];
  relationships: Relationship[];
  lineage: LineageStep[];
  affectedConsumers: string[];
  changeSummary: string;
}

export interface EvaluationSuite {
  id: string;
  workload: string;
  passed: number;
  total: number;
  criticalPassed: number;
  criticalTotal: number;
  categories: Array<{ name: string; passed: number; total: number }>;
}

export interface EvaluationCase {
  id: string;
  name: string;
  workload: string;
  severity: Severity;
  status: 'passed' | 'failed';
  input: string;
  expected: string;
  actual: string;
  tracedArtifacts: string[];
  owner: string;
  correction: string;
}

export interface StalenessEvent {
  id: string;
  severity: Severity;
  trigger: string;
  rootArtifact: string;
  state: 'at_risk' | 'stale' | 'blocked_pending_review';
  owner: string;
  effectiveDate: string;
  impacts: string[];
}

export interface SourceRecord {
  id: string;
  name: string;
  version: string;
  authority: 'authoritative' | 'governed' | 'supporting';
  state: 'current' | 'superseded' | 'quarantined';
  parsed: number;
  lastChecked: string;
}

export interface ActivityRecord {
  id: string;
  action: string;
  actor: string;
  artifact: string;
  at: string;
  receipt: string;
}

export interface ReleaseDiff {
  added: string[];
  changed: string[];
  invalidated: string[];
  layerPins: Array<{ layer: string; version: string; hash: string }>;
}

export interface ControlPlaneSnapshot {
  workspace: WorkspaceContext;
  domains: DomainSummary[];
  artifacts: ArtifactSummary[];
  sources: SourceRecord[];
  evalSuites: EvaluationSuite[];
  evalCases: EvaluationCase[];
  staleness: StalenessEvent[];
  activity: ActivityRecord[];
  releaseDiff: ReleaseDiff;
}

export type SimulationMode = 'candidate' | 'without_context';

export interface SimulationScenario {
  id: string;
  name: string;
  workload: string;
  prompt: string;
  market: string;
  audience: string;
}

export interface SimulationRequest {
  scenarioId: string;
  mode: SimulationMode;
  candidateQualified: boolean;
}

export interface SimulationResult {
  scenarioId: string;
  mode: SimulationMode;
  decision: 'allow_draft' | 'block' | 'return_with_findings' | 'answer' | 'abstain';
  confidence: number;
  answer: string;
  findings: string[];
  artifactsUsed: string[];
  evidenceUsed: string[];
  trace: Array<{ step: string; result: string; durationMs: number }>;
  receipt: {
    id: string;
    release: string;
    policyVersion: string;
    generatedAt: string;
    reproducible: boolean;
  };
}

export type ControlAction =
  | 'apply_eval_correction'
  | 'approve_risk_bundle'
  | 'compile_demo_release'
  | 'create_improvement_delta';

export interface ActionReceipt {
  id: string;
  action: ControlAction;
  status: 'accepted';
  summary: string;
  affectedArtifacts: string[];
  createdAt: string;
}
