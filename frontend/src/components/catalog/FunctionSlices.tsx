import { cn } from '@/lib/cn';
import type { FunctionSlice } from '@/types/catalog';

interface Props {
  slices: FunctionSlice[];
  total: number;
  active: string;
  onSelect: (fn: string) => void;
}

function Chip({ label, on, onClick }: { label: string; on: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      aria-pressed={on}
      onClick={onClick}
      className={cn(
        'mr-1.5 mb-1.5 rounded-lg border border-slate-700 px-3 py-1.5 text-sm',
        on ? 'bg-slate-800 text-slate-100' : 'text-slate-300',
      )}
    >
      {label}
    </button>
  );
}

/** Function-slice selector — picks "all" or a single function, with the
 * slice-vs-full token leanness note that is the offline functionalization payoff. */
export default function FunctionSlices({ slices, total, active, onSelect }: Props) {
  const current = slices.find((s) => s.function === active);
  return (
    <div>
      <Chip label={`Full pack · ${total}`} on={active === 'all'} onClick={() => onSelect('all')} />
      {slices.map((s) => (
        <Chip
          key={s.function}
          label={`${s.function} · ${s.count}`}
          on={active === s.function}
          onClick={() => onSelect(s.function)}
        />
      ))}
      {current && (
        <p className="mt-2 text-xs text-slate-500">
          Serving this slice ≈ {current.slice_tokens} tokens vs {current.full_tokens} for the full pack.
        </p>
      )}
    </div>
  );
}
