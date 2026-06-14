'use client';

import { useState } from 'react';
import { Plus, X } from 'lucide-react';
import type { SignalResponse } from '@/types/game';

interface Props {
  onNext: (data: SignalResponse[]) => void;
}

const ROLE_OPTIONS = ['validation', 'disconfirming', 'leading'] as const;
const ROLE_LABELS: Record<string, string> = {
  validation: 'Validates hypothesis',
  disconfirming: 'Could disprove it',
  leading: 'Leading indicator',
};

const SUGGESTED_SIGNALS = [
  'NBRx', 'TRx', 'PA rejects', 'Medical inquiries',
  'Competitor launches', 'Field visit frequency', 'Payer coverage changes',
];

export default function SignalPriority({ onNext }: Props) {
  const [signals, setSignals] = useState<SignalResponse[]>([]);
  const [custom, setCustom] = useState('');

  const addSignal = (name: string) => {
    if (signals.some((s) => s.signalName === name)) return;
    setSignals((prev) => [
      ...prev,
      { signalName: name, role: 'validation', priorityRank: prev.length + 1 },
    ]);
  };

  const removeSignal = (name: string) => {
    setSignals((prev) =>
      prev
        .filter((s) => s.signalName !== name)
        .map((s, i) => ({ ...s, priorityRank: i + 1 })),
    );
  };

  const updateRole = (name: string, role: SignalResponse['role']) => {
    setSignals((prev) =>
      prev.map((s) => (s.signalName === name ? { ...s, role } : s)),
    );
  };

  const addCustom = () => {
    const trimmed = custom.trim();
    if (!trimmed) return;
    addSignal(trimmed);
    setCustom('');
  };

  return (
    <div className="flex flex-col items-center justify-center h-full px-4">
      <div className="max-w-lg w-full space-y-6">
        <h2 className="text-2xl font-semibold text-slate-100">
          Which signals would you check first?
        </h2>
        <p className="text-slate-400">
          Pick 1-3 data points you&rsquo;d want to see. Order matters &mdash;
          your top pick is #1.
        </p>

        {/* Suggested signal chips */}
        <div className="flex flex-wrap gap-2">
          {SUGGESTED_SIGNALS.filter(
            (s) => !signals.some((sig) => sig.signalName === s),
          ).map((s) => (
            <button
              key={s}
              onClick={() => addSignal(s)}
              className="px-3 py-1.5 rounded-full text-sm bg-slate-800 text-slate-300 hover:bg-slate-700 transition-colors"
            >
              <Plus className="w-3 h-3 inline mr-1" />
              {s}
            </button>
          ))}
        </div>

        {/* Custom input */}
        <div className="flex gap-2">
          <input
            type="text"
            value={custom}
            onChange={(e) => setCustom(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && addCustom()}
            placeholder="Or type your own signal..."
            className="flex-1 px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none text-sm"
          />
          <button
            onClick={addCustom}
            className="px-3 py-2 rounded-lg bg-slate-700 text-slate-300 hover:bg-slate-600 text-sm"
          >
            Add
          </button>
        </div>

        {/* Selected signals with role */}
        {signals.length > 0 && (
          <div className="space-y-3">
            <p className="text-xs text-slate-500 uppercase tracking-wide">
              Your priorities (drag order = rank)
            </p>
            {signals.map((s) => (
              <div
                key={s.signalName}
                className="flex items-center gap-3 p-3 rounded-lg bg-slate-800 border border-slate-700"
              >
                <span className="text-blue-400 font-mono text-sm w-6">
                  #{s.priorityRank}
                </span>
                <span className="text-slate-200 flex-1 text-sm font-medium">
                  {s.signalName}
                </span>
                <select
                  value={s.role}
                  onChange={(e) =>
                    updateRole(s.signalName, e.target.value as SignalResponse['role'])
                  }
                  className="text-xs bg-slate-700 border border-slate-600 rounded px-2 py-1 text-slate-300"
                >
                  {ROLE_OPTIONS.map((r) => (
                    <option key={r} value={r}>
                      {ROLE_LABELS[r]}
                    </option>
                  ))}
                </select>
                <button
                  onClick={() => removeSignal(s.signalName)}
                  className="text-slate-500 hover:text-red-400"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}

        <button
          onClick={() => onNext(signals)}
          disabled={signals.length === 0}
          className="w-full py-3 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold transition-colors"
        >
          Next
        </button>
      </div>
    </div>
  );
}
