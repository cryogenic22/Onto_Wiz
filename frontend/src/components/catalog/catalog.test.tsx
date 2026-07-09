import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import type { ArtifactView, CatalogEntry, FunctionSlice } from '@/types/catalog';

import ArtifactDrawer from './ArtifactDrawer';
import ArtifactList from './ArtifactList';
import CatalogGrid from './CatalogGrid';
import FunctionSlices from './FunctionSlices';
import LoginBar from './LoginBar';
import PackCard from './PackCard';

const ENTRY: CatalogEntry = {
  name: 'commercial_analytics',
  domain: 'commercial',
  description: 'Pharma commercial judgment.',
  latest_version: '0.3.0',
  versions: ['0.3.0', '0.1.0'],
  artifact_count: 24,
  functions: { market_access: 9, forecasting: 4 },
  signed: true,
  eval_cases: 30,
  pass_rate: 1.0,
  agent_lift: 0.308,
  coverage: 1.0,
};

describe('PackCard', () => {
  it('renders the entry and fires onOpen', () => {
    const onOpen = vi.fn();
    render(<PackCard entry={ENTRY} onOpen={onOpen} />);
    expect(screen.getByText('commercial')).toBeInTheDocument();
    expect(screen.getByText(/lift/)).toHaveTextContent('+0.308');
    expect(screen.getByText('● sealed')).toBeInTheDocument();
    fireEvent.click(screen.getByTestId('pack-commercial_analytics'));
    expect(onOpen).toHaveBeenCalledWith(ENTRY);
  });
});

describe('CatalogGrid', () => {
  it('renders cards', () => {
    render(<CatalogGrid entries={[ENTRY]} onOpen={vi.fn()} />);
    expect(screen.getByTestId('pack-commercial_analytics')).toBeInTheDocument();
  });
  it('shows an empty state', () => {
    render(<CatalogGrid entries={[]} onOpen={vi.fn()} />);
    expect(screen.getByText('No packs match.')).toBeInTheDocument();
  });
});

const SLICES: FunctionSlice[] = [
  { function: 'market_access', count: 9, served_count: 9, eval_count: 5, slice_tokens: 120, full_tokens: 400 },
  { function: 'forecasting', count: 4, served_count: 4, eval_count: 4, slice_tokens: 80, full_tokens: 400 },
];

describe('FunctionSlices', () => {
  it('selects a slice and shows the token-leanness note', () => {
    const onSelect = vi.fn();
    const { rerender } = render(
      <FunctionSlices slices={SLICES} total={24} active="all" onSelect={onSelect} />,
    );
    fireEvent.click(screen.getByText('forecasting · 4'));
    expect(onSelect).toHaveBeenCalledWith('forecasting');
    rerender(<FunctionSlices slices={SLICES} total={24} active="forecasting" onSelect={onSelect} />);
    expect(screen.getByText(/≈ 80 tokens vs 400/)).toBeInTheDocument();
  });
});

describe('ArtifactList', () => {
  const rows = [
    { id: 'rule_a', name: 'Rule A', kind: 'DecisionHeuristic', served: true, has_eval: true, lifecycle: 'active' },
    { id: 'rule_b', name: 'Rule B', kind: 'DecisionHeuristic', served: false, has_eval: false, lifecycle: 'active' },
  ];
  it('renders rows with served/gated pills and opens one', () => {
    const onOpen = vi.fn();
    render(<ArtifactList rows={rows} onOpen={onOpen} />);
    expect(screen.getByText('served')).toBeInTheDocument();
    expect(screen.getByText('gated')).toBeInTheDocument();
    fireEvent.click(screen.getByTestId('artifact-rule_a'));
    expect(onOpen).toHaveBeenCalledWith('rule_a');
  });
  it('shows an empty slice state', () => {
    render(<ArtifactList rows={[]} onOpen={vi.fn()} />);
    expect(screen.getByText('No artifacts in this slice.')).toBeInTheDocument();
  });
});

