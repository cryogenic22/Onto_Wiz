'use client';

import { useState } from 'react';
import {
  ArrowRight,
  Bot,
  Braces,
  CheckCircle2,
  ChevronDown,
  CircleAlert,
  Clock3,
  FileWarning,
  FlaskConical,
  GitPullRequestArrow,
  LoaderCircle,
  Play,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';

import { httpControlPlaneClient } from '../api';
import styles from '../control-plane.module.css';
import { scenarios } from '../mock-data';
import type { SimulationMode, SimulationResult } from '../types';
import { SectionTitle, StatusPill } from './Primitives';

interface AgentSimulatorProps {
  candidateQualified: boolean;
  onCreateDelta: () => Promise<void>;
  actionBusy: boolean;
  actionMessage: string;
}

const decisionStatus = (decision: SimulationResult['decision']) => {
  if (decision === 'allow_draft' || decision === 'answer') return 'passed';
  if (decision === 'abstain') return 'review_required';
  return 'failed';
};

function ResultPanel({ result, title, governed }: { result: SimulationResult; title: string; governed: boolean }) {
  return (
    <article className={governed ? styles.governedResult : styles.baselineResult}>
      <div className={styles.resultHeader}>
        <div><span>{title}</span><strong>{governed ? 'Typed context contract' : 'Ungoverned retrieval'}</strong></div>
        <StatusPill status={decisionStatus(result.decision)} label={result.decision.replaceAll('_', ' ').toUpperCase()} />
      </div>
      <div className={styles.confidenceRow}><span>Decision confidence</span><div><i style={{ width: `${result.confidence * 100}%` }} /></div><strong>{Math.round(result.confidence * 100)}%</strong></div>
      <div className={styles.resultAnswer}><span>Returned result</span><p>{result.answer}</p></div>
      <div className={styles.findingsList}>
        <span>Findings and limitations</span>
        {result.findings.map((finding) => <div key={finding}>{governed ? <CheckCircle2 size={14} /> : <CircleAlert size={14} />}<p>{finding}</p></div>)}
      </div>
      {governed && (
        <div className={styles.resultRefs}>
          <div><span>Artifacts used</span>{result.artifactsUsed.map((id) => <code key={id}>{id}</code>)}</div>
          <div><span>Evidence / query receipts</span>{result.evidenceUsed.map((id) => <code key={id}>{id}</code>)}</div>
        </div>
      )}
      <div className={styles.receiptStrip}>
        <Braces size={14} />
        <span><strong>{result.receipt.id}</strong><small>{result.receipt.release} | {result.receipt.reproducible ? 'replayable' : 'not replayable'}</small></span>
      </div>
    </article>
  );
}

export function AgentSimulator({
  candidateQualified,
  onCreateDelta,
  actionBusy,
  actionMessage,
}: AgentSimulatorProps) {
  const [scenarioId, setScenarioId] = useState(scenarios[0].id);
  const [withContext, setWithContext] = useState<SimulationResult | null>(null);
  const [withoutContext, setWithoutContext] = useState<SimulationResult | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState('');
  const selected = scenarios.find((scenario) => scenario.id === scenarioId) ?? scenarios[0];

  const chooseScenario = (id: string) => {
    setScenarioId(id);
    setWithContext(null);
    setWithoutContext(null);
    setError('');
  };

  const run = async () => {
    setRunning(true);
    setError('');
    try {
      const modes: SimulationMode[] = ['candidate', 'without_context'];
      const [governed, baseline] = await Promise.all(modes.map((mode) => httpControlPlaneClient.runSimulation({
        scenarioId,
        mode,
        candidateQualified,
      })));
      setWithContext(governed.data);
      setWithoutContext(baseline.data);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'The deterministic simulation could not run.');
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className={styles.viewStack}>
      <SectionTitle
        eyebrow="Agent simulator"
        title="Test the serving contract, not the storage"
        description="Replay fixed agent workloads against a governed candidate and an ungoverned baseline."
        action={<div className={styles.apiState}><span /><strong>Simulator API</strong><small>deterministic | seed v1</small></div>}
      />

      <div className={styles.simulatorLayout}>
        <aside className={styles.scenarioRail}>
          <span className={styles.eyebrow}>Reference workloads</span>
          <h3>Choose a scenario</h3>
          {scenarios.map((scenario, index) => (
            <button type="button" key={scenario.id} className={scenarioId === scenario.id ? styles.scenarioActive : styles.scenarioButton} onClick={() => chooseScenario(scenario.id)}>
              <span>{String(index + 1).padStart(2, '0')}</span>
              <span><strong>{scenario.name}</strong><small>{scenario.workload}</small></span>
              <ArrowRight size={14} />
            </button>
          ))}
          <div className={styles.simulatorBoundary}><ShieldCheck size={16} /><p><strong>Trust boundary</strong>Raw storage is never exposed. Results return artifact, evidence, policy and release receipts.</p></div>
        </aside>

        <div className={styles.simulatorMain}>
          <section className={styles.scenarioForm}>
            <div className={styles.surfaceHeader}>
              <div><span className={styles.eyebrow}>Structured request</span><h3>{selected.name}</h3></div>
              <StatusPill status={candidateQualified ? 'passed' : 'failed'} label={candidateQualified ? 'rc2 qualified' : 'rc1 blocked'} />
            </div>
            <div className={styles.simFields}>
              <label><span>Market</span><span className={styles.selectWrap}><select aria-label="Simulation market" value={selected.market} disabled><option>{selected.market}</option></select><ChevronDown size={13} /></span></label>
              <label><span>Audience</span><span className={styles.selectWrap}><select aria-label="Simulation audience" value={selected.audience} disabled><option>{selected.audience}</option></select><ChevronDown size={13} /></span></label>
              <label><span>Pack release</span><span className={styles.selectWrap}><select aria-label="Simulation release" value={candidateQualified ? '0.1.1-rc2' : '0.1.1-rc1'} disabled><option>{candidateQualified ? '0.1.1-rc2' : '0.1.1-rc1'}</option></select><ChevronDown size={13} /></span></label>
            </div>
            <label className={styles.promptField}><span>Agent task</span><textarea aria-label="Agent task" value={selected.prompt} readOnly /></label>
            <div className={styles.runBar}>
              <span><FlaskConical size={15} /><strong>A/B run</strong> Candidate context versus no governed context</span>
              <button type="button" className={styles.runButton} disabled={running} onClick={() => void run()}>{running ? <LoaderCircle className={styles.spin} size={16} /> : <Play size={16} fill="currentColor" />} {running ? 'Running trace...' : 'Run simulation'}</button>
            </div>
          </section>

          {error && <div className={styles.errorBanner}><FileWarning size={17} /><span><strong>Simulation failed</strong><p>{error}</p></span></div>}

          {!withContext || !withoutContext ? (
            <section className={styles.simEmptyState}>
              <div className={styles.simEmptyIcon}><Bot size={25} /></div>
              <h3>Run the governed comparison</h3>
              <p>The response will show decision quality, artifacts, exact evidence, trace stages and the immutable simulation receipt.</p>
              {!candidateQualified && <div><CircleAlert size={15} /> The content-draft scenario will correctly abstain while the critical rc1 gate is open.</div>}
            </section>
          ) : (
            <>
              <section className={styles.comparisonGrid} aria-label="Simulation comparison">
                <ResultPanel result={withContext} title="With Auravia candidate" governed />
                <ResultPanel result={withoutContext} title="Without governed context" governed={false} />
              </section>

              <section className={styles.tracePanel}>
                <div className={styles.surfaceHeader}><div><span className={styles.eyebrow}>Decision receipt</span><h3>Governed execution trace</h3></div><code>{withContext.receipt.id}</code></div>
                <div className={styles.traceTimeline}>
                  {withContext.trace.map((step, index) => (
                    <div key={`${step.step}-${index}`}><span>{index + 1}</span><div><strong>{step.step}</strong><p>{step.result}</p></div><time><Clock3 size={12} /> {step.durationMs} ms</time></div>
                  ))}
                </div>
                <div className={styles.traceFooter}>
                  <span><ShieldCheck size={15} /> synthetic reference | production ineligible | no raw identities</span>
                  <button type="button" className={styles.secondaryButton} disabled={actionBusy} onClick={() => void onCreateDelta()}><GitPullRequestArrow size={15} /> Create improvement Delta</button>
                </div>
                {actionMessage.includes('candidate Delta') && <div className={styles.deltaCreated}><Sparkles size={15} /><span>{actionMessage}</span></div>}
              </section>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
