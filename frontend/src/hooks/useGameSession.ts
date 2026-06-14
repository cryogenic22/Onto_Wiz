'use client';

import { useState, useCallback } from 'react';
import type {
  GameSession,
  GameResponses,
  HypothesisResponse,
  SignalResponse,
  DisconfirmResponse,
  PatternResponse,
  MistakeResponse,
  ActionResponse,
  ConfidenceResponse,
} from '@/types/game';
import type { SessionResult } from '@/types/api';
import { STEP_ORDER } from '@/types/game';
import { submitGameSession } from '@/services/api';

function generateId(): string {
  return `gs_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

export function useGameSession(scenarioId: string) {
  const [session, setSession] = useState<GameSession>(() => ({
    sessionId: generateId(),
    scenarioId,
    currentStep: 'scenario',
    responses: {},
    startedAt: Date.now(),
  }));

  const advance = useCallback(
    (stepData?: Partial<GameResponses>) => {
      setSession((prev) => {
        const idx = STEP_ORDER.indexOf(prev.currentStep);
        const nextStep =
          idx < STEP_ORDER.length - 1 ? STEP_ORDER[idx + 1] : prev.currentStep;
        const isComplete = nextStep === 'summary';

        return {
          ...prev,
          currentStep: nextStep,
          responses: { ...prev.responses, ...stepData },
          ...(isComplete ? { completedAt: Date.now() } : {}),
        };
      });
    },
    [],
  );

  const submitHypothesis = useCallback(
    (data: HypothesisResponse) => advance({ hypothesis: data }),
    [advance],
  );

  const submitSignals = useCallback(
    (data: SignalResponse[]) => advance({ signals: data }),
    [advance],
  );

  const submitDisconfirm = useCallback(
    (data: DisconfirmResponse) => advance({ disconfirm: data }),
    [advance],
  );

  const submitPattern = useCallback(
    (data: PatternResponse) => advance({ pattern: data }),
    [advance],
  );

  const submitMistakes = useCallback(
    (data: MistakeResponse[]) => advance({ mistakes: data }),
    [advance],
  );

  const submitActions = useCallback(
    (data: ActionResponse[]) => advance({ actions: data }),
    [advance],
  );

  const submitConfidence = useCallback(
    (data: ConfidenceResponse) => advance({ confidence: data }),
    [advance],
  );

  const [submitState, setSubmitState] = useState<{
    submitting: boolean;
    submitted: boolean;
    result: SessionResult | null;
    error: string | null;
  }>({ submitting: false, submitted: false, result: null, error: null });

  const restart = useCallback(
    (newScenarioId?: string) => {
      setSession({
        sessionId: generateId(),
        scenarioId: newScenarioId ?? scenarioId,
        currentStep: 'scenario',
        responses: {},
        startedAt: Date.now(),
      });
      setSubmitState({ submitting: false, submitted: false, result: null, error: null });
    },
    [scenarioId],
  );

  const submitSession = useCallback(async () => {
    setSubmitState((prev) => ({ ...prev, submitting: true, error: null }));
    try {
      const result = await submitGameSession(session.scenarioId, session.responses);
      setSubmitState({ submitting: false, submitted: true, result, error: null });
      return result;
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Submission failed';
      setSubmitState((prev) => ({ ...prev, submitting: false, error: msg }));
      return null;
    }
  }, [session.scenarioId, session.responses]);

  return {
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
  };
}
