import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { PackDetail, PackSummary } from '@/types/packs';
import PackExplorer from './PackExplorer';

/* ── Fixtures: shaped from the LIVE capture (D1.0 §2/§5c), not invented ────────── */

const BASE_PACK: Omit<PackSummary, 'version' | 'evals'> = {
  name: 'commercial_analytics',
  description: 'Commercial pharma base pack, seeded from commercial.yaml',
  domain: '',
  author: 'ontowiz',
  layers: [],
  depends_on: [],
  artifact_count: 20,
  artifact_kinds: { entity_registry: 1, decision_heuristic: 19 },
  coverage: 0.0,
  freshness_days: null,
  compiled_at: null,
  compiler_version: '0.1.0',
  signed: true,
  encrypted: false,
  license_id: null,
  ctx_l2_path: 'context.ctx',
  ctx_l3_path: 'index.l3.ctx',
};

/** The benchmarked pack — real evidence. */
const EVIDENCED: PackSummary = {
  ...BASE_PACK,
  version: '0.1.0',
  evals: {
    eval_cases: 26,
    pass_rate: 1.0,
    agent_lift: 0.308,
    last_run_at: '2026-06-12T00:16:08.040427+00:00',
    gate_passed: true,
  },
};

/** The LATEST pack — genuinely carries no eval evidence (live-verified 2026-07-22). */
const UNEVIDENCED: PackSummary = {
  ...BASE_PACK,
  version: '0.3.0',
  evals: {
    eval_cases: 0,
    pass_rate: 0.0,
    agent_lift: null,
    last_run_at: null,
    gate_passed: false,
  },
};

/** Detail is NOT a superset of the summary and carries no provenance — live-verified. */
const DETAIL: PackDetail = {
  name: 'commercial_analytics',
  version: '0.3.0',
  description: 'Commercial pharma base pack, seeded from commercial.yaml',
  artifact_count: 20,
  artifact_kinds: { entity_registry: 1, decision_heuristic: 19 },
  evals: UNEVIDENCED.evals,
  coverage: 0.0,
  gaps: ['rule_formulary_exclusion', 'commercial-entities'],
  artifacts: [
    {
      id: 'rule_formulary_exclusion',
      kind: 'decision_heuristic',
      name: 'Formulary Exclusion',
      lifecycle: 'active',
      confidence: 0.8,
      served: true,
      has_eval: false,
    },
  ],
};

const CONTEXT = {
  query: 'formulary exclusion',
  agent_type: 'general',
  system_prompt: 'You have a domain knowledge base…',
  eligible: ['rule_formulary_exclusion', 'rule_channel_shift'],
  trust: {
    pack: 'commercial_analytics@0.3.0',
    confidence: 0.808,
    lifecycle_floor: 'active',
    artifacts_used: ['rule_formulary_exclusion'],
  },
  tokens_estimate: 58,
};

/* ── fetch routing ────────────────────────────────────────────────────────────── */

function jsonResponse(body: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
  } as unknown as Response;
}

let fetchMock: ReturnType<typeof vi.fn>;

/** Route by URL so the component exercises the real client, not a mocked module. */
function routeOk(packs: PackSummary[] = [EVIDENCED, UNEVIDENCED]) {
  return (url: string, init?: RequestInit) => {
    if (init?.method === 'POST') return Promise.resolve(jsonResponse(CONTEXT));
    if (url.includes('/detail')) return Promise.resolve(jsonResponse(DETAIL));
    return Promise.resolve(jsonResponse(packs));
  };
}

