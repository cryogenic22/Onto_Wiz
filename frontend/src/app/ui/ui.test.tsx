import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { FOUNDRY_COLORS } from '@/ui/tokens';
import { LIFECYCLE_STATES } from '@/ui/LifecycleBadge';
import UIGalleryPage from './page';

describe('/ui gallery', () => {
  it('renders the design-tokens section with a swatch per colour token', () => {
    render(<UIGalleryPage />);
    expect(
      screen.getByRole('heading', { name: /design tokens/i }),
    ).toBeInTheDocument();
    for (const name of Object.keys(FOUNDRY_COLORS)) {
      expect(screen.getByTestId(`swatch-${name}`)).toBeInTheDocument();
    }
  });

  it('renders a Lifecycle & Gate section with a badge for every state', () => {
    render(<UIGalleryPage />);
    expect(
      screen.getByRole('heading', { name: /lifecycle & gate/i }),
    ).toBeInTheDocument();
    for (const state of LIFECYCLE_STATES) {
      expect(screen.getByTestId(`lifecycle-badge-${state}`)).toBeInTheDocument();
    }
  });
});
