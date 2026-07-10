import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { FOUNDRY_COLORS } from '@/ui/tokens';
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
});
