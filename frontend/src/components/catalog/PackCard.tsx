import { cn } from '@/lib/cn';
import type { CatalogEntry } from '@/types/catalog';

interface Props {
  entry: CatalogEntry;
  onOpen: (entry: CatalogEntry) => void;
}

/** One pack tile in the catalog grid. */
export default function PackCard({ entry, onOpen }: Props) {
  return (
    <button
      type="button"
      onClick={() => onOpen(entry)}
      data-testid={`pack-${entry.name}`}
      className={cn(
        'text-left rounded-2xl border border-slate-800 bg-slate-900/60 p-4',
        'transition hover:-translate-y-0.5 hover:border-slate-600',
      )}
    >
      <div className="text-xs font-semibold text-teal-400">{entry.domain}</div>
      <h3 className="my-1 text-lg font-semibold text-slate-100">
        {entry.name} <span className="text-slate-500">v{entry.latest_version}</span>
      </h3>
      <p className="min-h-[34px] text-sm text-slate-400">{entry.description}</p>
      <div className="mt-3 flex flex-wrap gap-1.5">
        {Object.entries(entry.functions).map(([fn, count]) => (
          <span key={fn} className="rounded-full border border-slate-700 px-2 py-0.5 text-[11px] text-slate-300">
            {fn} · {count}
          </span>
        ))}
      </div>
      <div className="mt-3 flex gap-3 text-xs text-slate-400">
        <span><b className="text-slate-200">{entry.artifact_count}</b> artifacts</span>
        {entry.agent_lift != null && <span>lift <b className="text-slate-200">+{entry.agent_lift}</b></span>}
        {entry.signed && <span className="text-emerald-400">● sealed</span>}
      </div>
    </button>
  );
}
