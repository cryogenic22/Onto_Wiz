'use client';

import { Trophy } from 'lucide-react';
import type { ContributorSummary } from '@/types/sme';

interface Props {
  contributors: ContributorSummary[];
  loading: boolean;
  onSelect: (smeId: string) => void;
  selectedSmeId: string | null;
}

const RANK_COLORS = ['text-amber-400', 'text-slate-300', 'text-orange-400'];

export default function Leaderboard({ contributors, loading, onSelect, selectedSmeId }: Props) {
  if (loading) {
    return (
      <div className="rounded-lg bg-slate-900/50 border border-slate-800/50 p-4">
        <h3 className="text-sm font-semibold text-slate-400 mb-3 flex items-center gap-2">
          <Trophy className="w-4 h-4" /> Top Contributors
        </h3>
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-10 mb-2 rounded bg-slate-800/30 animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="rounded-lg bg-slate-900/50 border border-slate-800/50 p-4">
      <h3 className="text-sm font-semibold text-slate-400 mb-3 flex items-center gap-2">
        <Trophy className="w-4 h-4" /> Top Contributors
      </h3>
      {contributors.length === 0 ? (
        <p className="text-xs text-slate-500 text-center py-4">No contributions yet</p>
      ) : (
        <div className="space-y-1">
          {contributors.map((c, i) => (
            <button
              key={c.sme_id}
              onClick={() => onSelect(c.sme_id)}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left text-sm transition-colors ${
                selectedSmeId === c.sme_id ? 'bg-blue-600/20 border border-blue-600/40' : 'hover:bg-slate-800/50'
              }`}
            >
              <span className={`w-5 text-xs font-bold ${RANK_COLORS[i] ?? 'text-slate-500'}`}>#{i + 1}</span>
              <span className="flex-1 truncate text-slate-200">{c.sme_id}</span>
              <span className="text-xs text-slate-400">{c.total_deltas} deltas</span>
              <span className="text-xs text-slate-500">{(c.avg_confidence * 100).toFixed(0)}%</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
