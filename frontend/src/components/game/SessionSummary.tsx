'use client';

import { useState } from 'react';
import { CheckCircle, Clock, BarChart3, RefreshCw, Upload, Loader2, AlertCircle } from 'lucide-react';
import type { GameSession } from '@/types/game';
import type { SessionResult } from '@/types/api';
import { HYPOTHESIS_LABELS } from '@/types/game';

interface Props {
  session: GameSession;
  onPlayAgain: () => void;
  onSubmit: () => Promise<SessionResult | null>;
  submitState: {
    submitting: boolean;
    submitted: boolean;
    result: SessionResult | null;
    error: string | null;
  };
}

function formatDuration(ms: number): string {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const remaining = seconds % 60;
  return minutes > 0 ? `${minutes}m ${remaining}s` : `${remaining}s`;
}

export default function SessionSummary({ session, onPlayAgain, onSubmit, submitState }: Props) {
  const { responses, startedAt, completedAt } = session;
  const [now] = useState(() => Date.now());
  const duration = completedAt ? completedAt - startedAt : now - startedAt;

  return (
    <div className="flex flex-col items-center justify-center h-full px-4 overflow-y-auto">
      <div className="max-w-lg w-full space-y-8 py-8">
        <div className="text-center space-y-3">
          <CheckCircle className="w-12 h-12 text-emerald-400 mx-auto" />
          <h2 className="text-2xl font-semibold text-slate-100">Captured. Thank you.</h2>
          <p className="text-slate-400">
            Your judgment helps explain real-world performance patterns. Here&rsquo;s what you shared.
          </p>
        </div>
        <div className="flex items-center justify-center gap-2 text-sm text-slate-500">
          <Clock className="w-4 h-4" />
          <span>Session time: {formatDuration(duration)}</span>
        </div>
        <ResponseCards responses={responses} />
        <SubmitSection submitState={submitState} onSubmit={onSubmit} onPlayAgain={onPlayAgain} />
      </div>
    </div>
  );
}

function SummaryBlock({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700/50">
      <h3 className="text-xs uppercase tracking-wide text-slate-500 mb-2">{title}</h3>
      {children}
    </div>
  );
}

function ResponseCards({ responses }: { responses: GameSession['responses'] }) {
  return (
    <div className="space-y-4">
      {responses.hypothesis && (
        <SummaryBlock title="Your hypothesis">
          <p className="text-slate-200 font-medium">{HYPOTHESIS_LABELS[responses.hypothesis.category]}</p>
          {responses.hypothesis.specificDriver && (
            <p className="text-sm text-slate-400 mt-1">Specifically: {responses.hypothesis.specificDriver}</p>
          )}
          {responses.hypothesis.reasoning && (
            <p className="text-sm text-slate-500 mt-1 italic">&ldquo;{responses.hypothesis.reasoning}&rdquo;</p>
          )}
        </SummaryBlock>
      )}
      {responses.signals && responses.signals.length > 0 && (
        <SummaryBlock title="Signals you'd check">
          <div className="flex flex-wrap gap-2">
            {responses.signals.map((s) => (
              <span key={s.signalName} className="px-3 py-1 rounded-full bg-slate-700 text-sm text-slate-300">
                #{s.priorityRank} {s.signalName}
              </span>
            ))}
          </div>
        </SummaryBlock>
      )}
      {responses.pattern && (
        <SummaryBlock title="Pattern recognition">
          <p className="text-slate-300 text-sm">
            Frequency: <span className="font-medium">{responses.pattern.frequency}</span>
            {responses.pattern.typicalOutcome && ` \u2014 ${responses.pattern.typicalOutcome}`}
          </p>
        </SummaryBlock>
      )}
      {responses.actions && responses.actions.length > 0 && (
        <SummaryBlock title="Recommended actions">
          <ul className="space-y-1">
            {responses.actions.map((a, i) => (
              <li key={i} className="text-sm text-slate-300">
                <span className="text-blue-400 font-mono">#{a.priority}</span> {a.action}
              </li>
            ))}
          </ul>
        </SummaryBlock>
      )}
      {responses.confidence && (
        <SummaryBlock title="Final confidence">
          <div className="flex items-center gap-3">
            <BarChart3 className="w-5 h-5 text-blue-400" />
            <span className="text-2xl font-bold text-blue-400">
              {Math.round(responses.confidence.finalConfidence * 100)}%
            </span>
          </div>
        </SummaryBlock>
      )}
    </div>
  );
}

function SubmitSection({
  submitState,
  onSubmit,
  onPlayAgain,
}: {
  submitState: Props['submitState'];
  onSubmit: () => Promise<SessionResult | null>;
  onPlayAgain: () => void;
}) {
  if (submitState.submitted && submitState.result) {
    const { result } = submitState;
    return (
      <>
        <div className="p-4 rounded-lg bg-emerald-900/20 border border-emerald-800/50 text-sm text-emerald-300 space-y-2">
          <p className="font-medium">Submitted to Ontology</p>
          <p>{result.deltas_generated} delta{result.deltas_generated !== 1 ? 's' : ''} generated from your session.</p>
          <p className="text-xs text-emerald-400/60 font-mono">Session: {result.session_id}</p>
        </div>
        <button
          onClick={onPlayAgain}
          className="w-full py-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold transition-colors flex items-center justify-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Try another scenario
        </button>
      </>
    );
  }

  return (
    <>
      {submitState.error && (
        <div className="p-3 rounded-lg bg-red-900/20 border border-red-800/50 text-sm text-red-300 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
          <span>{submitState.error}</span>
        </div>
      )}
      <button
        onClick={onSubmit}
        disabled={submitState.submitting}
        className="w-full py-3 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold transition-colors flex items-center justify-center gap-2"
      >
        {submitState.submitting ? (
          <><Loader2 className="w-4 h-4 animate-spin" /> Submitting&hellip;</>
        ) : (
          <><Upload className="w-4 h-4" /> Submit to Ontology</>
        )}
      </button>
      {!submitState.submitting && (
        <button
          onClick={onPlayAgain}
          className="w-full py-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold transition-colors flex items-center justify-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Skip &mdash; Try another scenario
        </button>
      )}
    </>
  );
}
