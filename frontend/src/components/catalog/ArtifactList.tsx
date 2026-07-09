import { cn } from '@/lib/cn';
import type { ArtifactRow } from '@/types/catalog';

interface Props {
  rows: ArtifactRow[];
  onOpen: (id: string) => void;
}

/** The artifact rows for a pack (or active slice); a pill flags served vs gated. */
export default function ArtifactList({ rows, onOpen }: Props) {
  if (rows.length === 0) {
    return <p className="text-sm text-slate-500">No artifacts in this slice.</p>;
  }
  return (
    <ul className="space-y-2">
      {rows.map((r) => (
        <li key={r.id}>
          <button
            type="button"
            onClick={() => onOpen(r.id)}
            data-testid={`artifact-${r.id}`}
            className="flex w-full items-center gap-2 rounded-lg border border-slate-800 bg-slate-950 p-3 text-left hover:border-slate-600"
          >
            <span>
              <b className="text-slate-100">{r.name}</b>
              <span className="block text-xs text-slate-500">{r.id} · {r.kind}</span>
            </span>
            <span
              className={cn(
                'ml-auto rounded-full border px-2 py-0.5 text-[11px]',
                r.served ? 'border-emerald-600/40 text-emerald-400' : 'border-slate-700 text-slate-500',
              )}
            >
              {r.served ? 'served' : 'gated'}
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}