const ARTIFACT: ArtifactView = {
  id: 'rule_formulary_exclusion',
  kind: 'DecisionHeuristic',
  name: 'Formulary exclusion',
  lifecycle: 'active',
  served: true,
  confidence: 0.9,
  function: 'market_access',
  therapy: null,
  summary: 'Payer-driven access loss, not a demand problem.',
  content: {},
  anti_patterns: [{ wrong_conclusion: 'a demand problem', why_wrong: 'the trigger is payer policy' }],
  trigger_signals: [],
  sources: [],
  governance: [{ to_state: 'active', changed_by: 'curator', delta_id: 'D-1182' }],
  has_eval: true,
  yaml: 'id: rule_formulary_exclusion',
  tags: [{ dimension: 'function', value: 'market_access' }],
};

describe('ArtifactDrawer', () => {
  it('renders verdict, anti-patterns, governance, yaml and posts a comment', () => {
    const onPost = vi.fn();
    const onClose = vi.fn();
    render(
      <ArtifactDrawer
        artifact={ARTIFACT}
        comments={[{ pack: 'p', version: '0.3.0', artifact_id: ARTIFACT.id, author: 'Priya', role: 'sme', text: 'agreed', created_at: 'x' }]}
        canReview={false}
        onClose={onClose}
        onPostComment={onPost}
        onReview={vi.fn()}
      />,
    );
    expect(screen.getByText(/Payer-driven access loss/)).toBeInTheDocument();
    expect(screen.getByText(/Not →/)).toBeInTheDocument();
    expect(screen.getByText(/active by curator · D-1182/)).toBeInTheDocument();
    expect(screen.getByText('id: rule_formulary_exclusion')).toBeInTheDocument();
    expect(screen.getByText('Priya')).toBeInTheDocument();
    // a blank comment is ignored; a real one fires the callback and clears
    fireEvent.click(screen.getByText('Post'));
    expect(onPost).not.toHaveBeenCalled();
    const input = screen.getByLabelText('Comment');
    fireEvent.change(input, { target: { value: 'looks right' } });
    fireEvent.click(screen.getByText('Post'));
    expect(onPost).toHaveBeenCalledWith('looks right');
    expect((input as HTMLInputElement).value).toBe('');
    fireEvent.click(screen.getByLabelText('Close'));
    expect(onClose).toHaveBeenCalled();
  });

  it('shows review actions only when permitted', () => {
    const onReview = vi.fn();
    const { rerender } = render(
      <ArtifactDrawer artifact={ARTIFACT} comments={[]} canReview={false} onClose={vi.fn()} onPostComment={vi.fn()} onReview={onReview} />,
    );
    expect(screen.queryByText('Approve')).toBeNull();
    expect(screen.getByText('No comments yet.')).toBeInTheDocument();
    rerender(
      <ArtifactDrawer artifact={ARTIFACT} comments={[]} canReview onClose={vi.fn()} onPostComment={vi.fn()} onReview={onReview} />,
    );
    fireEvent.click(screen.getByText('Approve'));
    expect(onReview).toHaveBeenCalledWith('approve');
  });
});

describe('LoginBar', () => {
  it('submits credentials when signed out', () => {
    const onLogin = vi.fn();
    render(<LoginBar principal={null} onLogin={onLogin} onLogout={vi.fn()} error="bad creds" />);
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'c@x.io' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'pw' } });
    fireEvent.click(screen.getByText('Sign in'));
    expect(onLogin).toHaveBeenCalledWith('c@x.io', 'pw');
    expect(screen.getByRole('alert')).toHaveTextContent('bad creds');
  });

  it('shows the principal and signs out', () => {
    const onLogout = vi.fn();
    render(
      <LoginBar principal={{ sub: 'curator', role: 'curator', email: 'c@x.io' }} onLogin={vi.fn()} onLogout={onLogout} />,
    );
    expect(screen.getByText('c@x.io')).toBeInTheDocument();
    expect(screen.getByText('curator')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Sign out'));
    expect(onLogout).toHaveBeenCalled();
  });
});
