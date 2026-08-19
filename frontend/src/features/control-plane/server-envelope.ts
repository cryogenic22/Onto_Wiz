import type { ApiEnvelope, ApiErrorEnvelope, ApiMeta } from './api-contract';

const meta = (operation: string, durationMs: number): ApiMeta => ({
  requestId: `req_${operation}_001`,
  traceId: `trace_${operation}_001`,
  serverTime: '2026-06-25T10:00:00Z',
  durationMs,
  simulation: true,
  datasetVersion: 'auravia-control-plane-v1',
  syntheticReference: true,
  productionEligible: false,
});

export const envelope = <T>(
  data: T,
  operation: string,
  durationMs: number,
): ApiEnvelope<T> => ({
  data,
  meta: meta(operation, durationMs),
  warnings: [{ code: 'SYNTHETIC_REFERENCE', message: 'Reference data only; never eligible for production use.' }],
});

export const errorEnvelope = (
  code: string,
  message: string,
  operation: string,
  durationMs: number,
): ApiErrorEnvelope => ({
  error: { code, message, retryable: false },
  meta: meta(operation, durationMs),
});
