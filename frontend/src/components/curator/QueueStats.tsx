'use client';

import { Zap, Users, ShieldAlert } from 'lucide-react';
import type { QueueStatsResponse } from '@/types/curator';

interface Props {
  stats: QueueStatsResponse | null;
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

export default function QueueStats({ stats, loading }: Props) {
  if (loading || !stats) {
    return (
      <div className="grid grid-cols-4 gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-16 rounded-lg bg-slate-800/30 animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-4 gap-3">
      <StatCard label="Auto" count={stats.auto} icon={Zap} color="text-emerald-400" />
      <StatCard label="Standard" count={stats.standard} icon={Users} color="text-blue-400" />
      <StatCard label="Escalated" count={stats.escalated} icon={ShieldAlert} color="text-amber-400" />
      <StatCard label="Total Pending" count={stats.total_pending} icon={Users} color="text-slate-300" />
    </div>
  );
}
