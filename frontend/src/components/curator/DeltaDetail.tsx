'use client';

import { useState } from 'react';
import { CheckCircle, XCircle, ArrowUpCircle, AlertTriangle, Loader2 } from 'lucide-react';
import type { ReviewQueueItem } from '@/types/curator';

interface Props {
  item: ReviewQueueItem | null;
  onApprove: (deltaId: string, reviewer: string) => Promise<void>;
  onReject: (deltaId: string, reviewer: string, reason: string) => Promise<void>;
  onEscalate: (deltaId: string, reason: string) => Promise<void>;
  actionLoading: boolean;
}

function ContentRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-2 text-sm">
      <span className="text-slate-500 min-w-[100px]">{label}:</span>
      <span className="text-slate-300">{value}</span>
    </div>
  );
}

function ContentBlock({ content }: { content: Record<string, unknown> }) {
  const entries = Object.entries(content);
  if (entries.length === 0) return <p className="text-sm text-slate-500 italic">No content</p>;

  return (
    <div className="space-y-1.5">
      {entries.map(([key, val]) => (
        <ContentRow key={key} label={key} value={String(val)} />
      ))}
    </div>
  );
}

function ActionButtons({ item, onApprove, onReject, onEscalate, actionLoading }: Props & { item: ReviewQueueItem }) {
  const [rejectReason, setRejectReason] = useState('');
  const [escalateReason, setEscalateReason] = useState('');
  const [mode, setMode] = useState<'actions' | 'reject' | 'escalate'>('actions');

  if (mode === 'reject') {
    return (
      <div className="space-y-2">
        <textarea
          value={rejectReason}
          onChange={(e) => setRejectReason(e.target.value)}
          placeholder="Reason for rejection..."
          className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm text-slate-200 placeholder-slate-500 focus:border-red-500 focus:outline-none resize-none"
          rows={2}
        />
        <div className="flex gap-2">
          <button
            onClick={() => { onReject(item.delta.id, 'curator', rejectReason); setMode('actions'); }}
            disabled={!rejectReason.trim() || actionLoading}
            className="flex-1 py-2 rounded-lg bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-sm font-medium transition-colors"
          >
            {actionLoading ? 'Rejecting...' : 'Confirm Reject'}
          </button>
          <button onClick={() => setMode('actions')} className="px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-sm text-slate-300 transition-colors">
            Cancel
          </button>
        </div>
      </div>
    );
  }

  if (mode === 'escalate') {
    return (
      <div className="space-y-2">
        <textarea
          value={escalateReason}
          onChange={(e) => setEscalateReason(e.target.value)}
          placeholder="Reason for escalation..."
          className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-sm text-slate-200 placeholder-slate-500 focus:border-amber-500 focus:outline-none resize-none"
          rows={2}
        />
        <div className="flex gap-2">
          <button
            onClick={() => { onEscalate(item.delta.id, escalateReason); setMode('actions'); }}
            disabled={!escalateReason.trim() || actionLoading}
            className="flex-1 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white text-sm font-medium transition-colors"
          >
            {actionLoading ? 'Escalating...' : 'Confirm Escalate'}
          </button>
          <button onClick={() => setMode('actions')} className="px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 text-sm text-slate-300 transition-colors">
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-2">
      <button
        onClick={() => onApprove(item.delta.id, 'curator')}
        disabled={actionLoading}
        className="flex-1 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-sm font-medium transition-colors flex items-center justify-center gap-1.5"
      >
        {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
        Approve
      </button>
      <button
        onClick={() => setMode('reject')}
        disabled={actionLoading}
        className="flex-1 py-2 rounded-lg bg-red-600/20 hover:bg-red-600/30 border border-red-600/40 text-red-400 text-sm font-medium transition-colors flex items-center justify-center gap-1.5"
      >
        <XCircle className="w-4 h-4" /> Reject
      </button>
      <button
        onClick={() => setMode('escalate')}
        disabled={actionLoading}
        className="flex-1 py-2 rounded-lg bg-amber-600/20 hover:bg-amber-600/30 border border-amber-600/40 text-amber-400 text-sm font-medium transition-colors flex items-center justify-center gap-1.5"
      >
        <ArrowUpCircle className="w-4 h-4" /> Escalate
      </button>
    </div>
  );
}

export default function DeltaDetail({ item, onApprove, onReject, onEscalate, actionLoading }: Props) {
  if (!item) {
    return (
      <div className="flex items-center justify-center h-full text-slate-500 text-sm">
        Select a delta from the queue to review
      </div>
    );
  }

  const { delta } = item;
  const typeLabel = delta.type.replace('proposed_', '').replace('_', ' ');

  return (
    <div className="flex flex-col gap-4 overflow-y-auto max-h-[calc(100vh-12rem)]">
      <div>
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-base font-semibold text-slate-200 capitalize">{typeLabel}</h3>
          <span className="text-xs font-mono text-slate-500">{delta.id.slice(0, 12)}</span>
        </div>
        <div className="text-xs text-slate-500">
          {delta.source_type} | blast: {delta.blast_radius} | conf: {Math.round(delta.confidence * 100)}%
        </div>
      </div>

      <div className="p-3 rounded-lg bg-slate-800/50 border border-slate-700/50">
        <h4 className="text-xs uppercase tracking-wide text-slate-500 mb-2">Content</h4>
        <ContentBlock content={delta.content} />
      </div>

      {delta.evidence_pointers.length > 0 && (
        <div className="p-3 rounded-lg bg-slate-800/50 border border-slate-700/50">
          <h4 className="text-xs uppercase tracking-wide text-slate-500 mb-2">Evidence</h4>
          <div className="flex flex-wrap gap-1.5">
            {delta.evidence_pointers.map((ep) => (
              <span key={ep} className="px-2 py-0.5 rounded bg-slate-700 text-xs text-slate-300">{ep}</span>
            ))}
          </div>
        </div>
      )}

      <div className="p-3 rounded-lg bg-slate-800/50 border border-slate-700/50">
        <h4 className="text-xs uppercase tracking-wide text-slate-500 mb-2">Routing</h4>
        <ContentRow label="Queue" value={item.queue} />
        <ContentRow label="Assigned" value={item.assigned_to} />
        <ContentRow label="Judgment" value={item.judgment_type} />
        <ContentRow label="SLA" value={item.sla_hours > 0 ? `${item.sla_hours}h` : 'Auto'} />
        <ContentRow label="Reason" value={item.reason} />
      </div>

      {delta.status === 'proposed' && (
        <ActionButtons item={item} onApprove={onApprove} onReject={onReject} onEscalate={onEscalate} actionLoading={actionLoading} />
      )}

      {delta.status !== 'proposed' && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-slate-800/30 border border-slate-700/30">
          <AlertTriangle className="w-4 h-4 text-slate-500" />
          <span className="text-sm text-slate-500">Status: {delta.status} {delta.reviewed_by ? `by ${delta.reviewed_by}` : ''}</span>
        </div>
      )}
    </div>
  );
}
