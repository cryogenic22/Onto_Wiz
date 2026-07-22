import { render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import PacksPage from './page';

/** The /packs route renders the explorer; data-path behaviour is covered by
 *  `features/packs/PackExplorer.test.tsx`. This guards the route wiring itself. */

beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve([]),
    } as unknown as Response),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('/packs route', () => {
  it('renders the Pack Explorer heading', () => {
    render(<PacksPage />);
    expect(
      screen.getByRole('heading', { name: /pack explorer/i }),
    ).toBeInTheDocument();
  });

  it('starts in the loading state before the registry responds', () => {
    render(<PacksPage />);
    expect(screen.getByTestId('packs-loading')).toBeInTheDocument();
  });

  it('reaches the empty state when the registry serves no packs', async () => {
    render(<PacksPage />);
    expect(await screen.findByTestId('packs-empty')).toBeInTheDocument();
  });
});
