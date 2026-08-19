export interface ApiMeta {
  requestId: string;
  traceId: string;
  serverTime: string;
  durationMs: number;
  simulation: true;
  datasetVersion: 'auravia-control-plane-v1';
  syntheticReference: true;
  productionEligible: false;
}

export interface ApiEnvelope<T> {
  data: T;
  meta: ApiMeta;
  warnings: Array<{ code: string; message: string }>;
}

export interface ApiErrorEnvelope {
  error: {
    code: string;
    message: string;
    retryable: boolean;
  };
  meta: ApiMeta;
}
