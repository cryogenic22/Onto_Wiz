/** API response types matching backend schemas. */

export interface BrandContext {
  brand: string;
  lifecycle: string;
  channel?: string | null;
  biomarkers_required?: string[] | null;
  companion_diagnostic?: string | null;
}

export interface AccountContext {
  type: string;
  biomarker_testing?: string | null;
  potential?: string | null;
  access_status?: string | null;
  payer_mix?: string | null;
  tumor_board_influence?: string | null;
}

export interface Scenario {
  id: string;
  name: string;
  description: string;
  therapeutic_area: string;
  indication: string;
  molecular_context?: string | null;
  line_of_therapy?: string | null;
  brand_context: BrandContext;
  account_context: AccountContext;
  trigger_signal: string;
  complexity_level: string;
  expected_hypothesis: string;
}

export interface SessionResult {
  session_id: string;
  deltas_generated: number;
  delta_ids: string[];
  reasoning_event_id: string;
}

export interface SessionDetail {
  id: string;
  scenario_id: string;
  started_at: string;
  deltas_generated: number;
  delta_ids: string[];
  hypothesis_category: string | null;
  sme_confidence: number;
  processed: boolean;
}
