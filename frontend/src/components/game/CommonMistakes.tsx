'use client';

import { useState } from 'react';
import { Plus, X } from 'lucide-react';
import type { MistakeResponse } from '@/types/game';

interface Props {
  onNext: (data: MistakeResponse[]) => void;
}

export default function CommonMistakes({ onNext }: Props) {
  const [mistakes, setMistakes] = useState<MistakeResponse[]>([]);
  const [draft, setDraft] = useState({ wrongConclusion: '', whyWrong: '', unlessEvidence: '' });

  const addMistake = () => {
    if (!draft.wrongConclusion.trim()) return;
    setMistakes((prev) => [...prev, { ...draft }]);
    setDraft({ wrongConclusion: '', whyWrong: '', unlessEvidence: '' });
  };

  const removeMistake = (idx: number) => {
    setMistakes((prev) => prev.filter((_, i) => i !== idx));
  };

  return (
    <div className="flex flex-col items-center justify-center h-full px-4">
      <div className="max-w-lg w-full space-y-6">
        <h2 className="text-2xl font-semibold text-slate-100">
          What do people commonly get wrong here?
        </h2>
        <p className="text-slate-400">
          Flag the traps others fall into with this type of situation.
        </p>

        {/* Existing mistakes */}
        {mistakes.map((m, i) => (
          <div
            key={i}
            className="p-3 rounded-lg bg-slate-800 border border-slate-700 flex items-start gap-3"
          >
            <div className="flex-1">
              <p className="text-sm text-slate-200 font-medium">{m.wrongConclusion}</p>
              {m.whyWrong && (
                <p className="text-xs text-slate-400 mt-1">Why: {m.whyWrong}</p>
              )}
            </div>
            <button
              onClick={() => removeMistake(i)}
              className="text-slate-500 hover:text-red-400 mt-0.5"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ))}

        {/* Add form */}
        <div className="space-y-3 p-4 rounded-lg bg-slate-800/50 border border-slate-700/50">
          <input
            type="text"
            value={draft.wrongConclusion}
            onChange={(e) => setDraft({ ...draft, wrongConclusion: e.target.value })}
            placeholder="Wrong conclusion people jump to..."
            className="w-full px-4 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none text-sm"
          />
          <input
            type="text"
            value={draft.whyWrong}
            onChange={(e) => setDraft({ ...draft, whyWrong: e.target.value })}
            placeholder="Why is it wrong? (optional)"
            className="w-full px-4 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none text-sm"
          />
          <input
            type="text"
            value={draft.unlessEvidence}
            onChange={(e) => setDraft({ ...draft, unlessEvidence: e.target.value })}
            placeholder="Unless this evidence is present... (optional)"
            className="w-full px-4 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none text-sm"
          />
          <button
            onClick={addMistake}
            disabled={!draft.wrongConclusion.trim()}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 disabled:opacity-40 text-slate-200 text-sm transition-colors"
          >
            <Plus className="w-4 h-4" /> Add trap
          </button>
        </div>

        <button
          onClick={() => onNext(mistakes)}
          className="w-full py-3 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold transition-colors"
        >
          {mistakes.length === 0 ? 'Skip' : 'Next'}
        </button>
      </div>
    </div>
  );
}
