import type { ReactNode } from 'react';

import styles from '../control-plane.module.css';

type Tone = 'good' | 'warning' | 'danger' | 'info' | 'neutral' | 'iris';

const toneByStatus: Record<string, Tone> = {
  released: 'good',
  current: 'good',
  passed: 'good',
  healthy: 'good',
  candidate: 'info',
  building: 'info',
  at_risk: 'warning',
  review_required: 'warning',
  blocked_pending_review: 'danger',
  stale: 'danger',
  failed: 'danger',
  rejected: 'danger',
  superseded: 'neutral',
  quarantined: 'iris',
};

export const humanize = (value: string) => value
  .replaceAll('_', ' ')
  .replace(/\b\w/g, (letter) => letter.toUpperCase());

export function StatusPill({ status, label }: { status: string; label?: string }) {
  const tone = toneByStatus[status] ?? 'neutral';
  return <span className={`${styles.statusPill} ${styles[`tone_${tone}`]}`}>{label ?? humanize(status)}</span>;
}

export function SectionTitle({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className={styles.sectionTitle}>
      <div>
        {eyebrow && <span className={styles.eyebrow}>{eyebrow}</span>}
        <h2>{title}</h2>
        {description && <p>{description}</p>}
      </div>
      {action && <div className={styles.sectionAction}>{action}</div>}
    </div>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return <div className={styles.emptyState}>{children}</div>;
}
