'use client';

import { useMemo, useState } from 'react';
import {
  ArrowRight,
  Check,
  CheckCircle2,
  CircleAlert,
  FlaskConical,
  GitBranch,
  LoaderCircle,
  RotateCcw,
  ShieldAlert,
} from 'lucide-react';

import styles from '../control-plane.module.css';
import type { ControlPlaneSnapshot } from '../types';
import { humanize, SectionTitle, StatusPill } from './Primitives';

interface EvaluationCenterProps {
  snapshot: ControlPlaneSnapshot;
  corrected: boolean;
  actionBusy: boolean;
  actionMessage: string;
  onApplyCorrection: () => Promise<void>;
  onOpenArtifact: (artifactId: string) => void;
}

export function EvaluationCenter({
  snapshot,
  corrected,
  actionBusy,
  actionMessage,
  onApplyCorrection,
  onOpenArtifact,
}: EvaluationCenterProps) {
  const [selectedCaseId, setSelectedCaseId] = useState('eval_missing_timepoint_block');
  const selected = useMemo(
    () => snapshot.evalCases.find((item) => item.id === selectedCaseId) ?? snapshot.evalCases[0],
    [selectedCaseId, snapshot.evalCases],
  );
  const selectedCorrected = corrected && selected?.id === 'eval_missing_timepoint_block';

  return (
    <div className={styles.viewStack}>
      <SectionTitle
        eyebrow="Evaluation center"
        title="Route quality by failure mode"
        description="Deterministic cases make correctness, safety, data and causality regressions release-blocking evidence."
        action={<button type="button" className={styles.secondaryButton} disabled={actionBusy}><RotateCcw size={14} /> Run full reference suite</button>}
      />

      <section className={styles.evalHeroBand}>
        <div className={styles.evalScore}>
          <span className={corrected ? styles.scoreRingPassed : styles.scoreRingFailed}><strong>{corrected ? '28' : '27'}</strong><small>/ 28</small></span>
          <div><span className={styles.eyebrow}>Candidate receipt</span><h3>{corrected ? 'Reference gate passed' : 'Candidate gate failed'}</h3><p>{corrected ? 'All golden cases are reproducible. Production remains permanently blocked for this fixture.' : 'One critical semantic regression prevents compilation to a qualified demo release.'}</p></div>
        </div>
        <div className={styles.evalHeroMeta}>
          <div><span>Candidate</span><strong>{corrected ? '0.1.1-rc2' : '0.1.1-rc1'}</strong></div>
          <div><span>Run receipt</span><code>{corrected ? 'eval_28f03c' : 'eval_f40bb9'}</code></div>
          <div><span>Critical failures</span><strong className={corrected ? styles.goodText : styles.dangerText}>{corrected ? 0 : 1}</strong></div>
          <div><span>Runtime</span><strong>2.8 s</strong></div>
        </div>
      </section>

      <section className={styles.evalMatrix}>
        <div className={styles.surfaceHeader}><div><span className={styles.eyebrow}>Workload matrix</span><h3>Evaluation coverage</h3></div><span className={styles.refreshStamp}>Critical failures cannot be averaged away</span></div>
        <div className={styles.matrixHeader}><span>Workload</span><span>Categories</span><span>Critical</span><span>Total</span><span>Gate</span></div>
        {snapshot.evalSuites.map((suite) => {
          const adjustedPassed = corrected && suite.id === 'suite-content' ? suite.total : suite.passed;
          const criticalPassed = corrected && suite.id === 'suite-content' ? suite.criticalTotal : suite.criticalPassed;
          return (
            <div className={styles.matrixRow} key={suite.id}>
              <strong>{suite.workload}</strong>
              <div className={styles.categoryCells}>{suite.categories.map((category) => {
                const passed = corrected && suite.id === 'suite-content' ? category.total : category.passed;
                return <span key={category.name}><small>{category.name}</small><b className={passed === category.total ? styles.goodText : styles.dangerText}>{passed}/{category.total}</b></span>;
              })}</div>
              <span><b>{criticalPassed}/{suite.criticalTotal}</b><small> critical</small></span>
              <span><b>{adjustedPassed}/{suite.total}</b><small> passing</small></span>
              <StatusPill status={adjustedPassed === suite.total ? 'passed' : 'failed'} />
            </div>
          );
        })}
      </section>

      <div className={styles.evalWorkbench}>
        <section className={styles.caseList}>
          <div className={styles.surfaceHeader}><div><span className={styles.eyebrow}>Featured golden cases</span><h3>Regression detail</h3></div></div>
          {snapshot.evalCases.map((item) => {
            const isCorrected = corrected && item.id === 'eval_missing_timepoint_block';
            return (
              <button type="button" key={item.id} className={selected?.id === item.id ? styles.caseRowActive : styles.caseRow} onClick={() => setSelectedCaseId(item.id)}>
                <span className={isCorrected || item.status === 'passed' ? styles.casePassIcon : styles.caseFailIcon}>{isCorrected || item.status === 'passed' ? <Check size={14} /> : <CircleAlert size={14} />}</span>
                <span><strong>{item.name}</strong><code>{item.id}</code><small>{item.workload}</small></span>
                <StatusPill status={isCorrected ? 'passed' : item.status} />
              </button>
            );
          })}
        </section>

        {selected && (
          <section className={styles.caseDetail}>
            <div className={styles.caseDetailHeader}>
              <div><span className={styles.eyebrow}>{selected.workload} | {humanize(selected.severity)}</span><h3>{selected.name}</h3><code>{selected.id}</code></div>
              <StatusPill status={selectedCorrected ? 'passed' : selected.status} label={selectedCorrected ? 'Corrected in rc2' : undefined} />
            </div>

            <div className={styles.caseInput}><span>Test input</span><p>{selected.input}</p></div>
            <div className={styles.expectedActual}>
              <div><span>Expected</span><strong>{selected.expected}</strong></div>
              <div className={selectedCorrected || selected.status === 'passed' ? styles.actualPassed : styles.actualFailed}><span>Actual</span><strong>{selectedCorrected ? 'BLOCK / ERR-CONTENT-SEMANTIC-BROADENING' : selected.actual}</strong></div>
            </div>

            <div className={styles.traceArtifacts}>
              <span>Artifact trace</span>
              {selected.tracedArtifacts.map((artifactId, index) => (
                <span key={artifactId}><button type="button" onClick={() => onOpenArtifact(artifactId)}>{artifactId}</button>{index < selected.tracedArtifacts.length - 1 && <ArrowRight size={13} />}</span>
              ))}
            </div>

            {!selectedCorrected && selected.status === 'failed' ? (
              <div className={styles.correctionPanel}>
                <div><GitBranch size={17} /><span><strong>Proposed governed correction</strong><p>{selected.correction}</p></span></div>
                <button type="button" className={styles.primaryButton} disabled={actionBusy} onClick={() => void onApplyCorrection()}>
                  {actionBusy ? <LoaderCircle className={styles.spin} size={15} /> : <FlaskConical size={15} />}
                  Apply Delta & rerun affected cases
                </button>
              </div>
            ) : (
              <div className={styles.correctionPassed}><CheckCircle2 size={18} /><span><strong>Regression is closed</strong><small>{selectedCorrected ? actionMessage || 'The semantic invariant is restored and the immutable receipt was written.' : 'This case matched its expected governed outcome.'}</small></span></div>
            )}

            <div className={styles.caseFooter}><span>Owner <strong>{selected.owner}</strong></span><span>Determinism <strong>Byte-equivalent replay</strong></span><span>Fixture <strong>auravia-control-plane-v1</strong></span></div>
          </section>
        )}
      </div>

      {!corrected && (
        <section className={styles.hardRuleCallout}><ShieldAlert size={18} /><div><strong>Hard rule</strong><p>A critical semantic broadening failure blocks release even when the aggregate pass rate is 96.4%.</p></div></section>
      )}
    </div>
  );
}
