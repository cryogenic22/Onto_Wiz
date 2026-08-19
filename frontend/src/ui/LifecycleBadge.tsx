import type { LucideIcon } from 'lucide-react';
import {
  Archive,
  Ban,
  Check,
  CircleCheck,
  Eye,
  FileText,
  GitMerge,
  GitPullRequest,
  ShieldCheck,
  TriangleAlert,
  X,
} from 'lucide-react';
import { cn } from '@/lib/cn';

/**
 * The true governance/gate states, sourced (not invented) from:
 *   ontowiz_spec.Lifecycle  — draft·review·verified·active·deprecated·archived
 *   ontowiz_core.DeltaStatus — proposed·approved·rejected·merged
 *   gate outcomes (Prototype 9 .b.pass/fail/warn) — pass·fail·warn
 */
export const LIFECYCLE_STATES = [
  'draft',
  'review',
  'verified',
  'active',
  'deprecated',
  'archived',
  'proposed',
  'approved',
  'rejected',
  'merged',
  'pass',
  'fail',
  'warn',
] as const;

export type LifecycleState = (typeof LIFECYCLE_STATES)[number];

interface StateSpec {
  label: string;
  Icon: LucideIcon;
  /** Foundry-token tone classes (bg-soft / text / border) — see tokens.css. */
  tone: string;
}

const NEUTRAL = 'bg-ink3/10 text-ink3 border-edge';

const SPECS: Record<LifecycleState, StateSpec> = {
  // Artifact lifecycle (ontowiz_spec.Lifecycle)
  draft: { label: 'DRAFT', Icon: FileText, tone: NEUTRAL },
  review: { label: 'REVIEW', Icon: Eye, tone: 'bg-info-soft text-info border-info/30' },
  verified: { label: 'VERIFIED', Icon: ShieldCheck, tone: 'bg-cyan-soft text-cyan border-cyan/30' },
  active: { label: 'ACTIVE', Icon: CircleCheck, tone: 'bg-jade-soft text-jade border-jade/30' },
  deprecated: { label: 'DEPRECATED', Icon: Ban, tone: NEUTRAL },
  archived: { label: 'ARCHIVED', Icon: Archive, tone: NEUTRAL },
  // Delta status (ontowiz_core.DeltaStatus)
  proposed: { label: 'PROPOSED', Icon: GitPullRequest, tone: 'bg-info-soft text-info border-info/30' },
  approved: { label: 'APPROVED', Icon: Check, tone: 'bg-jade-soft text-jade border-jade/30' },
  rejected: { label: 'REJECTED', Icon: X, tone: 'bg-ember-soft text-ember border-ember/30' },
  merged: { label: 'MERGED', Icon: GitMerge, tone: 'bg-iris-soft text-iris border-iris/30' },
  // Gate outcomes
  pass: { label: 'PASS', Icon: CircleCheck, tone: 'bg-jade-soft text-jade border-jade/30' },
  fail: { label: 'FAIL', Icon: X, tone: 'bg-ember-soft text-ember border-ember/30' },
  warn: { label: 'WARN', Icon: TriangleAlert, tone: 'bg-molten-soft text-molten border-molten/30' },
};

export interface LifecycleBadgeProps {
  state: LifecycleState;
  /** Override the default text (e.g. "CANDIDATE"/"ratified") — tone + icon stay fixed. */
  label?: string;
  className?: string;
}

/**
 * A governance/gate state as an icon + text label on foundry tokens. The colour is
 * never the sole signal (icon + label carry the state) — WCAG 2.2 AA. Presentational
 * only: reads state, drives no transition (Tier-A read-only; R1 untouched).
 */
export function LifecycleBadge({ state, label, className }: LifecycleBadgeProps) {
  const spec = SPECS[state] ?? { label: state, Icon: FileText, tone: NEUTRAL };
  const { Icon } = spec;
  return (
    <span
      data-testid={`lifecycle-badge-${state}`}
      data-state={state}
      className={cn(
        'inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 font-mono text-[10.5px] font-semibold tracking-[0.3px]',
        spec.tone,
        className,
      )}
    >
      <Icon aria-hidden="true" size={12} strokeWidth={2.5} className="shrink-0" />
      {label ?? spec.label}
    </span>
  );
}
