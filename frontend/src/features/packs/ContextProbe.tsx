import { useState } from 'react';
import Button from '@/components/ui/Button';
import Card from '@/components/ui/Card';
import Input from '@/components/ui/Input';
import { fetchContext } from '@/services/packs';
import type { ContextResponse, PackDetail } from '@/types/packs';

/**
 * Probe a pack with a real query and show the trust envelope `POST /v1/context` returns.
 *
 * Every figure below is read straight off the response — confidence, lifecycle floor and
 * token estimate are never computed client-side (D1.0 §5a).
 */
export default function ContextProbe({ pack }: { pack: PackDetail }) {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState<ContextResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const run = async () => {
    setBusy(true);
    setError(null);
    try {
      setResult(
        await fetchContext({
          pack_name: pack.name,
          pack_version: pack.version,
          query,
        }),
      );
    } catch (e) {
      setResult(null);
      setError(e instanceof Error ? e.message : 'Probe failed.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card variant="inset" className="mt-4">
      <div className="mb-3 font-mono text-[10.5px] uppercase tracking-[1px] text-ink3">
        Context probe
      </div>

      <div className="flex flex-wrap items-end gap-2">
        <div className="min-w-[240px] flex-1">
          <Input
            id="probe-query"
            label="Probe query"
            placeholder="why did volume drop after a formulary change"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </div>
        <Button variant="primary" onClick={run} disabled={busy}>
          {busy ? 'Running…' : 'Run probe'}
        </Button>
      </div>

      {error && (
        <div data-testid="probe-error" className="mt-3 text-[12px] text-ember">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-4 space-y-3">
          <div className="flex flex-wrap gap-x-6 gap-y-2 font-mono text-[11px]">
            <span data-testid="trust-confidence" className="text-ink">
              confidence <span className="text-cyan">{result.trust.confidence}</span>
            </span>
            <span data-testid="trust-floor" className="text-ink">
              lifecycle floor{' '}
              <span className="text-cyan">{result.trust.lifecycle_floor}</span>
            </span>
            <span data-testid="tokens-estimate" className="text-ink">
              tokens ≈ <span className="text-cyan">{result.tokens_estimate}</span>
            </span>
          </div>

          <div>
            <div className="mb-1.5 font-mono text-[10px] uppercase tracking-[1px] text-ink3">
              Eligible · ranked by the engine ({result.eligible.length})
            </div>
            <div className="flex flex-wrap gap-1.5">
              {result.eligible.map((id) => (
                <span
                  key={id}
                  data-testid={`eligible-${id}`}
                  className="rounded-md border border-edge bg-slab px-1.5 py-0.5 font-mono text-[10.5px] text-ink2"
                >
                  {id}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}
