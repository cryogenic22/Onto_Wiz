/** SME Impact Dashboard types — mirrors backend Contribution schemas. */

export interface Contribution {
  id: string;
  reasoning_event_id: string;
  sme_id: string;
  sme_persona: string;
  delta_ids: string[];
  contributed_at: string;
  therapeutic_area: string;
  scenario_type: string;
  sme_confidence: number;
}

export interface ContributorSummary {
  sme_id: string;
  total_contributions: number;
  total_deltas: number;
  domains: Record<string, number>;
  avg_confidence: number;
  last_contributed: string | null;
}

export interface ContributionStats {
  total_contributions: number;
  unique_smes: number;
  total_deltas: number;
}
