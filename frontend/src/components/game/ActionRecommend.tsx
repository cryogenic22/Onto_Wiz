'use client';

import { useState } from 'react';
import { Plus, X } from 'lucide-react';
import type { ActionResponse } from '@/types/game';

interface Props {
  onNext: (data: ActionResponse[]) => void;
}

const ACTION_TYPES = [
  { value: 'investigate', label: 'Investigate' },
  { value: 'escalate', label: 'Escalate' },
  { value: 'wait', label: 'Wait & Watch' },
  { value: 'intervene', label: 'Intervene Now' },
] as const;

const OWNER_OPTIONS = ['Field team', 'Access team', 'Analytics', 'Medical', 'Leadership'];

export default function ActionRecommend({ onNext }: Props) {
  const [actions, setActions] = useState<ActionResponse[]>([]);
  const [draft, setDraft] = useState({
    action: '',
    actionType: 'investigate' as ActionResponse['actionType'],
    ownerFunction: '',
  });

  const addAction = () => {
    if (!draft.action.trim()) return;
    setActions((prev) => [
      ...prev,
      { ...draft, priority: prev.length + 1 },
    ]);
    setDraft({ action: '', actionType: 'investigate', ownerFunction: '' });
  };

  const removeAction = (idx: number) => {
    setActions((prev) =>
      prev
        .filter((_, i) => i !== idx)
        .map((a, i) => ({ ...a, priority: i + 1 })),
    );
  };

  return (
    <div className="flex flex-col items-center justify-center h-full px-4">
      <div className="max-w-lg w-full space-y-6">
        <h2 className="text-2xl font-semibold text-slate-100">
          What would you do next?
        </h2>
        <p className="text-slate-400">
          If this landed on your desk, what actions would you recommend?
        </p>

        {/* Existing actions */}
        {actions.map((a, i) => (
          <div
            key={i}
            className="p-3 rounded-lg bg-slate-800 border border-slate-700 flex items-center gap-3"
          >
            <span className="text-blue-400 font-mono text-sm w-6">#{a.priority}</span>
            <div className="flex-1">
              <p className="text-sm text-slate-200 font-medium">{a.action}</p>
              <p className="text-xs text-slate-500">
                {a.actionType}{a.ownerFunction ? ` \u2022 ${a.ownerFunction}` : ''}
              </p>
            </div>
            <button
              onClick={() => removeAction(i)}
              className="text-slate-500 hover:text-red-400"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ))}

        {/* Add form */}
        <div className="space-y-3 p-4 rounded-lg bg-slate-800/50 border border-slate-700/50">
          <input
            type="text"
            value={draft.action}
            onChange={(e) => setDraft({ ...draft, action: e.target.value })}
            placeholder='e.g., "Pull PA reject data for last 90 days"'
            className="w-full px-4 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none text-sm"
          />

          <div className="flex gap-2">
            {/* Action type */}
            <select
              value={draft.actionType}
              onChange={(e) =>
                setDraft({ ...draft, actionType: e.target.value as ActionResponse['actionType'] })
              }
              className="flex-1 px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-300 text-sm"
            >
              {ACTION_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>

            {/* Owner */}
            <select
              value={draft.ownerFunction}
              onChange={(e) => setDraft({ ...draft, ownerFunction: e.target.value })}
              className="flex-1 px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-300 text-sm"
            >
              <option value="">Who owns this?</option>
              {OWNER_OPTIONS.map((o) => (
                <option key={o} value={o}>
                  {o}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={addAction}
            disabled={!draft.action.trim()}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 disabled:opacity-40 text-slate-200 text-sm transition-colors"
          >
            <Plus className="w-4 h-4" /> Add action
          </button>
        </div>

        <button
          onClick={() => onNext(actions)}
          className="w-full py-3 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold transition-colors"
        >
          {actions.length === 0 ? 'Skip' : 'Next'}
        </button>
      </div>
    </div>
  );
}