beforeEach(() => {
  fetchMock = vi.fn(routeOk());
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

/* ── tests ────────────────────────────────────────────────────────────────────── */

describe('PackExplorer — real-data vertical slice', () => {
  it('renders a loading state before the packs resolve', () => {
    render(<PackExplorer />);
    expect(screen.getByTestId('packs-loading')).toBeInTheDocument();
  });

  it('renders each pack from the API with its version and artifact count', async () => {
    render(<PackExplorer />);
    const card = await screen.findByTestId('pack-card-commercial_analytics@0.1.0');
    expect(within(card).getByText(/0\.1\.0/)).toBeInTheDocument();
    expect(within(card).getByText(/20/)).toBeInTheDocument();
    expect(
      screen.getByTestId('pack-card-commercial_analytics@0.3.0'),
    ).toBeInTheDocument();
  });

  it('shows the real measured lift for an evidenced pack', async () => {
    render(<PackExplorer />);
    const card = await screen.findByTestId('pack-card-commercial_analytics@0.1.0');
    expect(within(card).getByTestId('eval-evidence')).toHaveTextContent('0.308');
    expect(within(card).queryByTestId('no-eval-evidence')).toBeNull();
  });

  // ── the load-bearing invariant (D1.0 §5b/§5c) ──
  it('shows an explicit "no eval evidence" state when eval_cases is 0', async () => {
    render(<PackExplorer />);
    const card = await screen.findByTestId('pack-card-commercial_analytics@0.3.0');
    expect(within(card).getByTestId('no-eval-evidence')).toBeInTheDocument();
    expect(within(card).getByTestId('no-eval-evidence')).toHaveTextContent(
      /no eval evidence/i,
    );
  });

  it('never leaks the benchmarked pack\'s lift onto the unevidenced pack', async () => {
    render(<PackExplorer />);
    const card = await screen.findByTestId('pack-card-commercial_analytics@0.3.0');
    expect(card.textContent).not.toContain('0.308');
    expect(within(card).queryByTestId('eval-evidence')).toBeNull();
  });

  it('reports an unsealed pack as unsealed', async () => {
    fetchMock.mockImplementation(
      routeOk([{ ...UNEVIDENCED, signed: false }]),
    );
    render(<PackExplorer />);
    const card = await screen.findByTestId('pack-card-commercial_analytics@0.3.0');
    expect(within(card).getByTestId('seal-state')).toHaveTextContent('unsealed');
  });

  it('never prints a null lift when cases ran but no lift was computed', async () => {
    fetchMock.mockImplementation(
      routeOk([
        {
          ...EVIDENCED,
          evals: { ...EVIDENCED.evals, agent_lift: null },
        },
      ]),
    );
    render(<PackExplorer />);
    const card = await screen.findByTestId('pack-card-commercial_analytics@0.1.0');
    const evidence = within(card).getByTestId('eval-evidence');
    expect(evidence.textContent).not.toMatch(/null/);
    expect(evidence).toHaveTextContent('26 cases');
  });

  it('does not render a failed gate in a passing tone', async () => {
    render(<PackExplorer />);
    const card = await screen.findByTestId('pack-card-commercial_analytics@0.3.0');
    const gate = within(card).getByTestId('gate-state');
    expect(gate.className).not.toMatch(/jade/);
  });

  it('loads detail and lists artifacts with their lifecycle when a pack is selected', async () => {
    render(<PackExplorer />);
    const card = await screen.findByTestId('pack-card-commercial_analytics@0.3.0');
    fireEvent.click(within(card).getByRole('button', { name: /inspect/i }));
    const row = await screen.findByTestId('artifact-row-rule_formulary_exclusion');
    expect(within(row).getByText(/Formulary Exclusion/)).toBeInTheDocument();
    expect(
      within(row).getByTestId('lifecycle-badge-active'),
    ).toBeInTheDocument();
  });

  it('renders "no provenance recorded" and emits no chip, because detail carries none', async () => {
    render(<PackExplorer />);
    const card = await screen.findByTestId('pack-card-commercial_analytics@0.3.0');
    fireEvent.click(within(card).getByRole('button', { name: /inspect/i }));
    const row = await screen.findByTestId('artifact-row-rule_formulary_exclusion');
    expect(within(row).getByTestId('provenance-none')).toHaveTextContent(
      /no provenance recorded/i,
    );
    expect(row.querySelector('[data-testid^="provenance-chip-"]')).toBeNull();
  });

  it('marks an artifact with has_eval=false as untested rather than silently blank', async () => {
    render(<PackExplorer />);
    const card = await screen.findByTestId('pack-card-commercial_analytics@0.3.0');
    fireEvent.click(within(card).getByRole('button', { name: /inspect/i }));
    const row = await screen.findByTestId('artifact-row-rule_formulary_exclusion');
    expect(within(row).getByTestId('artifact-untested')).toHaveTextContent(/untested/i);
  });

  it("surfaces the engine's own served-but-untested gap list", async () => {
    render(<PackExplorer />);
    const card = await screen.findByTestId('pack-card-commercial_analytics@0.3.0');
    fireEvent.click(within(card).getByRole('button', { name: /inspect/i }));
    expect(await screen.findByTestId('detail-gaps')).toHaveTextContent('2');
  });

  it('shows the trust envelope and token estimate returned by /v1/context', async () => {
    render(<PackExplorer />);
    const card = await screen.findByTestId('pack-card-commercial_analytics@0.3.0');
    fireEvent.click(within(card).getByRole('button', { name: /inspect/i }));
    const input = await screen.findByLabelText(/probe/i);
    fireEvent.change(input, { target: { value: 'formulary exclusion' } });
    fireEvent.click(screen.getByRole('button', { name: /run probe/i }));

    expect(await screen.findByTestId('trust-confidence')).toHaveTextContent('0.808');
    expect(screen.getByTestId('trust-floor')).toHaveTextContent(/active/i);
    expect(screen.getByTestId('tokens-estimate')).toHaveTextContent('58');
    expect(screen.getByTestId('eligible-rule_formulary_exclusion')).toBeInTheDocument();
  });

  // Guards the convergence risk in DESIGN_SYSTEM_CONVERGENCE §B: the control-plane
  // vocabulary ("candidate", "quarantined", …) is NOT yet ratified against ontowiz-spec.
  // If the backend ever serves one, the row must degrade to the raw string, never crash
  // and never be silently mapped onto a lifecycle it does not mean.
  it('renders an unrecognised lifecycle verbatim instead of guessing a badge', async () => {
    fetchMock.mockImplementation((url: string, init?: RequestInit) => {
      if (init?.method === 'POST') return Promise.resolve(jsonResponse(CONTEXT));
      if (url.includes('/detail'))
        return Promise.resolve(
          jsonResponse({
            ...DETAIL,
            artifacts: [
              { ...DETAIL.artifacts[0], id: 'weird', lifecycle: 'candidate' },
              { ...DETAIL.artifacts[0], id: 'tested', has_eval: true },
            ],
          }),
        );
      return Promise.resolve(jsonResponse([UNEVIDENCED]));
    });

    render(<PackExplorer />);
    const card = await screen.findByTestId('pack-card-commercial_analytics@0.3.0');
    fireEvent.click(within(card).getByRole('button', { name: /inspect/i }));

    const row = await screen.findByTestId('artifact-row-weird');
    expect(within(row).getByText('candidate')).toBeInTheDocument();
    expect(row.querySelector('[data-testid^="lifecycle-badge-"]')).toBeNull();

    const tested = screen.getByTestId('artifact-row-tested');
    expect(within(tested).getByTestId('artifact-tested')).toHaveTextContent(
      /eval covered/i,
    );
  });

  it('surfaces a probe failure inline without clearing the detail panel', async () => {
    render(<PackExplorer />);
    const card = await screen.findByTestId('pack-card-commercial_analytics@0.3.0');
    fireEvent.click(within(card).getByRole('button', { name: /inspect/i }));
    await screen.findByTestId('detail-gaps');

    fetchMock.mockResolvedValue(jsonResponse({ detail: 'pack not loaded' }, 503));
    fireEvent.change(await screen.findByLabelText(/probe/i), {
      target: { value: 'anything' },
    });
    fireEvent.click(screen.getByRole('button', { name: /run probe/i }));

    expect(await screen.findByTestId('probe-error')).toHaveTextContent(
      /pack not loaded/i,
    );
    expect(screen.getByTestId('detail-gaps')).toBeInTheDocument();
    expect(screen.queryByTestId('trust-confidence')).toBeNull();
  });

  it('renders an error state (not an empty list) when the backend fails', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: 'boom' }, 500));
    render(<PackExplorer />);
    const err = await screen.findByTestId('packs-error');
    expect(err).toHaveTextContent(/500/);
    expect(screen.queryByTestId('packs-empty')).toBeNull();
  });

  it('retries the fetch from the error state', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: 'boom' }, 500));
    render(<PackExplorer />);
    await screen.findByTestId('packs-error');
    fetchMock.mockImplementation(routeOk());
    fireEvent.click(screen.getByRole('button', { name: /retry/i }));
    expect(
      await screen.findByTestId('pack-card-commercial_analytics@0.1.0'),
    ).toBeInTheDocument();
  });

  it('renders an empty state when the backend returns zero packs', async () => {
    fetchMock.mockImplementation(routeOk([]));
    render(<PackExplorer />);
    expect(await screen.findByTestId('packs-empty')).toBeInTheDocument();
  });

  it('surfaces a detail-fetch failure without discarding the pack list', async () => {
    render(<PackExplorer />);
    const card = await screen.findByTestId('pack-card-commercial_analytics@0.3.0');
    fetchMock.mockResolvedValue(jsonResponse({ detail: 'gone' }, 404));
    fireEvent.click(within(card).getByRole('button', { name: /inspect/i }));
    await waitFor(() =>
      expect(screen.getByTestId('detail-error')).toHaveTextContent(/404/),
    );
    expect(
      screen.getByTestId('pack-card-commercial_analytics@0.1.0'),
    ).toBeInTheDocument();
  });
});
