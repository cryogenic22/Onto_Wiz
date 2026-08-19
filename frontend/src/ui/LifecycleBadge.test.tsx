import { render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { LIFECYCLE_STATES, LifecycleBadge, type LifecycleState } from './LifecycleBadge';

describe('LifecycleBadge', () => {
  it('represents exactly the true governance/gate states (no invented states)', () => {
    // Sourced from ontowiz_spec.Lifecycle + ontowiz_core.DeltaStatus + gate outcomes.
    expect([...LIFECYCLE_STATES]).toEqual([
      'draft', 'review', 'verified', 'active', 'deprecated', 'archived',
      'proposed', 'approved', 'rejected', 'merged',
      'pass', 'fail', 'warn',
    ]);
  });

  it.each([...LIFECYCLE_STATES])(
    'renders %s with a visible label AND a decorative icon (never colour-only)',
    (state) => {
      render(<LifecycleBadge state={state} />);
      const badge = screen.getByTestId(`lifecycle-badge-${state}`);
      expect(badge.textContent?.trim().length ?? 0).toBeGreaterThan(0);
      const icon = badge.querySelector('svg');
      expect(icon).not.toBeNull();
      // decorative → accessible name is the text label, and state is distinguishable
      // without relying on colour (WCAG 2.2 AA, §13 DoD)
      expect(icon).toHaveAttribute('aria-hidden', 'true');
    },
  );

  it('gives every state a distinct default label (no colour-only collisions)', () => {
    const labels = [...LIFECYCLE_STATES].map((s) => {
      const view = render(<LifecycleBadge state={s} />);
      const text = view.getByTestId(`lifecycle-badge-${s}`).textContent?.trim();
      view.unmount();
      return text;
    });
    expect(new Set(labels).size).toBe(LIFECYCLE_STATES.length);
  });

  it('lets a caller override the label while keeping the state tone/icon', () => {
    render(<LifecycleBadge state="proposed" label="CANDIDATE" />);
    const badge = screen.getByTestId('lifecycle-badge-proposed');
    expect(within(badge).getByText('CANDIDATE')).toBeInTheDocument();
    expect(badge).toHaveAttribute('data-state', 'proposed');
    expect(badge.querySelector('svg')).not.toBeNull();
  });

  it('falls back gracefully for an unmapped state (defensive, per §9)', () => {
    render(<LifecycleBadge state={'bogus' as LifecycleState} />);
    const badge = screen.getByTestId('lifecycle-badge-bogus');
    expect(badge).toHaveTextContent('bogus');
    expect(badge.querySelector('svg')).not.toBeNull();
  });
});
