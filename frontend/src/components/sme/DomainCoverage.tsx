'use client';

import { Globe } from 'lucide-react';
import type { ContributorSummary } from '@/types/sme';

interface Props {
  summary: ContributorSummary | null;
  loading: boolean;
}

export default function DomainCoverage({ summary, loading }: Props) {
  if (loading) {
    return (
      <div className="rounded-lg bg-slate-900/50 border border-slate-800/50 p-4">
        <h3 className="text-sm font-semibold text-slate-400 mb-3 flex items-center gap-2">
          <Globe className="w-4 h-4" /> Domain Coverage
        </h3>
        <div className="h-24 rounded bg-slate-800/30 animate-pulse" />
      </div>
    );
  }

  if (!summary || Object.keys(summary.domains).length === 0) {
    return (
      <div className="rounded-lg bg-slate-900/50 border border-slate-800/50 p-4">
        <h3 className="text-sm font-semibold text-slate-400 mb-3 flex items-center gap-2">
          <Globe className="w-4 h-4" /> Domain Coverage
        </h3>
        <p className="text-xs text-slate-500 text-center py-4">Select a contributor to view domain breakdown</p>
      </div>
    );
  }

  const total = Object.values(summary.domains).reduce((a, b) => a + b, 0);
  const sorted = Object.entries(summary.domains).sort(([, a], [, b]) => b - a);

  return (
    <div className="rounded-lg bg-slate-900/50 border border-slate-800/50 p-4">
      <h3 className="text-sm font-semibold text-slate-400 mb-3 flex items-center gap-2">
        <Globe className="w-4 h-4" /> Domain Coverage — {summary.sme_id}
      </h3>
      <div className="space-y-2">
        {sorted.map(([domain, count]) => {
          const pct = total > 0 ? (count / total) * 100 : 0;
          return (
            <div key={domain}>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-300">{domain || 'unknown'}</span>
                <span className="text-slate-500">{count} ({pct.toFixed(0)}%)</span>
              </div>
              <div className="h-1.5 rounded-full bg-slate-800">
                <div className="h-full rounded-full bg-blue-500" style={{ width: `${pct}%` }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
