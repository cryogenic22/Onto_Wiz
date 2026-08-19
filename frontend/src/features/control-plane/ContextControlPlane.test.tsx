import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import ContextControlPlane from './ContextControlPlane';
import { getArtifact, getSnapshot, performAction, runSimulation } from './mock-server';
import type { ControlAction, SimulationRequest } from './types';

const response = (data: unknown, status = 200) => ({
  ok: status >= 200 && status < 300,
  status,
  json: async () => ({ data, warnings: [], meta: {} }),
}) as Response;

describe('ContextControlPlane', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const path = String(input);
      if (path.endsWith('/v1/snapshot')) return response(getSnapshot());
      if (path.includes('/v1/artifacts/')) return response(getArtifact(decodeURIComponent(path.split('/').at(-1) ?? '')));
      if (path.endsWith('/v1/simulations')) return response(runSimulation(JSON.parse(String(init?.body)) as SimulationRequest));
      if (path.endsWith('/v1/actions')) return response(performAction((JSON.parse(String(init?.body)) as { action: ControlAction }).action));
      return response(null, 404);
    }));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('loads the candidate command center from the simulated API', async () => {
    render(<ContextControlPlane />);

    expect(await screen.findByRole('heading', { name: 'Is this context safe to serve?' })).toBeInTheDocument();
    expect(screen.getByText('27 / 28')).toBeInTheDocument();
    expect(screen.getByText('Candidate cannot enter the demo release channel')).toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith('/api/control-plane/v1/snapshot', expect.any(Object));
  });

  it('closes the critical regression and qualifies a demo release', async () => {
    const user = userEvent.setup();
    render(<ContextControlPlane />);
    await screen.findByRole('heading', { name: 'Is this context safe to serve?' });

    await user.click(screen.getByRole('button', { name: 'Evaluations' }));
    await user.click(screen.getByRole('button', { name: /Apply Delta & rerun affected cases/i }));
    expect(await screen.findByText('Regression is closed')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Reference gate passed' })).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Release center' }));
    await user.click(screen.getByRole('button', { name: /Record synthetic scoped MLR decision/i }));
    expect(await screen.findByText('Scoped review decision recorded')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /Publish to demo/i }));
    await waitFor(() => expect(screen.getByText('Demo released')).toBeInTheDocument());
    expect(screen.getByRole('button', { name: /Production disabled/i })).toBeDisabled();
  });

  it('compares governed and ungoverned agent results', async () => {
    const user = userEvent.setup();
    render(<ContextControlPlane />);
    await screen.findByRole('heading', { name: 'Is this context safe to serve?' });

    await user.click(screen.getByRole('button', { name: 'Agent simulator' }));
    await user.click(screen.getByRole('button', { name: /Run simulation/i }));

    expect(await screen.findByText('Typed context contract')).toBeInTheDocument();
    expect(screen.getByText('Ungoverned retrieval')).toBeInTheDocument();
    expect(screen.getByText('ABSTAIN')).toBeInTheDocument();
    expect(screen.getByText('ALLOW DRAFT')).toBeInTheDocument();
    expect(screen.getByText(/critical semantic-invariant evaluation/i)).toBeInTheDocument();
  });
});
