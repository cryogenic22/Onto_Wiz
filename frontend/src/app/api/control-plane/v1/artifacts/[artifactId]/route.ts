import { NextResponse } from 'next/server';

import { getArtifact, MockApiError } from '@/features/control-plane/mock-server';
import { envelope, errorEnvelope } from '@/features/control-plane/server-envelope';

interface ArtifactRouteContext {
  params: Promise<{ artifactId: string }>;
}

export async function GET(_request: Request, context: ArtifactRouteContext) {
  const { artifactId } = await context.params;
  try {
    return NextResponse.json(envelope(getArtifact(artifactId), 'artifact_detail', 110));
  } catch (error) {
    if (error instanceof MockApiError) {
      return NextResponse.json(
        errorEnvelope(error.code, error.message, 'artifact_detail', 4),
        { status: error.status },
      );
    }
    throw error;
  }
}
