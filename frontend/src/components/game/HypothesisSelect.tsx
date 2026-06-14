'use client';

import { useState } from 'react';
import type { HypothesisCategory, HypothesisResponse } from '@/types/game';
import { HYPOTHESIS_LABELS } from '@/types/game';

interface Props {
  onNext: (data: HypothesisResponse) => void;
}

const CATEGORIES = Object.entries(HYPOTHESIS_LABELS) as [HypothesisCategory, string][];

export default function HypothesisSelect({ onNext }: Props) {
  const [selected, setSelected] = useState<HypothesisCategory | null>(null);
  const [driver, setDriver] = useState('');
  const [confidence, setConfidence] = useState(50);
  const [reasoning, setReasoning] = useState('');

  const canSubmit = selected !== null;

  const handleSubmit = () => {
    if (!selected) return;
    onNext({
      category: selected,
      specificDriver: driver,
      confidence: confidence / 100,
      reasoning,
    });
  };

  return (
    <div className="flex flex-col items-center justify-center h-full px-4">
      <div className="max-w-lg w-full space-y-6">
        <h2 className="text-2xl font-semibold text-slate-100">
          What&rsquo;s your first instinct?
        </h2>
        <p className="text-slate-400">
          Based on what you just read, what do you think is driving this situation?
        </p>

        {/* Category chips */}
        <div className="flex flex-wrap gap-2">
          {CATEGORIES.map(([key, label]) => (
            <button
              key={key}
              onClick={() => setSelected(key)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                selected === key
                  ? 'bg-blue-600 text-white ring-2 ring-blue-400'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Optional specifics (shown after selection) */}
        {selected && (
          <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2">
            <input
              type="text"
              value={driver}
              onChange={(e) => setDriver(e.target.value)}
              placeholder="Any specific driver? (optional)"
              className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
            />

            <textarea
              value={reasoning}
              onChange={(e) => setReasoning(e.target.value)}
              placeholder="Brief reasoning (optional)"
              rows={2}
              className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none resize-none"
            />

            {/* Quick confidence */}
            <div>
              <label className="text-sm text-slate-400 block mb-1">
                Initial confidence: {confidence}%
              </label>
              <input
                type="range"
                min={10}
                max={100}
                step={5}
                value={confidence}
                onChange={(e) => setConfidence(Number(e.target.value))}
                className="w-full accent-blue-500"
              />
            </div>
          </div>
        )}

        <button
          onClick={handleSubmit}
          disabled={!canSubmit}
          className="w-full py-3 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold transition-colors"
        >
          Next
        </button>
      </div>
    </div>
  );
}
