'use client';

import { useCallback, useEffect, useState } from 'react';
import { Boxes, LoaderCircle, RotateCcw, TriangleAlert } from 'lucide-react';

import { httpControlPlaneClient } from './api';
import { AgentSimulator } from './components/AgentSimulator';
import { AppShell, type ViewId } from './components/AppShell';
import { CommandCenter } from './components/CommandCenter';
import { EvaluationCenter } from './components/EvaluationCenter';
import { KnowledgeWorkbench } from './components/KnowledgeWorkbench';
import { ReleaseCenter } from './components/ReleaseCenter';
import styles from './control-plane.module.css';
import type { ControlAction, ControlPlaneSnapshot } from './types';

export default function ContextControlPlane() {
  const [snapshot, setSnapshot] = useState<ControlPlaneSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [activeView, setActiveView] = useState<ViewId>('command');
  const [query, setQuery] = useState('');
  const [selectedArtifactId, setSelectedArtifactId] = useState('claim_auravia_easi75_week16');
  const [corrected, setCorrected] = useState(false);
  const [riskApproved, setRiskApproved] = useState(false);
  const [demoReleased, setDemoReleased] = useState(false);
  const [actionBusy, setActionBusy] = useState(false);
  const [actionMessage, setActionMessage] = useState('');
  const [actionError, setActionError] = useState('');

  const loadSnapshot = useCallback(async () => {
    setLoading(true);
    setLoadError('');
    try {
      const response = await httpControlPlaneClient.getSnapshot();
      setSnapshot(response.data);
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : 'The context snapshot could not be loaded.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void loadSnapshot(); }, [loadSnapshot]);

  const perform = async (action: ControlAction, onAccepted: () => void) => {
    setActionBusy(true);
    setActionError('');
    setActionMessage('');
    try {
      const response = await httpControlPlaneClient.performAction(action);
      onAccepted();
      setActionMessage(response.data.summary);
    } catch (error) {
      setActionError(error instanceof Error ? error.message : 'The simulated control action failed.');
    } finally {
      setActionBusy(false);
    }
  };

  const openArtifact = (artifactId: string) => {
    setSelectedArtifactId(artifactId);
    setActiveView('knowledge');
  };

  if (loading) {
    return (
      <main className={styles.bootScreen}>
        <span><Boxes size={22} /></span>
        <div><strong>Compiling context control plane</strong><small>Loading deterministic Auravia reference state</small></div>
        <LoaderCircle className={styles.spin} size={18} />
      </main>
    );
  }

  if (!snapshot || loadError) {
    return (
      <main className={styles.bootScreen}>
        <span className={styles.bootError}><TriangleAlert size={22} /></span>
        <div><strong>Control-plane snapshot unavailable</strong><small>{loadError || 'The response was empty.'}</small></div>
        <button type="button" className={styles.primaryButton} onClick={() => void loadSnapshot()}><RotateCcw size={15} /> Retry</button>
      </main>
    );
  }

  return (
    <AppShell
      workspace={snapshot.workspace}
      activeView={activeView}
      onViewChange={setActiveView}
      query={query}
      onQueryChange={setQuery}
    >
      {actionError && <div className={styles.globalError}><TriangleAlert size={16} /><span>{actionError}</span><button type="button" onClick={() => setActionError('')} aria-label="Dismiss error">Dismiss</button></div>}

      {activeView === 'command' && (
        <CommandCenter
          snapshot={snapshot}
          corrected={corrected}
          riskApproved={riskApproved}
          demoReleased={demoReleased}
          onNavigate={setActiveView}
          onOpenArtifact={openArtifact}
        />
      )}
      {activeView === 'knowledge' && (
        <KnowledgeWorkbench
          snapshot={snapshot}
          query={query}
          onQueryChange={setQuery}
          selectedId={selectedArtifactId}
          onSelectedIdChange={setSelectedArtifactId}
          corrected={corrected}
        />
      )}
      {activeView === 'evaluations' && (
        <EvaluationCenter
          snapshot={snapshot}
          corrected={corrected}
          actionBusy={actionBusy}
          actionMessage={actionMessage}
          onApplyCorrection={() => perform('apply_eval_correction', () => setCorrected(true))}
          onOpenArtifact={openArtifact}
        />
      )}
      {activeView === 'simulator' && (
        <AgentSimulator
          candidateQualified={corrected}
          actionBusy={actionBusy}
          actionMessage={actionMessage}
          onCreateDelta={() => perform('create_improvement_delta', () => undefined)}
        />
      )}
      {activeView === 'release' && (
        <ReleaseCenter
          snapshot={snapshot}
          corrected={corrected}
          riskApproved={riskApproved}
          demoReleased={demoReleased}
          actionBusy={actionBusy}
          actionMessage={actionMessage}
          onApproveRisk={() => perform('approve_risk_bundle', () => setRiskApproved(true))}
          onCompileDemo={() => perform('compile_demo_release', () => setDemoReleased(true))}
          onOpenSimulator={() => setActiveView('simulator')}
        />
      )}
    </AppShell>
  );
}
