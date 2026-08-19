'use client';

import { useCallback, useEffect, useState } from 'react';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import {
  LIFECYCLE_STATES,
  LifecycleBadge,
  type LifecycleState,
} from '@/ui/LifecycleBadge';
import { fetchPackDetail, fetchPacks } from '@/services/packs';
import type { PackDetail, PackSummary } from '@/types/packs';
import ContextProbe from './ContextProbe';
import PackCard from './PackCard';

/** The API types `lifecycle` as a free string; only render a badge for a state we know. */
function asLifecycleState(value: string): LifecycleState | null {
  return (LIFECYCLE_STATES as readonly string[]).includes(value)
    ? (value as LifecycleState)
    : null;
}

function message(e: unknown, fallback: string): string {
  return e instanceof Error ? e.message : fallback;
}

/**
 * D1.0 — the vertical slice: real `ontowiz-serve` data rendered entirely in D0 Foundry
 * components. Read-only (§5f). Loading / error / empty are explicit states, never a
 * silently empty list (§5, §9).
 */
export default function PackExplorer() {
  const [packs, setPacks] = useState<PackSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [detail, setDetail] = useState<PackDetail | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);

  const [reloadKey, setReloadKey] = useState(0);

  // Canonical effect-fetch: state is only written from the promise callbacks (never
  // synchronously in the effect body), and `cancelled` drops a late response so an
  // unmount or a rapid retry cannot write stale packs over fresh ones.
  useEffect(() => {
    let cancelled = false;
    fetchPacks()
      .then((rows) => {
        if (cancelled) return;
        setPacks(rows);
        setError(null);
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        setPacks(null);
        setError(message(e, 'Could not reach the pack registry.'));
      });
    return () => {
      cancelled = true;
    };
  }, [reloadKey]);

  /** Retry is an event handler, so resetting to the loading state here is safe. */
  const retry = useCallback(() => {
    setError(null);
    setPacks(null);
    setReloadKey((k) => k + 1);
  }, []);

  const inspect = useCallback(async (pack: PackSummary) => {
    setDetailError(null);
    setDetail(null);
    try {
      setDetail(await fetchPackDetail(pack.name, pack.version));
    } catch (e) {
      setDetailError(message(e, 'Could not load pack detail.'));
    }
  }, []);

  return (
    <main className="min-h-screen bg-void px-8 py-10 text-ink">
      <header className="mb-8">
        <div className="mb-2 font-mono text-[11px] uppercase tracking-[1px] text-cyan">
          Onto_Wiz Foundry
        </div>
        <h1 className="font-display text-[26px] font-semibold tracking-[-0.5px]">
          Pack Explorer
        </h1>
        <p className="mt-1 max-w-[70ch] text-[14px] text-ink2">
          Live data from <code className="font-mono text-[12.5px] text-ink3">ontowiz-serve</code>.
          Trust figures are shown exactly as the engine reports them — including where the
          evidence is missing.
        </p>
      </header>

      {error && (
        <Card>
          <div data-testid="packs-error" className="text-[13px] text-ember">
            {error}
          </div>
          <p className="mt-1 text-[12px] text-ink3">
            Is the backend running on the configured base URL?
          </p>
          <div className="mt-3">
            <Button variant="secondary" onClick={retry}>
              Retry
            </Button>
          </div>
        </Card>
      )}

      {!error && packs === null && (
        <div data-testid="packs-loading" className="font-mono text-[12px] text-ink3">
          Loading packs…
        </div>
      )}

      {!error && packs?.length === 0 && (
        <Card>
          <div data-testid="packs-empty" className="text-[13px] text-ink2">
            The registry served zero compiled packs.
          </div>
        </Card>
      )}

      {!error && packs && packs.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {packs.map((pack) => (
            <PackCard
              key={`${pack.name}@${pack.version}`}
              pack={pack}
              selected={
                detail?.name === pack.name && detail?.version === pack.version
              }
              onInspect={inspect}
            />
          ))}
        </div>
      )}

      {detailError && (
        <div className="mt-6">
          <Card>
            <div data-testid="detail-error" className="text-[13px] text-ember">
              {detailError}
            </div>
          </Card>
        </div>
      )}

      {detail && (
        <section className="mt-8">
          <h2 className="mb-1 font-display text-[18px] font-semibold">
            {detail.name}{' '}
            <span className="font-mono text-[13px] text-cyan">{detail.version}</span>
          </h2>
          <div
            data-testid="detail-gaps"
            className="mb-4 font-mono text-[11px] text-molten"
            title="Artifacts the pack serves but has no eval case for — the engine's own coverage gap list."
          >
            {detail.gaps.length} served-but-untested artifacts
          </div>

          <div className="space-y-2">
            {detail.artifacts.map((a) => {
              const state = asLifecycleState(a.lifecycle);
              return (
                <div
                  key={a.id}
                  data-testid={`artifact-row-${a.id}`}
                  className="flex flex-wrap items-center gap-x-3 gap-y-1.5 rounded-md border border-edge bg-carbon px-3 py-2"
                >
                  {state ? (
                    <LifecycleBadge state={state} />
                  ) : (
                    <span className="font-mono text-[10.5px] text-ink3">
                      {a.lifecycle}
                    </span>
                  )}
                  <span className="text-[13px] text-ink">{a.name}</span>
                  <span className="font-mono text-[11px] text-ink3">{a.kind}</span>
                  <span className="font-mono text-[11px] text-ink3">
                    conf {a.confidence}
                  </span>

                  {a.has_eval ? (
                    <span
                      data-testid="artifact-tested"
                      className="font-mono text-[10.5px] text-jade"
                    >
                      eval covered
                    </span>
                  ) : (
                    <span
                      data-testid="artifact-untested"
                      className="font-mono text-[10.5px] text-molten"
                    >
                      untested
                    </span>
                  )}

                  {/* The detail endpoint carries no provenance field, so we say exactly
                      that rather than emitting a chip we have no source for (§5d). */}
                  <span
                    data-testid="provenance-none"
                    className="font-mono text-[10.5px] text-ink3"
                  >
                    no provenance recorded
                  </span>
                </div>
              );
            })}
          </div>

          <ContextProbe pack={detail} />
        </section>
      )}
    </main>
  );
}
