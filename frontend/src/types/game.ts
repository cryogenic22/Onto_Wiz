/** Game session types — mirrors backend ReasoningEvent structure. */

export type GameStep =
  | 'scenario'
  | 'hypothesis'
  | 'signals'
  | 'disconfirm'
  | 'pattern'
  | 'mistakes'
  | 'actions'
  | 'confidence'
  | 'summary';

export const STEP_ORDER: GameStep[] = [
  'scenario',
  'hypothesis',
  'signals',
  'disconfirm',
  'pattern',
  'mistakes',
  'actions',
  'confidence',
  'summary',
];

export const STEP_LABELS: Record<GameStep, string> = {
  scenario: 'Review Scenario',
  hypothesis: 'First Instinct',
  signals: 'Key Signals',
  disconfirm: 'Change My Mind',
  pattern: 'Seen Before?',
  mistakes: 'Common Traps',
  actions: 'Next Steps',
  confidence: 'Your Confidence',
  summary: 'Session Complete',
};

export type HypothesisCategory =
  | 'commercial_execution'
  | 'market_access'
  | 'clinical_safety'
  | 'competitive_pressure'
  | 'demand_erosion'
  | 'supply_disruption'
  | 'too_early';

export const HYPOTHESIS_LABELS: Record<HypothesisCategory, string> = {
  commercial_execution: 'Commercial Execution',
  market_access: 'Market Access',
  clinical_safety: 'Clinical / Safety',
  competitive_pressure: 'Competitive Pressure',
  demand_erosion: 'Demand Erosion',
  supply_disruption: 'Supply Disruption',
  too_early: 'Too Early to Tell',
};

export interface HypothesisResponse {
  category: HypothesisCategory;
  specificDriver: string;
  confidence: number;
  reasoning: string;
}

export interface SignalResponse {
  signalName: string;
  role: 'validation' | 'disconfirming' | 'leading';
  priorityRank: number;
}

export interface DisconfirmResponse {
  condition: string;
  wouldSuggest: string;
  wouldRuleOut: string;
}

export interface PatternResponse {
  frequency: 'often' | 'sometimes' | 'rarely' | 'never';
  typicalOutcome: string;
  timeToResolution: string;
}

export interface MistakeResponse {
  wrongConclusion: string;
  whyWrong: string;
  unlessEvidence: string;
}

export interface ActionResponse {
  action: string;
  actionType: 'investigate' | 'escalate' | 'wait' | 'intervene';
  priority: number;
  ownerFunction: string;
}

export interface ConfidenceResponse {
  finalConfidence: number;
  reasoning: string;
}

export interface GameResponses {
  hypothesis?: HypothesisResponse;
  signals?: SignalResponse[];
  disconfirm?: DisconfirmResponse;
  pattern?: PatternResponse;
  mistakes?: MistakeResponse[];
  actions?: ActionResponse[];
  confidence?: ConfidenceResponse;
}

export interface GameSession {
  sessionId: string;
  scenarioId: string;
  currentStep: GameStep;
  responses: GameResponses;
  startedAt: number;
  completedAt?: number;
}
