import { artifactDetails, scenarios, snapshot } from './mock-data';
import type {
  ActionReceipt,
  ControlAction,
  SimulationRequest,
  SimulationResult,
} from './types';

export class MockApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: string,
  ) {
    super(message);
    this.name = 'MockApiError';
  }
}

export const getSnapshot = () => snapshot;

export const getArtifact = (artifactId: string) => {
  const artifact = artifactDetails[artifactId];
  if (!artifact) {
    throw new MockApiError(`Artifact ${artifactId} was not found.`, 404, 'ARTIFACT_NOT_FOUND');
  }
  return artifact;
};

const simulationBase = (
  request: SimulationRequest,
  result: Omit<SimulationResult, 'scenarioId' | 'mode' | 'receipt'>,
): SimulationResult => ({
  ...result,
  scenarioId: request.scenarioId,
  mode: request.mode,
  receipt: {
    id: `sim_${request.scenarioId}_${request.mode}`,
    release: request.mode === 'candidate' ? '0.1.1-rc2' : 'unmanaged-context',
    policyVersion: request.mode === 'candidate' ? 'auravia-policy@1.0.0' : 'none',
    generatedAt: '2026-06-25T10:04:20Z',
    reproducible: true,
  },
});

const withoutContext = (request: SimulationRequest): SimulationResult => {
  const common = {
    confidence: 0.58,
    artifactsUsed: [],
    evidenceUsed: [],
    trace: [
      { step: 'Prompt retrieval', result: 'Ungoverned semantic similarity only', durationMs: 71 },
      { step: 'Policy resolution', result: 'No typed policy contract available', durationMs: 2 },
      { step: 'Answer generation', result: 'Answer emitted without a release receipt', durationMs: 386 },
    ],
  };

  switch (request.scenarioId) {
    case 'content-valid-us-hcp':
      return simulationBase(request, {
        ...common,
        decision: 'allow_draft',
        answer: 'Auravia delivered meaningful EASI-75 results in adults. Ask your representative whether Auravia is right for your patients.',
        findings: ['Week-16 timepoint omitted', 'Placebo comparator omitted', 'Required risk bundle omitted', 'No human-review state attached'],
      });
    case 'mlr-overclaim':
      return simulationBase(request, {
        ...common,
        decision: 'allow_draft',
        answer: 'No obvious spelling or grammar issues were found.',
        findings: ['Unsupported superiority was not detected', 'Absolute safety language was not detected'],
      });
    case 'brand-diagnosis':
      return simulationBase(request, {
        ...common,
        decision: 'answer',
        answer: 'Email underperformance likely caused the 8% NBRx miss. Consider shifting spend toward field activity.',
        findings: ['Causal assertion without an experiment', 'No metric versions or query receipt', 'Provisional-period status omitted'],
      });
    case 'omni-frequency':
      return simulationBase(request, {
        ...common,
        decision: 'answer',
        answer: 'Send the next approved HCP email and follow up through the field team.',
        findings: ['Email frequency cap missed', 'Channel exclusion was not independently evaluated'],
      });
    default:
      throw new MockApiError('Unknown simulation scenario.', 422, 'INVALID_SCENARIO');
  }
};

