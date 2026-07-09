import type { CatalogEntry } from '@/types/catalog';

import PackCard from './PackCard';

interface Props {
  entries: CatalogEntry[];
  onOpen: (entry: CatalogEntry) => void;
}

/** The catalog grid (or an empty state when nothing matches the search). */
export default function CatalogGrid({ entries, onOpen }: Props) {
  if (entries.length === 0) {
    return <p className="text-sm text-slate-500">No packs match.</p>;
  }
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
      {entries.map((entry) => (
        <PackCard key={entry.name} entry={entry} onOpen={onOpen} />
      ))}
    </div>
  );
}
