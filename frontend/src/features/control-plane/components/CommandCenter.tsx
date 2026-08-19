import {
  ArrowRight,
  Bot,
  CheckCircle2,
  CircleAlert,
  Database,
  FileCheck2,
  GitBranch,
  ShieldAlert,
} from 'lucide-react';

import styles from '../control-plane.module.css';
import type { ControlPlaneSnapshot } from '../types';
import type { ViewId } from './AppShell';
import { SectionTitle, StatusPill } from './Primitives';

interface CommandCenterProps {
  snapshot: ControlPlaneSnapshot;
  corrected: boolean;
  riskApproved: boolean;
  demoReleased: boolean;
  onNavigate: (view: ViewId) => void;
  onOpenArtifact: (artifactId: string) => void;
}

const flow = [
  { label: 'Sources', detail: '6 governed', icon: Database },
  { label: 'Candidates', detail: '4 changed', icon: GitBranch },
  { label: 'Human decisions', detail: '1 pending', icon: FileCheck2 },
  { label: 'Eval gate', detail: '28 golden', icon: ShieldAlert },
  { label: 'Agent contracts', detail: '4 consumers', icon: Bot },
];

const consumers = [
  ['AGENT-CONTENT-DRAFT-01', 'Content brief', '3 artifacts'],
  ['AGENT-MLR-COPILOT-01', 'Draft validation', '4 artifacts'],
  ['AGENT-BRAND-PERFORMANCE-01', 'Metric diagnosis', '11 contracts'],
  ['AGENT-CHANNEL-ORCHESTRATOR-01', 'Next action', '6 policies'],
];

