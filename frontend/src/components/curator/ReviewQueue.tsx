'use client';

import { Clock, Loader2 } from 'lucide-react';
import { cn } from '@/lib/cn';
import type { ReviewQueueItem } from '@/types/curator';

interface Props {
  items: ReviewQueueItem[];
  loading: boolean;
  selectedId: string | null;
  onSelect: (item: ReviewQueueItem) => void;
  roleFilter: string;
  onRoleFilterChange: (role: string) => void;
}

const PRIORITY_STYLES: Record<string, string> = {
  critical: 'bg-red-600/20 text-red-400 border-red-600/40',
  high: 'bg-amber-600/20 text-amber-400 border-amber-600/40',
  normal: 'bg-blue-600/20 text-blue-400 border-blue-600/40',
  low: 'bg-slate-600/30 text-slate-400 border-slate-600',
};

const JUDGMENT_STYLES: Record<string, string> = {
  empirical: 'text-emerald-400',
  causal_hypothesis: 'text-blue-400',
  normative: 'text-amber-400',
};

function PriorityBadge({ priority }: { priority: string }) {
  return (
    <span className={cn('px-2 py-0.5 text-xs font-medium border rounded-full', PRIORITY_STYLES[priority] ?? PRIORITY_STYLES.normal)}>
      {priority}
    </span>
  );
}

function RoleFilter({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-sm text-slate-300 focus:border-blue-500 focus:outline-none"
    >
      <option value="">All roles</option>
      <option value="system_auto">Auto</option>
      <option value="domain_expert">Domain Expert</option>
      <option value="governance_board">Governance Board</option>
    </select>
  );
}

function QueueItem({ item, selected, onSelect }: { item: ReviewQueueItem; selected: boolean; onSelect: () => void }) {
  const delta = item.delta;
  const typeLabel = delta.type.replace('proposed_', '').replace('_', ' ');
  const judgmentLabel = item.judgment_type.replace('_', ' ');

  return (
    <button
      onClick={onSelect}
      className={cn(
        'w-full text-left p-3 rounded-lg border transition-colors',
        selected
          ? 'bg-blue-600/10 border-blue-600/40'
          : 'bg-slate-800/30 border-slate-700/50 hover:bg-slate-800/60',
      )}
    >
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs font-mono text-slate-500">{delta.id.slice(0, 8)}</span>
        <PriorityBadge priority={item.priority} />
      </div>
      <p className="text-sm font-medium text-slate-200 capitalize mb-1">{typeLabel}</p>
      <div className="flex items-center gap-2 text-xs text-slate-500">
        <span className={JUDGMENT_STYLES[item.judgment_type] ?? 'text-slate-400'}>{judgmentLabel}</span>
        <span>|</span>
        <span>{item.queue}</span>
        {item.sla_hours > 0 && (
          <>
            <span>|</span>
            <Clock className="w-3 h-3" />
            <span>{item.sla_hours}h SLA</span>
          </>
        )}
      </div>
    </button>
  );
}

export default function ReviewQueue({ items, loading, selectedId, onSelect, roleFilter, onRoleFilterChange }: Props) {
  if (loading) {
    return (
      <div className="flex items-center justify-center h-48">
        <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-300">Review Queue</h3>
        <RoleFilter value={roleFilter} onChange={onRoleFilterChange} />
      </div>
      {items.length === 0 ? (
        <p className="text-sm text-slate-500 text-center py-8">No deltas pending review</p>
      ) : (
        <div className="flex flex-col gap-2 overflow-y-auto max-h-[calc(100vh-16rem)]">
          {items.map((item) => (
            <QueueItem
              key={item.delta.id}
              item={item}
              selected={selectedId === item.delta.id}
              onSelect={() => onSelect(item)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
