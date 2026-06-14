'use client';

import { useState } from 'react';
import type { ConfidenceResponse } from '@/types/game';

interface Props {
  initialConfidence?: number;
  onNext: (data: ConfidenceResponse) => void;
}

const CALIBRATION_LABELS: Record<number, string> = {
  10: 'Very uncertain',
  20: 'Quite uncertain',
  30: 'More unsure than sure',
  40: 'Leaning uncertain',
  50: 'Coin flip',
  60: 'Leaning confident',
  70: 'Moderately confident',
  80: 'Fairly confident',
  90: 'Very confident',
  100: 'Certain',
};

function getLabel(value: number): string {
  const keys = Object.keys(CALIBRATION_LABELS).map(Number);
  const closest = keys.reduce((prev, curr) =>
    Math.abs(curr - value) < Math.abs(prev - value) ? curr : prev,
  );
  return CALIBRATION_LABELS[closest];
}

export default function ConfidenceSlider({ initialConfidence, onNext }: Props) {
  const [confidence, setConfidence] = useState(
    initialConfidence ? Math.round(initialConfidence * 100) : 50,
  );
  const [reasoning, setReasoning] = useState('');

  const handleSubmit = () => {
    onNext({ finalConfidence: confidence / 100, reasoning });
  };

  return (
    <div className="flex flex-col items-center justify-center h-full px-4">
      <div className="max-w-lg w-full space-y-8">
        <h2 className="text-2xl font-semibold text-slate-100">
          How confident are you in your overall assessment?
        </h2>
        <p className="text-slate-400">
          After everything you&rsquo;ve considered, calibrate your confidence.
          There&rsquo;s no wrong answer &mdash; accurate uncertainty is valuable.
        </p>

        {/* Big confidence display */}
        <div className="text-center space-y-2">
          <div className="text-6xl font-bold text-blue-400">{confidence}%</div>
          <div className="text-lg text-slate-300">{getLabel(confidence)}</div>
        </div>

        {/* Slider */}
        <div className="space-y-2">
          <input
            type="range"
            min={10}
            max={100}
            step={5}
            value={confidence}
            onChange={(e) => setConfidence(Number(e.target.value))}
            className="w-full h-2 accent-blue-500 cursor-pointer"
          />
          <div className="flex justify-between text-xs text-slate-500">
            <span>Very uncertain</span>
            <span>Certain</span>
          </div>
        </div>

        {/* Optional reasoning */}
        <textarea
          value={reasoning}
          onChange={(e) => setReasoning(e.target.value)}
          placeholder="What's driving your confidence level? (optional)"
          rows={2}
          className="w-full px-4 py-3 rounded-lg bg-slate-800 border border-slate-700 text-slate-200 placeholder-slate-500 focus:border-blue-500 focus:outline-none resize-none"
        />

        <button
          onClick={handleSubmit}
          className="w-full py-3 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold transition-colors"
        >
          Submit
        </button>
      </div>
    </div>
  );
}
