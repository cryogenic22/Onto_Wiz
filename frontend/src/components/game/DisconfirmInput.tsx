'use client';

import { useState } from 'react';
import type { DisconfirmResponse } from '@/types/game';

interface Props {
  onNext: (data: DisconfirmResponse) => void;
}

export default function DisconfirmInput({ onNext }: Props) {
  const [condition, setCondition] = useState('');
  const [wouldSuggest, setWouldSuggest] = useState('');
  const [wouldRuleOut, setWouldRuleOut] = useState('');

  const handleSubmit = () => {
    onNext({ condition, wouldSuggest, wouldRuleOut });
  };

  return (
    <div className="flex flex-col items-center justify-center h-full px-4">
      <div className="max-w-lg w-full space-y-6">
        <h2 className="text-2xl font-semibold text-slate-100">
          What would change your mind?
        </h2>
        <p className="text-slate-400">
          Think about what evidence could disprove your hypothesis. This is
          optional but very valuable.
        </p>

        <div className="space-y-4">
          <div>
            <label className="text-sm text-slate-400 block mb-1">
              If I saw this...
            </label>
            <input
              type="text"
              value={condition}
              onChange={(e) => setCondition(e.target.value)}
              placeholder='e.g., "NBRx flat but TRx drops"'
              className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="text-sm text-slate-400 block mb-1">
              ...I&rsquo;d suspect instead:
            </label>
            <input
              type="text"
              value={wouldSuggest}
              onChange={(e) => setWouldSuggest(e.target.value)}
              placeholder='e.g., "Access issue at fulfillment level"'
              className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="text-sm text-slate-400 block mb-1">
              ...and I&rsquo;d rule out:
            </label>
            <input
              type="text"
              value={wouldRuleOut}
              onChange={(e) => setWouldRuleOut(e.target.value)}
              placeholder='e.g., "Demand erosion" (optional)'
              className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
            />
          </div>
        </div>

        <button
          onClick={handleSubmit}
          className="w-full py-3 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold transition-colors"
        >
          Next
        </button>

        <button
          onClick={() => onNext({ condition: '', wouldSuggest: '', wouldRuleOut: '' })}
          className="w-full py-2 text-sm text-slate-500 hover:text-slate-300 transition-colors"
        >
          Skip this step
        </button>
      </div>
    </div>
  );
}
