import { NextResponse } from 'next/server';

import { MockApiError, performAction } from '@/features/control-plane/mock-server';
import { envelope, errorEnvelope } from '@/features/control-plane/server-envelope';
import type { ControlAction } from '@/features/control-plane/types';

const actions: ControlAction[] = [
  'apply_eval_correction',
  'approve_risk_bundle',
  'compile_demo_release',
  'create_improvement_delta',
];

export async function POST(request: Request) {
  const body: unknown = await request.json().catch(() => null);
  const action = body && typeof body === 'object' ? (body as { action?: unknown }).action : null;
  if (typeof action !== 'string' || !actions.includes(action as ControlAction)) {
    return NextResponse.json(
      errorEnvelope('INVALID_ACTION', 'A supported simulated action is required.', 'control_action', 2),
      { status: 422 },
    );
  }

  try {
    return NextResponse.json(envelope(performAction(action as ControlAction), 'control_action', 180));
  } catch (error) {
    if (error instanceof MockApiError) {
      return NextResponse.json(
        errorEnvelope(error.code, error.message, 'control_action', 3),
        { status: error.status },
      );
    }
    throw error;
  }
}
