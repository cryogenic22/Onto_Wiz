import { NextResponse } from 'next/server';

import { MockApiError, runSimulation } from '@/features/control-plane/mock-server';
import { envelope, errorEnvelope } from '@/features/control-plane/server-envelope';
import type { SimulationRequest } from '@/features/control-plane/types';

const isSimulationRequest = (value: unknown): value is SimulationRequest => {
  if (!value || typeof value !== 'object') return false;
  const candidate = value as Partial<SimulationRequest>;
  return typeof candidate.scenarioId === 'string'
    && (candidate.mode === 'candidate' || candidate.mode === 'without_context')
    && typeof candidate.candidateQualified === 'boolean';
};

export async function POST(request: Request) {
  const body: unknown = await request.json().catch(() => null);
  if (!isSimulationRequest(body)) {
    return NextResponse.json(
      errorEnvelope('INVALID_REQUEST', 'A valid scenario, mode and qualification state are required.', 'simulation', 2),
      { status: 422 },
    );
  }

  try {
    return NextResponse.json(envelope(runSimulation(body), 'simulation', 650));
  } catch (error) {
    if (error instanceof MockApiError) {
      return NextResponse.json(
        errorEnvelope(error.code, error.message, 'simulation', 3),
        { status: error.status },
      );
    }
    throw error;
  }
}