export const runSimulation = (request: SimulationRequest): SimulationResult => {
  if (!scenarios.some((scenario) => scenario.id === request.scenarioId)) {
    throw new MockApiError('Unknown simulation scenario.', 422, 'INVALID_SCENARIO');
  }
  if (request.mode === 'without_context') return withoutContext(request);

  const traceStart = [
    { step: 'Scope resolution', result: 'synthetic_client / brand_auravia / governed market and audience', durationMs: 18 },
    { step: 'Pack selection', result: request.candidateQualified ? '0.1.1-rc2 / reference gate passed' : '0.1.1-rc1 / critical gate failed', durationMs: 12 },
  ];

  if (request.scenarioId === 'content-valid-us-hcp' && !request.candidateQualified) {
    return simulationBase(request, {
      decision: 'abstain',
      confidence: 1,
      answer: 'Draft generation is withheld because the candidate claim variant failed a critical semantic-invariant evaluation.',
      findings: ['eval_missing_timepoint_block failed', 'Restore timepoint_week_16 and recompile the candidate'],
      artifactsUsed: ['claim_variant_easi75_us_hcp_v1', 'eval_missing_timepoint_block'],
      evidenceUsed: [],
      trace: [...traceStart, { step: 'Release gate', result: 'ABSTAIN: critical evaluation failure', durationMs: 6 }],
    });
  }

  switch (request.scenarioId) {
    case 'content-valid-us-hcp':
      return simulationBase(request, {
        decision: 'allow_draft',
        confidence: 0.98,
        answer: 'In the synthetic VELA-1 fixture, 62% of trial-eligible adults receiving fictional Auravia achieved EASI-75 at week 16, compared with 28% receiving placebo. Fictional safety statement for architecture testing only. Refer to the complete synthetic prescribing-information fixture. DRAFT REQUIRES HUMAN MLR.',
        findings: ['All required qualifiers preserved', 'Risk bundle coupled', 'Asset-level visual review remains required'],
        artifactsUsed: ['claim_auravia_easi75_week16', 'claim_variant_easi75_us_hcp_v1', 'risk_bundle_us_hcp_core'],
        evidenceUsed: ['VELA-1 / Table 2 / EASI-75 week 16', 'Synthetic US label / Clinical studies'],
        trace: [...traceStart, { step: 'Claim resolution', result: 'Eligible claim and exact variant resolved', durationMs: 42 }, { step: 'Risk coupling', result: 'risk_bundle_us_hcp_core attached', durationMs: 17 }, { step: 'Contract response', result: 'ALLOW_DRAFT_WORKFLOW; human MLR required', durationMs: 211 }],
      });
    case 'mlr-overclaim':
      return simulationBase(request, {
        decision: 'return_with_findings',
        confidence: 1,
        answer: 'Return the draft for correction. Automated preflight is not MLR approval.',
        findings: ['CRITICAL: unsupported superiority', 'CRITICAL: side-effect-free safety minimization', 'CRITICAL: required risk information missing'],
        artifactsUsed: ['claim_auravia_easi75_week16', 'risk_bundle_us_hcp_core', 'policy_us_hcp_synthetic_promotion'],
        evidenceUsed: ['VELA-1 / limitations', 'Synthetic US label / warnings and precautions'],
        trace: [...traceStart, { step: 'Semantic comparison', result: 'Unsupported SUPERIOR proposition detected', durationMs: 54 }, { step: 'Risk validation', result: 'Absolute safety wording and missing bundle detected', durationMs: 31 }, { step: 'Decision', result: 'RETURN_WITH_FINDINGS', durationMs: 7 }],
      });
    case 'brand-diagnosis':
      return simulationBase(request, {
        decision: 'answer',
        confidence: 0.93,
        answer: 'Northeast NBRx was 920 versus plan 1,000: -80 (-8.0%). Active writers rose 2.8%, while writer depth fell 10.1%. Paid-claim rate declined from 74% to 67%, with 75% of the shortfall concentrated in two synthetic plans. Reach was stable at 68% and the email engagement proxy rose from 20% to 21%. Access friction is supported for investigation; email causality is unresolved because no controlled experiment exists.',
        findings: ['Period is provisional', 'Provider completeness is 98.7%, below the 99% warning threshold', 'No autonomous budget reallocation permitted'],
        artifactsUsed: ['obs.new_to_brand_rx', 'obs.active_writers', 'obs.writer_depth', 'obs.paid_claim_rate'],
        evidenceUsed: ['fixture_auravia_northeast_2026_w26', 'query_receipt_nbrx_vs_plan_w26'],
        trace: [...traceStart, { step: 'Metric contracts', result: '4 metric versions and 2 governed joins resolved', durationMs: 63 }, { step: 'Fixture query', result: 'Snapshot provider_snapshot_2026_w26_r1', durationMs: 284 }, { step: 'Causal check', result: 'UNRESOLVED_NO_CONTROLLED_EXPERIMENT', durationMs: 36 }, { step: 'Trust envelope', result: 'Query receipt attached', durationMs: 11 }],
      });
    case 'omni-frequency':
      return simulationBase(request, {
        decision: 'answer',
        confidence: 0.99,
        answer: 'Exclude HCP email because two valid deliveries occurred in the rolling 14-day window. Propose field follow-up for human workflow if its independent eligibility and suppression checks remain valid. Approved web remains conditionally eligible after authentication.',
        findings: ['Email blocked for this decision only', 'No silent channel substitution', 'Autonomous execution is not permitted'],
        artifactsUsed: ['contact_policy_us_hcp_email_v1', 'action_propose_field_followup', 'suppress_frequency_limit'],
        evidenceUsed: ['decision_synthetic_frequency_block_v1'],
        trace: [...traceStart, { step: 'Consent and suppression', result: 'Current and permitted', durationMs: 49 }, { step: 'Frequency evaluation', result: '2 / 2 valid deliveries; email excluded', durationMs: 24 }, { step: 'Independent channel checks', result: 'Field proposal eligible; web conditional', durationMs: 32 }],
      });
    default:
      throw new MockApiError('Unknown simulation scenario.', 422, 'INVALID_SCENARIO');
  }
};

const actionCopy: Record<ControlAction, { summary: string; artifacts: string[] }> = {
  apply_eval_correction: {
    summary: 'Restored timepoint_week_16, compiled 0.1.1-rc2 and reran the affected deterministic cases.',
    artifacts: ['claim_variant_easi75_us_hcp_v1', 'eval_missing_timepoint_block'],
  },
  approve_risk_bundle: {
    summary: 'Recorded a synthetic scoped review decision for the US HCP risk bundle.',
    artifacts: ['risk_bundle_us_hcp_core'],
  },
  compile_demo_release: {
    summary: 'Published qualified reference candidate 0.1.1-rc2 to the demo environment.',
    artifacts: ['0.1.1-rc2'],
  },
  create_improvement_delta: {
    summary: 'Created a candidate Delta from simulator feedback; no released artifact changed.',
    artifacts: ['delta_simulator_feedback_001'],
  },
};

export const performAction = (action: ControlAction): ActionReceipt => {
  const copy = actionCopy[action];
  if (!copy) throw new MockApiError('Unsupported control action.', 422, 'INVALID_ACTION');
  return {
    id: `act_${action}_20260625`,
    action,
    status: 'accepted',
    summary: copy.summary,
    affectedArtifacts: copy.artifacts,
    createdAt: '2026-06-25T10:06:00Z',
  };
};
