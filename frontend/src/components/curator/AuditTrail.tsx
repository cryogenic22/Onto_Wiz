'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, Download, Loader2 } from 'lucide-react';
import type { AuditEntry } from '@/types/curator';

interface Props {
  entries: AuditEntry[];
  loading: boolean;
  onExport: () => void;
  exporting: boolean;
}

function formatTimestamp(ts: string): string {
  const d = new Date(ts);
  return d.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function AuditRow({ entry }: { entry: AuditEntry }) {
  return (
    <tr className="border-b border-slate-800/50">
      <td className="py-2 pr-3 text-xs text-slate-500 whitespace-nowrap">{formatTimestamp(entry.timestamp)}</td>
      <td className="py-2 pr-3 text-xs text-slate-400">{entry.actor}</td>
      <td className="py-2 pr-3 text-xs text-slate-300 font-medium">{entry.action}</td>
      <td className="py-2 text-xs font-mono text-slate-500">{entry.artifact_id.slice(0, 8)}</td>
    </tr>
  );
}

export default function AuditTrail({ entries, loading, onExport, exporting }: Props) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-lg border border-slate-700/50 bg-slate-800/30">
      <button
        onClick={() => setExpanded((p) => !p)}
        className="w-full flex items-center justify-between px-4 py-2.5 text-sm font-medium text-slate-300 hover:bg-slate-800/50 transition-colors"
      >
        <span>Audit Trail ({entries.length})</span>
        {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>

      {expanded && (
        <div className="px-4 pb-3">
          <div className="flex justify-end mb-2">
            <button
              onClick={onExport}
              disabled={exporting}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-xs text-slate-300 transition-colors"
            >
              {exporting ? <Loader2 className="w-3 h-3 animate-spin" /> : <Download className="w-3 h-3" />}
              Export All
            </button>
          </div>

          {loading ? (
            <div className="flex justify-center py-4">
              <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
            </div>
          ) : entries.length === 0 ? (
            <p className="text-xs text-slate-500 text-center py-4">No audit entries yet</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="py-1.5 pr-3 text-left text-xs font-medium text-slate-500">Time</th>
                    <th className="py-1.5 pr-3 text-left text-xs font-medium text-slate-500">Actor</th>
                    <th className="py-1.5 pr-3 text-left text-xs font-medium text-slate-500">Action</th>
                    <th className="py-1.5 text-left text-xs font-medium text-slate-500">Artifact</th>
                  </tr>
                </thead>
                <tbody>
                  {entries.map((entry) => (
                    <AuditRow key={entry.id} entry={entry} />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
