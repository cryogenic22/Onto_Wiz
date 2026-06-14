'use client';

import { Clock } from 'lucide-react';
import type { Contribution } from '@/types/sme';

interface Props {
  contributions: Contribution[];
  loading: boolean;
}

function formatTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export default function ContributionHistory({ contributions, loading }: Props) {
  if (loading) {
    return (
      <div className="rounded-lg bg-slate-900/50 border border-slate-800/50 p-4">
        <h3 className="text-sm font-semibold text-slate-400 mb-3 flex items-center gap-2">
          <Clock className="w-4 h-4" /> Recent Contributions
        </h3>
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-12 mb-2 rounded bg-slate-800/30 animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="rounded-lg bg-slate-900/50 border border-slate-800/50 p-4">
      <h3 className="text-sm font-semibold text-slate-400 mb-3 flex items-center gap-2">
        <Clock className="w-4 h-4" /> Recent Contributions
      </h3>
      {contributions.length === 0 ? (
        <p className="text-xs text-slate-500 text-center py-4">Select a contributor to view history</p>
      ) : (
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {contributions.map((c) => (
            <div key={c.id} className="flex items-start gap-3 px-3 py-2 rounded-lg bg-slate-800/30">
              <div className="flex-1 min-w-0">
                <p className="text-xs text-slate-200 truncate">{c.scenario_type || 'game_session'}</p>
                <p className="text-xs text-slate-500">{c.therapeutic_area || 'general'} &middot; {c.delta_ids.length} delta{c.delta_ids.length !== 1 ? 's' : ''}</p>
              </div>
              <div className="text-right shrink-0">
                <p className="text-xs text-slate-400">{(c.sme_confidence * 100).toFixed(0)}%</p>
                <p className="text-xs text-slate-600">{formatTime(c.contributed_at)}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
