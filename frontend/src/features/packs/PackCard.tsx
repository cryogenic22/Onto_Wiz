import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import { hasEvalEvidence, type PackSummary } from '@/types/packs';

/**
 * One compiled pack, with its trust signals rendered honestly (D1.0 §5a/§5b).
 *
 * The load-bearing rule: every number here is a field the API returned. When a pack has
 * no eval evidence we say so explicitly — we do not fall back to a zero, a blank, or a
 * neighbouring version's headline lift.
 */
export default function PackCard({
  pack,
  selected,
  onInspect,
}: {
  pack: PackSummary;
  selected: boolean;
  onInspect: (pack: PackSummary) => void;
}) {
  const { evals } = pack;
  const evidenced = hasEvalEvidence(evals);

  // The testid lives on a wrapper rather than on <Card>: Card's reviewed D0.4 API takes
  // only {variant, children, className}, and a consumer must not widen a submitted unit.
  return (
    <div data-testid={`pack-card-${pack.name}@${pack.version}`}>
      <Card className={selected ? 'border-cyan/50' : undefined}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="font-display text-[15px] font-semibold text-ink">
            {pack.name}
          </div>
          <div className="mt-0.5 font-mono text-[11px] text-cyan">{pack.version}</div>
        </div>
        <span
          data-testid="seal-state"
          className="shrink-0 rounded-md border border-edge px-1.5 py-0.5 font-mono text-[10px] text-ink3"
          title="SHA-256 integrity seal — integrity, not PKI authorship"
        >
          {pack.signed ? 'sealed' : 'unsealed'}
        </span>
      </div>

      <p className="mt-2 line-clamp-2 text-[12.5px] text-ink2">{pack.description}</p>

      <div className="mt-3 font-mono text-[11px] text-ink3">
        {pack.artifact_count} artifacts
      </div>

      {/* ── evidence ─────────────────────────────────────────────── */}
      <div className="mt-3 border-t border-edge pt-3">
        {evidenced ? (
          <div data-testid="eval-evidence" className="font-mono text-[11px] text-jade">
            lift +{evals.agent_lift ?? '—'} · {Math.round(evals.pass_rate * 100)}% pass ·{' '}
            {evals.eval_cases} cases
          </div>
        ) : (
          <div
            data-testid="no-eval-evidence"
            className="font-mono text-[11px] text-molten"
            title="This pack has never been benchmarked — no eval cases were run against it."
          >
            no eval evidence
          </div>
        )}

        <div
          data-testid="gate-state"
          className={
            evals.gate_passed
              ? 'mt-1 font-mono text-[10.5px] text-jade'
              : 'mt-1 font-mono text-[10.5px] text-ink3'
          }
        >
          gate {evals.gate_passed ? 'passed' : 'not passed'}
        </div>
      </div>

      <div className="mt-3">
        <Button variant="secondary" onClick={() => onInspect(pack)}>
          Inspect
        </Button>
      </div>
      </Card>
    </div>
  );
}
