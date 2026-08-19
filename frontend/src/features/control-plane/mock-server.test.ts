import { describe, expect, it } from 'vitest';

import {
  getArtifact,
  getSnapshot,
  MockApiError,
  performAction,
  runSimulation,
} from './mock-server';

describe('control-plane mock server', () => {
  it('exposes the actual Auravia reference inventory and 28-case gate', () => {
    const value = getSnapshot();
    const total = value.evalSuites.reduce((sum, suite) => sum + suite.total, 0);
    const passed = value.evalSuites.reduce((sum, suite) => sum + suite.passed, 0);

    expect(value.workspace.pack).toBe('Auravia US HCP Marketing');
    expect(total).toBe(28);
    expect(passed).toBe(27);
    expect(value.artifacts.some((item) => item.id === 'obs.new_to_brand_rx')).toBe(true);
  });

  it('fails unknown artifact requests with a typed 404 error', () => {
    expect(() => getArtifact('does-not-exist')).toThrow(MockApiError);
    try {
      getArtifact('does-not-exist');
    } catch (error) {
      expect(error).toMatchObject({ status: 404, code: 'ARTIFACT_NOT_FOUND' });
    }
  });

  it('abstains on the failed candidate and allows the corrected content workflow', () => {
    const blocked = runSimulation({ scenarioId: 'content-valid-us-hcp', mode: 'candidate', candidateQualified: false });
    const qualified = runSimulation({ scenarioId: 'content-valid-us-hcp', mode: 'candidate', candidateQualified: true });

    expect(blocked.decision).toBe('abstain');
    expect(blocked.findings).toContain('eval_missing_timepoint_block failed');
    expect(qualified.decision).toBe('allow_draft');
    expect(qualified.answer).toContain('at week 16');
    expect(qualified.artifactsUsed).toContain('risk_bundle_us_hcp_core');
  });

  it('returns exact governed analytics and refuses a causal email conclusion', () => {
    const result = runSimulation({ scenarioId: 'brand-diagnosis', mode: 'candidate', candidateQualified: true });

    expect(result.answer).toContain('920 versus plan 1,000');
    expect(result.answer).toContain('writer depth fell 10.1%');
    expect(result.answer).toContain('email causality is unresolved');
    expect(result.evidenceUsed).toContain('query_receipt_nbrx_vs_plan_w26');
  });

  it('makes simulated mutations explicit and receipt-bearing', () => {
    const receipt = performAction('apply_eval_correction');

    expect(receipt.status).toBe('accepted');
    expect(receipt.summary).toContain('0.1.1-rc2');
    expect(receipt.affectedArtifacts).toContain('eval_missing_timepoint_block');
  });
});
