import { NextResponse } from 'next/server';

import { getSnapshot } from '@/features/control-plane/mock-server';
import { envelope } from '@/features/control-plane/server-envelope';

export async function GET() {
  return NextResponse.json(envelope(getSnapshot(), 'snapshot', 72));
}
