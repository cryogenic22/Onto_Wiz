'use client';

import { useState } from 'react';
import type { PatternResponse } from '@/types/game';

interface Props {
  onNext: (data: PatternResponse) => void;
}

const FREQUENCY_OPTIONS: { value: PatternResponse['frequency']; label: string; desc: string }[] = [
  { value: 'often', label: 'Often', desc: 'I see this regularly' },
  { value: 'sometimes', label: 'Sometimes', desc: 'Comes up now and then' },
  { value: 'rarely', label: 'Rarely', desc: 'Very unusual pattern' },
  { value: 'never', label: 'Never', desc: 'First time seeing this' },
];

export default function PatternRecognition({ onNext }: Props) {
  const [frequency, setFrequency] = useState<PatternResponse['frequency'] | null>(null);
  const [typicalOutcome, setTypicalOutcome] = useState('');
  const [timeToResolution, setTimeToResolution] = useState('');

  const handleSubmit = () => {
    if (!frequency) return;
    onNext({
      frequency,
      typicalOutcome,
      timeToResolution,
    });
  };

  return (
    <div className="flex flex-col items-center justify-center h-full px-4">
      <div className="max-w-lg w-full space-y-6">
        <h2 className="text-2xl font-semibold text-slate-100">
          Have you seen this before?
        </h2>
        <p className="text-slate-400">
          Your pattern recognition is one of the most valuable things we capture.
        </p>

        {/* Frequency selection */}
        <div className="grid grid-cols-2 gap-3">
          {FREQUENCY_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setFrequency(opt.value)}
              className={`p-4 rounded-lg text-left transition-all border ${
                frequency === opt.value
                  ? 'bg-blue-600/20 border-blue-500 text-blue-100'
                  : 'bg-slate-800 border-slate-700 text-slate-300 hover:border-slate-600'
              }`}
            >
              <span className="block font-semibold text-sm">{opt.label}</span>
              <span className="block text-xs mt-1 opacity-70">{opt.desc}</span>
            </button>
          ))}
        </div>

        {frequency && (
          <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2">
            <div>
              <label className="text-sm text-slate-400 block mb-1">
                How does it usually play out?
              </label>
              <input
                type="text"
                value={typicalOutcome}
                onChange={(e) => setTypicalOutcome(e.target.value)}
                placeholder="e.g., Volume recovers after 2 quarters"
                className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="text-sm text-slate-400 block mb-1">
                Typical time to resolve?
              </label>
              <input
                type="text"
                value={timeToResolution}
                onChange={(e) => setTimeToResolution(e.target.value)}
                placeholder="e.g., 3-6 months"
                className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
              />
            </div>
          </div>
        )}

        <button
          onClick={handleSubmit}
          disabled={!frequency}
          className="w-full py-3 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold transition-colors"
        >
          Next
        </button>
      </div>
    </div>
  );
}
