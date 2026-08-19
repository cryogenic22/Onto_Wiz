'use client';

import {
  ArrowRight,
  Ban,
  Check,
  CheckCircle2,
  CircleAlert,
  FileCheck2,
  Fingerprint,
  FlaskConical,
  GitCompareArrows,
  LoaderCircle,
  LockKeyhole,
  PackageCheck,
  ShieldCheck,
} from 'lucide-react';

import styles from '../control-plane.module.css';
import type { ControlPlaneSnapshot } from '../types';
import { SectionTitle, StatusPill } from './Primitives';

interface ReleaseCenterProps {
  snapshot: ControlPlaneSnapshot;
  corrected: boolean;
  riskApproved: boolean;
  demoReleased: boolean;
  actionBusy: boolean;
  actionMessage: string;
  onApproveRisk: () => Promise<void>;
  onCompileDemo: () => Promise<void>;
  onOpenSimulator: () => void;
}

export function ReleaseCenter({
  snapshot,
  corrected,
  riskApproved,
  demoReleased,
  actionBusy,
  actionMessage,
  onApproveRisk,
  onCompileDemo,
  onOpenSimulator,
}: ReleaseCenterProps) {
  const ready = corrected && riskApproved;
  const candidateVersion = corrected ? '0.1.1-rc2' : snapshot.workspace.candidateRelease;
  const gates = [
    { name: 'Exact manifest and deterministic rebuild', detail: 'Compiler digest reproduced from pinned layers', passed: true, critical: true },
    { name: 'Golden evaluation receipt', detail: corrected ? '28 / 28 passed; zero critical failures' : '27 / 28 passed; semantic-invariant failure open', passed: corrected, critical: true },
    { name: 'Scoped human decisions current', detail: riskApproved ? 'Synthetic MLR decision recorded for US HCP scope' : 'risk_bundle_us_hcp_core review pending', passed: riskApproved, critical: true },
    { name: 'Tenant and access isolation', detail: 'Cross-client case denied; aggregate-only data access enforced', passed: true, critical: true },
    { name: 'Staleness policy applied', detail: corrected ? 'Critical propagation closed; 2 non-blocking items remain' : 'Candidate claim variant blocks dependent serving', passed: corrected, critical: true },
    { name: 'Rollback evidence', detail: '0.1.0-reference remains addressable and replayable', passed: true, critical: false },
  ];

  return (
    <div className={styles.viewStack}>
      <SectionTitle
        eyebrow="Release center"
        title="Qualify a compiled context release"
        description="A release is a pinned, diffable artifact with human decisions, eval receipts and rollback evidence."
        action={<StatusPill status={demoReleased ? 'passed' : ready ? 'candidate' : 'failed'} label={demoReleased ? 'Demo released' : ready ? 'Ready for demo' : 'Release blocked'} />}
      />

      <section className={styles.releaseHero}>
        <div className={styles.releaseIdentity}>
          <span className={styles.releaseIcon}><PackageCheck size={23} /></span>
          <div><span className={styles.eyebrow}>synthetic.pharma.marketing.auravia</span><h2>{candidateVersion}</h2><p>Candidate compiled from 5 immutable layers | reference channel only</p></div>
        </div>
        <div className={styles.releaseComparison}><span>{snapshot.workspace.currentRelease}</span><ArrowRight size={16} /><strong>{candidateVersion}</strong></div>
        <div className={styles.releaseDigest}><Fingerprint size={16} /><span><small>Candidate digest</small><code>{corrected ? '9aec02b75895d28...' : '970c38e9f8a40d7...'}</code></span></div>
      </section>

      <div className={styles.releaseGrid}>
        <section className={styles.releaseDiff}>
          <div className={styles.surfaceHeader}><div><span className={styles.eyebrow}>Semantic comparison</span><h3>Candidate diff</h3></div><GitCompareArrows size={18} /></div>
          <div className={styles.diffCounts}><div><strong>2</strong><span>added</span></div><div><strong>{corrected ? 3 : 2}</strong><span>changed</span></div><div><strong>{corrected ? 0 : 1}</strong><span>invalidated</span></div><div><strong>124</strong><span>unchanged</span></div></div>
          <div className={styles.semanticDiff}>
            <div><span className={corrected ? styles.diffAdded : styles.diffRemoved}>{corrected ? '+' : '-'}</span><code>claim_variant_easi75_us_hcp_v1</code><StatusPill status={corrected ? 'passed' : 'failed'} label={corrected ? 'Invariant restored' : 'Release block'} /></div>
            <p><span>semantic_invariants.timepoint_week_16</span><strong>{corrected ? 'PRESENT' : 'MISSING'}</strong></p>
            <small>{corrected ? 'rc2 restores the canonical week-16 constraint and records a review receipt.' : 'rc1 broadens the proposition by allowing a claim variant without its required timepoint.'}</small>
          </div>
          <div className={styles.diffLists}>
            <div><span>Added</span>{snapshot.releaseDiff.added.map((id) => <code key={id}>+ {id}</code>)}</div>
            <div><span>Changed</span>{snapshot.releaseDiff.changed.map((id) => <code key={id}>~ {id}</code>)}</div>
            {!corrected && <div><span>Invalidated</span>{snapshot.releaseDiff.invalidated.map((id) => <code key={id}>! {id}</code>)}</div>}
          </div>
        </section>

        <section className={styles.gateChecklist}>
          <div className={styles.surfaceHeader}><div><span className={styles.eyebrow}>Hard gates</span><h3>Release qualification</h3></div><strong className={ready ? styles.goodText : styles.dangerText}>{gates.filter((gate) => gate.passed).length}/{gates.length}</strong></div>
          {gates.map((gate) => (
            <div className={styles.gateRow} key={gate.name}>
              <span className={gate.passed ? styles.gatePass : styles.gateFail}>{gate.passed ? <Check size={14} /> : <CircleAlert size={14} />}</span>
              <span><strong>{gate.name}</strong><small>{gate.detail}</small></span>
              {gate.critical && <code>HARD</code>}
            </div>
          ))}
          {!riskApproved && (
            <button type="button" className={styles.reviewAction} disabled={actionBusy} onClick={() => void onApproveRisk()}>
              {actionBusy ? <LoaderCircle className={styles.spin} size={16} /> : <FileCheck2 size={16} />}
              <span><strong>Record synthetic scoped MLR decision</strong><small>Approve risk_bundle_us_hcp_core for US HCP demo scope</small></span>
              <ArrowRight size={15} />
            </button>
          )}
          {riskApproved && <div className={styles.approvalReceipt}><CheckCircle2 size={16} /><span><strong>Scoped review decision recorded</strong><small>review_synth_mlr_20260625 | append-only</small></span></div>}
        </section>
      </div>

      <section className={styles.layerManifest}>
        <div className={styles.surfaceHeader}><div><span className={styles.eyebrow}>Compiled manifest</span><h3>Layer pins</h3></div><LockKeyhole size={17} /></div>
        <div className={styles.manifestHeader}><span>Layer</span><span>Version</span><span>Digest</span><span>Precedence</span></div>
        {snapshot.releaseDiff.layerPins.map((pin, index) => (
          <div className={styles.manifestRow} key={pin.layer}><span><ShieldCheck size={14} /> {pin.layer}</span><code>{pin.layer === 'brand_auravia_synthetic' ? candidateVersion : pin.version}</code><code>{pin.layer === 'brand_auravia_synthetic' && corrected ? '9aec02b' : pin.hash}</code><strong>{(index + 1) * 10}</strong></div>
        ))}
      </section>

      <section className={styles.releaseActions}>
        <div className={ready ? styles.demoChannelReady : styles.demoChannelBlocked}>
          <FlaskConical size={20} />
          <div><strong>Demo channel</strong><p>{demoReleased ? `${candidateVersion} is live for deterministic agent simulation.` : ready ? 'All hard reference gates are satisfied.' : 'Close the remaining hard gates before publishing.'}</p></div>
          {demoReleased ? <button type="button" className={styles.secondaryButton} onClick={onOpenSimulator}>Open simulator <ArrowRight size={14} /></button> : <button type="button" className={styles.primaryButton} disabled={!ready || actionBusy} onClick={() => void onCompileDemo()}>{actionBusy ? <LoaderCircle className={styles.spin} size={15} /> : <PackageCheck size={15} />} Publish to demo</button>}
        </div>
        <div className={styles.productionBlocked}>
          <Ban size={20} />
          <div><strong>Production channel</strong><p>Permanent blocker: synthetic_reference=true and production_eligible=false.</p></div>
          <button type="button" disabled><LockKeyhole size={14} /> Production disabled</button>
        </div>
      </section>

      {actionMessage && <div className={styles.actionReceipt}><CheckCircle2 size={16} /><span><strong>Simulated action receipt</strong><small>{actionMessage}</small></span></div>}
    </div>
  );
}
