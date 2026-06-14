'use client';

import { AlertTriangle, Building2, FlaskConical, Pill, Tag } from 'lucide-react';
import type { Scenario } from '@/types/api';

interface Props {
  scenario: Scenario;
  onNext: () => void;
}

const COMPLEXITY_BADGE: Record<string, { bg: string; text: string }> = {
  low: { bg: 'bg-emerald-500/20 border-emerald-500/30', text: 'text-emerald-400' },
  medium: { bg: 'bg-amber-500/20 border-amber-500/30', text: 'text-amber-400' },
  high: { bg: 'bg-red-500/20 border-red-500/30', text: 'text-red-400' },
};

function DetailRow({ label, value }: { label: string; value?: string | null }) {
  if (!value) return null;
  return (
    <div>
      <span className="text-slate-500">{label}: </span>
      <span className="text-slate-200">{value}</span>
    </div>
  );
}

export default function ScenarioCard({ scenario, onNext }: Props) {
  const badge = COMPLEXITY_BADGE[scenario.complexity_level] ?? COMPLEXITY_BADGE.medium;
  const brand = scenario.brand_context;
  const account = scenario.account_context;

  return (
    <div className="flex flex-col items-center h-full overflow-y-auto px-4 py-8">
      <div className="max-w-2xl w-full space-y-6">

        {/* Header: ID + complexity badge */}
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono text-slate-500">{scenario.id}</span>
          <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${badge.bg} ${badge.text}`}>
            {scenario.complexity_level} complexity
          </span>
        </div>

        {/* Title */}
        <h2 className="text-2xl font-semibold text-slate-100 leading-tight">
          {scenario.name}
        </h2>

        {/* Tag pills */}
        <div className="flex flex-wrap gap-2">
          <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-blue-500/15 text-blue-400 border border-blue-500/20">
            <Tag className="w-3 h-3" />
            {scenario.therapeutic_area}
          </span>
          <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-purple-500/15 text-purple-400 border border-purple-500/20">
            <FlaskConical className="w-3 h-3" />
            {scenario.indication}
          </span>
          {scenario.molecular_context && (
            <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-cyan-500/15 text-cyan-400 border border-cyan-500/20">
              {scenario.molecular_context}
            </span>
          )}
          {scenario.line_of_therapy && (
            <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-slate-500/15 text-slate-300 border border-slate-500/20">
              {scenario.line_of_therapy}
            </span>
          )}
        </div>

        {/* Full description */}
        <p className="text-base text-slate-300 leading-relaxed">
          {scenario.description}
        </p>

        {/* 2-column context grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Brand Context */}
          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4 space-y-2">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-400 uppercase tracking-wide">
              <Pill className="w-3.5 h-3.5" />
              Brand Context
            </div>
            <div className="space-y-1 text-sm">
              <DetailRow label="Brand" value={brand?.brand} />
              <DetailRow label="Lifecycle" value={brand?.lifecycle} />
              <DetailRow label="Channel" value={brand?.channel} />
              <DetailRow label="Companion Dx" value={brand?.companion_diagnostic} />
              {brand?.biomarkers_required && brand.biomarkers_required.length > 0 && (
                <div>
                  <span className="text-slate-500">Biomarkers: </span>
                  <span className="text-slate-200">{brand.biomarkers_required.join(', ')}</span>
                </div>
              )}
            </div>
          </div>

          {/* Account Context */}
          <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-4 space-y-2">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-400 uppercase tracking-wide">
              <Building2 className="w-3.5 h-3.5" />
              Account Context
            </div>
            <div className="space-y-1 text-sm">
              <DetailRow label="Type" value={account?.type} />
              <DetailRow label="Testing" value={account?.biomarker_testing} />
              <DetailRow label="Potential" value={account?.potential} />
              <DetailRow label="Access" value={account?.access_status} />
              <DetailRow label="Payer mix" value={account?.payer_mix} />
              <DetailRow label="Tumor board" value={account?.tumor_board_influence} />
            </div>
          </div>
        </div>

        {/* Trigger Signal — highlighted block */}
        <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-4">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-400 uppercase tracking-wide mb-2">
            <AlertTriangle className="w-3.5 h-3.5" />
            Trigger Signal
          </div>
          <p className="text-sm text-amber-200/90 leading-relaxed">
            {scenario.trigger_signal}
          </p>
        </div>

        {/* CTA */}
        <p className="text-sm text-slate-500 pt-1">
          Read the scenario briefing above carefully. When you&rsquo;re ready, share your
          first instinct about what&rsquo;s happening.
        </p>

        <button
          onClick={onNext}
          className="w-full py-3 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold text-base transition-colors"
        >
          I&rsquo;ve read it &mdash; let&rsquo;s go
        </button>
      </div>
    </div>
  );
}
