'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Brain, Loader2, Shield, BarChart3 } from 'lucide-react';
import { fetchScenarios } from '@/services/api';
import { useGameSession } from '@/hooks/useGameSession';
import { STEP_ORDER, STEP_LABELS } from '@/types/game';
import type { Scenario } from '@/types/api';

import ScenarioCard from './game/ScenarioCard';
import HypothesisSelect from './game/HypothesisSelect';
import SignalPriority from './game/SignalPriority';
import DisconfirmInput from './game/DisconfirmInput';
import PatternRecognition from './game/PatternRecognition';
import CommonMistakes from './game/CommonMistakes';
import ActionRecommend from './game/ActionRecommend';
import ConfidenceSlider from './game/ConfidenceSlider';
import SessionSummary from './game/SessionSummary';

const COMPLEXITY_COLORS: Record<string, string> = {
  low: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  medium: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  high: 'bg-red-500/20 text-red-400 border-red-500/30',
};

export default function SituationRoom() {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load scenarios on mount
  useEffect(() => {
    let cancelled = false;
    fetchScenarios()
      .then((data) => {
        if (cancelled) return;
        setScenarios(data);
        setLoading(false);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err.message);
        setLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  const scenarioId = selectedScenario?.id ?? '';

  const {
    session,
    advance,
    submitHypothesis,
    submitSignals,
    submitDisconfirm,
    submitPattern,
    submitMistakes,
    submitActions,
    submitConfidence,
    restart,
    submitSession,
    submitState,
  } = useGameSession(scenarioId);

  const handleSelectScenario = (scenario: Scenario) => {
    setSelectedScenario(scenario);
    restart(scenario.id);
  };

  const handlePlayAgain = () => {
    setSelectedScenario(null);
  };

  // Loading state
  if (loading) {
    return (
      <div className="h-screen w-screen bg-slate-950 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
      </div>
    );
  }

  // Error state
  if (error || scenarios.length === 0) {
    return (
      <div className="h-screen w-screen bg-slate-950 flex flex-col items-center justify-center text-slate-400 gap-4">
        <Brain className="w-12 h-12 text-slate-600" />
        <p className="text-lg">Could not load scenarios.</p>
        <p className="text-sm text-slate-500">
          {error ?? 'No scenarios available. Is the backend running?'}
        </p>
      </div>
    );
  }

  // Scenario picker — no scenario selected yet
  if (!selectedScenario) {
    return (
      <div className="h-screen w-screen bg-slate-950 text-slate-200 flex flex-col overflow-hidden">
        <header className="h-14 border-b border-slate-800/50 flex items-center px-6 bg-slate-900/30 backdrop-blur shrink-0">
          <Brain className="w-5 h-5 text-blue-400 mr-2" />
          <span className="font-semibold text-slate-200">Situation Room</span>
          <span className="mx-3 text-slate-700">|</span>
          <span className="text-sm text-slate-400">Choose a scenario</span>
          <div className="ml-auto flex items-center gap-3">
            <Link href="/curator" className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors">
              <Shield className="w-3.5 h-3.5" />
              Curator
            </Link>
            <Link href="/sme-dashboard" className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors">
              <BarChart3 className="w-3.5 h-3.5" />
              SME Impact
            </Link>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-6xl mx-auto">
            <h2 className="text-2xl font-semibold text-slate-100 mb-2">Select a Scenario</h2>
            <p className="text-slate-400 mb-6">Pick a clinical scenario to begin your reasoning exercise.</p>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {scenarios.map((s) => (
                <button
                  key={s.id}
                  onClick={() => handleSelectScenario(s)}
                  className="text-left p-4 rounded-xl border border-slate-800 bg-slate-900/50 hover:bg-slate-800/70 hover:border-slate-700 transition-all group"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-mono text-slate-500">{s.id}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full border ${COMPLEXITY_COLORS[s.complexity_level] ?? COMPLEXITY_COLORS.medium}`}>
                      {s.complexity_level}
                    </span>
                  </div>
                  <h3 className="font-semibold text-slate-200 group-hover:text-white mb-1.5 text-sm leading-snug">
                    {s.name}
                  </h3>
                  <p className="text-xs text-slate-400 line-clamp-2 mb-3">{s.description}</p>
                  <div className="flex flex-wrap gap-1.5">
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/15 text-blue-400 border border-blue-500/20">
                      {s.therapeutic_area}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/15 text-purple-400 border border-purple-500/20">
                      {s.indication}
                    </span>
                    {s.brand_context?.lifecycle && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700/50 text-slate-400">
                        {s.brand_context.lifecycle}
                      </span>
                    )}
                    {s.line_of_therapy && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-700/50 text-slate-400">
                        {s.line_of_therapy}
                      </span>
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </main>
      </div>
    );
  }

  // Step progress indicator
  const currentStepIdx = STEP_ORDER.indexOf(session.currentStep);

  return (
    <div className="h-screen w-screen bg-slate-950 text-slate-200 flex flex-col overflow-hidden">
      {/* Header — minimal, warm */}
      <header className="h-14 border-b border-slate-800/50 flex items-center px-6 bg-slate-900/30 backdrop-blur shrink-0">
        <Brain className="w-5 h-5 text-blue-400 mr-2" />
        <span className="font-semibold text-slate-200">Situation Room</span>
        <span className="mx-3 text-slate-700">|</span>
        <span className="text-sm text-slate-400">
          {STEP_LABELS[session.currentStep]}
        </span>
        <div className="ml-auto flex items-center gap-3">
          <Link href="/curator" className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors">
            <Shield className="w-3.5 h-3.5" />
            Curator
          </Link>
          <Link href="/sme-dashboard" className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors">
            <BarChart3 className="w-3.5 h-3.5" />
            SME Impact
          </Link>
          <div className="flex items-center gap-1">
          {STEP_ORDER.map((step, i) => (
            <div
              key={step}
              className={`w-2 h-2 rounded-full transition-colors ${
                i < currentStepIdx
                  ? 'bg-emerald-500'
                  : i === currentStepIdx
                    ? 'bg-blue-400'
                    : 'bg-slate-700'
              }`}
            />
          ))}
          </div>
        </div>
      </header>

      {/* Main content — single step at a time */}
      <main className="flex-1 overflow-hidden">
        {session.currentStep === 'scenario' && (
          <ScenarioCard scenario={selectedScenario} onNext={() => advance()} />
        )}
        {session.currentStep === 'hypothesis' && (
          <HypothesisSelect onNext={submitHypothesis} />
        )}
        {session.currentStep === 'signals' && (
          <SignalPriority onNext={submitSignals} />
        )}
        {session.currentStep === 'disconfirm' && (
          <DisconfirmInput onNext={submitDisconfirm} />
        )}
        {session.currentStep === 'pattern' && (
          <PatternRecognition onNext={submitPattern} />
        )}
        {session.currentStep === 'mistakes' && (
          <CommonMistakes onNext={submitMistakes} />
        )}
        {session.currentStep === 'actions' && (
          <ActionRecommend onNext={submitActions} />
        )}
        {session.currentStep === 'confidence' && (
          <ConfidenceSlider
            initialConfidence={session.responses.hypothesis?.confidence}
            onNext={submitConfidence}
          />
        )}
        {session.currentStep === 'summary' && (
          <SessionSummary
            session={session}
            onPlayAgain={handlePlayAgain}
            onSubmit={submitSession}
            submitState={submitState}
          />
        )}
      </main>
    </div>
  );
}
