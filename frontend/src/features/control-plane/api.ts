import type { ApiEnvelope, ApiErrorEnvelope } from './api-contract';
import type {
  ActionReceipt,
  ArtifactDetail,
  ControlAction,
  ControlPlaneSnapshot,
  SimulationRequest,
  SimulationResult,
} from './types';

export class ControlPlaneApiError extends Error {
  constructor(
    message: string,
    readonly code: string,
    readonly status: number,
  ) {
    super(message);
    this.name = 'ControlPlaneApiError';
  }
}

const request = async <T>(path: string, init?: RequestInit): Promise<ApiEnvelope<T>> => {
  const response = await fetch(path, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  });
  const body: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    const error = body as ApiErrorEnvelope | null;
    throw new ControlPlaneApiError(
      error?.error.message ?? 'The control-plane simulator returned an invalid response.',
      error?.error.code ?? 'SIMULATOR_ERROR',
      response.status,
    );
  }

  return body as ApiEnvelope<T>;
};

export interface ControlPlaneClient {
  getSnapshot(): Promise<ApiEnvelope<ControlPlaneSnapshot>>;
  getArtifact(artifactId: string): Promise<ApiEnvelope<ArtifactDetail>>;
  runSimulation(input: SimulationRequest): Promise<ApiEnvelope<SimulationResult>>;
  performAction(action: ControlAction): Promise<ApiEnvelope<ActionReceipt>>;
}

export const httpControlPlaneClient: ControlPlaneClient = {
  getSnapshot: () => request<ControlPlaneSnapshot>('/api/control-plane/v1/snapshot'),
  getArtifact: (artifactId) => request<ArtifactDetail>(`/api/control-plane/v1/artifacts/${encodeURIComponent(artifactId)}`),
  runSimulation: (input) => request<SimulationResult>('/api/control-plane/_sim/v1/simulations', {
    method: 'POST',
    body: JSON.stringify(input),
  }),
  performAction: (action) => request<ActionReceipt>('/api/control-plane/_sim/v1/actions', {
    method: 'POST',
    body: JSON.stringify({ action }),
  }),
};
