'use client';

import { Users, FileText, GitBranch } from 'lucide-react';
import type { ContributionStats as Stats } from '@/types/sme';

interface Props {
  stats: Stats | null;
  loading: boolean;
}

function StatCard({
  label,
  count,
  icon: Icon,
  color,
}: {
  label: string;
  count: number;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
}) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-800/50 border border-slate-700/50">
      <Icon className={`w-5 h-5 ${color}`} />
      <div>
        <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
        <p className={`text-xl font-bold ${color}`}>{count}</p>
      </div>
    </div>
  );
}

export default function ContributionStats({ stats, loading }: Props) {
  if (loading || !stats) {
    return (
      <div className="grid grid-cols-3 gap-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-16 rounded-lg bg-slate-800/30 animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-3 gap-3">
      <StatCard label="Total Contributions" count={stats.total_contributions} icon={FileText} color="text-blue-400" />
      <StatCard label="Unique SMEs" count={stats.unique_smes} icon={Users} color="text-emerald-400" />
      <StatCard label="Total Deltas" count={stats.total_deltas} icon={GitBranch} color="text-amber-400" />
    </div>
  );
}