export function CommandCenter({
  snapshot,
  corrected,
  riskApproved,
  demoReleased,
  onNavigate,
  onOpenArtifact,
}: CommandCenterProps) {
  const passed = corrected ? 28 : 27;
  const blockerCount = Number(!corrected) + Number(!riskApproved);

  return (
    <div className={styles.viewStack}>
      <SectionTitle
        eyebrow="Pack command center"
        title="Is this context safe to serve?"
        description="One operational view of evidence, semantics, evaluation and release readiness."
        action={<span className={styles.refreshStamp}>Snapshot | 25 Jun 2026 10:00 UTC</span>}
      />

      <section className={styles.flowBand} aria-label="Context lifecycle">
        {flow.map((step, index) => {
          const Icon = step.icon;
          return (
            <div className={styles.flowStep} key={step.label}>
              <span className={styles.flowIcon}><Icon size={16} aria-hidden="true" /></span>
              <span><strong>{step.label}</strong><small>{step.detail}</small></span>
              {index < flow.length - 1 && <ArrowRight className={styles.flowArrow} size={15} aria-hidden="true" />}
            </div>
          );
        })}
      </section>

      <section className={styles.statBand} aria-label="Pack health summary">
        <div><span>Candidate</span><strong>{corrected ? '0.1.1-rc2' : snapshot.workspace.candidateRelease}</strong><small>vs {snapshot.workspace.currentRelease}</small></div>
        <div><span>Golden evaluations</span><strong className={corrected ? styles.goodText : styles.dangerText}>{passed} / 28</strong><small>{corrected ? 'Reference gate passed' : '1 critical failure'}</small></div>
        <div><span>Evidence coverage</span><strong>96%</strong><small>Material claims exact-spanned</small></div>
        <div><span>Stale dependencies</span><strong className={styles.warningText}>{corrected ? 2 : 3}</strong><small>1 review expires tomorrow</small></div>
        <div><span>Release state</span><strong className={blockerCount === 0 ? styles.goodText : styles.dangerText}>{demoReleased ? 'Demo live' : blockerCount === 0 ? 'Ready' : 'Blocked'}</strong><small>{blockerCount} hard blocker{blockerCount === 1 ? '' : 's'}</small></div>
      </section>

      {blockerCount > 0 ? (
        <section className={styles.blockerBanner} aria-label="Release blockers">
          <CircleAlert size={21} aria-hidden="true" />
          <div>
            <strong>Candidate cannot enter the demo release channel</strong>
            <p>{!corrected ? 'A critical semantic-invariant regression remains open. ' : ''}{!riskApproved ? 'The scoped risk-bundle review is pending.' : ''}</p>
          </div>
          <div className={styles.bannerActions}>
            {!corrected && <button type="button" className={styles.secondaryButton} onClick={() => onNavigate('evaluations')}>Review failure</button>}
            {!riskApproved && <button type="button" className={styles.primaryButton} onClick={() => onOpenArtifact('risk_bundle_us_hcp_core')}>Inspect risk bundle</button>}
          </div>
        </section>
      ) : (
        <section className={styles.readyBanner} aria-label="Release ready">
          <CheckCircle2 size={21} aria-hidden="true" />
          <div><strong>Reference gates are satisfied</strong><p>The synthetic candidate is qualified for the demo channel. Production remains permanently disabled.</p></div>
          <button type="button" className={styles.primaryButton} onClick={() => onNavigate('release')}>Open release center</button>
        </section>
      )}

      <div className={styles.dashboardGrid}>
        <section className={styles.toolSurface}>
          <div className={styles.surfaceHeader}><div><span className={styles.eyebrow}>Coverage</span><h3>Domain portfolio</h3></div><button type="button" className={styles.textButton} onClick={() => onNavigate('knowledge')}>Open catalog <ArrowRight size={14} /></button></div>
          <div className={styles.domainList}>
            {snapshot.domains.map((domain) => (
              <div className={styles.domainRow} key={domain.id}>
                <div><strong>{domain.name}</strong><span>{domain.artifactCount} artifacts</span></div>
                <div className={styles.coverageTrack} aria-label={`${domain.evalCoverage}% evaluation coverage`}><span style={{ width: `${domain.evalCoverage}%` }} /></div>
                <b>{domain.evalCoverage}%</b>
                <StatusPill status={domain.health} />
              </div>
            ))}
          </div>
        </section>

        <section className={styles.toolSurface}>
          <div className={styles.surfaceHeader}><div><span className={styles.eyebrow}>Failure-mode coverage</span><h3>Evaluation posture</h3></div><button type="button" className={styles.textButton} onClick={() => onNavigate('evaluations')}>Inspect cases <ArrowRight size={14} /></button></div>
          <div className={styles.evalCompactList}>
            {snapshot.evalSuites.map((suite) => {
              const suitePassed = corrected && suite.id === 'suite-content' ? suite.total : suite.passed;
              return (
                <div className={styles.evalCompactRow} key={suite.id}>
                  <div><strong>{suite.workload}</strong><span>{suite.criticalPassed + (corrected && suite.id === 'suite-content' ? 1 : 0)}/{suite.criticalTotal} critical</span></div>
                  <div className={styles.evalSegments} aria-label={`${suitePassed} of ${suite.total} passed`}>
                    {Array.from({ length: suite.total }, (_, index) => <i key={index} className={index < suitePassed ? styles.segmentPass : styles.segmentFail} />)}
                  </div>
                  <b>{suitePassed}/{suite.total}</b>
                </div>
              );
            })}
          </div>
        </section>

        <section className={styles.toolSurface}>
          <div className={styles.surfaceHeader}><div><span className={styles.eyebrow}>Impact propagation</span><h3>Why this candidate is stale</h3></div><StatusPill status={corrected ? 'at_risk' : 'blocked_pending_review'} /></div>
          <div className={styles.impactChain}>
            <button type="button" onClick={() => onOpenArtifact('claim_variant_easi75_us_hcp_v1')}><span>Root change</span><strong>{corrected ? 'Invariant restored in rc2' : 'timepoint_week_16 missing'}</strong></button>
            <ArrowRight size={15} aria-hidden="true" />
            <button type="button" onClick={() => onOpenArtifact('eval_missing_timepoint_block')}><span>Evaluation</span><strong>{corrected ? 'Regression passed' : 'Critical regression failed'}</strong></button>
            <ArrowRight size={15} aria-hidden="true" />
            <div><span>Serving impact</span><strong>{corrected ? 'Candidate eligible' : 'Draft agent abstains'}</strong></div>
          </div>
          <div className={styles.impactMeta}>
            <span>Owner <strong>Content Governance</strong></span>
            <span>Consumers <strong>2 agents | 1 brief</strong></span>
            <span>Policy <strong>Fail closed</strong></span>
          </div>
        </section>

        <section className={styles.toolSurface}>
          <div className={styles.surfaceHeader}><div><span className={styles.eyebrow}>Typed serving</span><h3>Agent consumers</h3></div><button type="button" className={styles.textButton} onClick={() => onNavigate('simulator')}>Simulate <ArrowRight size={14} /></button></div>
          <div className={styles.consumerTable}>
            {consumers.map(([id, operation, scope]) => (
              <div key={id}><Bot size={15} aria-hidden="true" /><span><strong>{id}</strong><small>{operation}</small></span><b>{scope}</b></div>
            ))}
          </div>
        </section>
      </div>

      <section className={styles.activityBand}>
        <div className={styles.surfaceHeader}><div><span className={styles.eyebrow}>Append-only receipts</span><h3>Recent control activity</h3></div></div>
        <div className={styles.activityList}>
          {snapshot.activity.map((item) => (
            <div key={item.id}><span className={styles.activityTime}>{item.at}</span><span><strong>{item.action}</strong><small>{item.actor} | {item.artifact}</small></span><code>{item.receipt}</code></div>
          ))}
        </div>
      </section>
    </div>
  );
}
