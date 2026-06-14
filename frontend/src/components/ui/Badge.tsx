import { cn } from '@/lib/cn';

type BadgeStatus = 'draft' | 'proposed' | 'approved' | 'rejected' | 'merged' | 'deprecated';

interface BadgeProps {
  status: BadgeStatus;
  className?: string;
}

const STATUS_STYLES: Record<BadgeStatus, string> = {
  draft: 'bg-slate-600/30 text-slate-400 border-slate-600',
  proposed: 'bg-amber-600/20 text-amber-400 border-amber-600/40',
  approved: 'bg-emerald-600/20 text-emerald-400 border-emerald-600/40',
  rejected: 'bg-red-600/20 text-red-400 border-red-600/40',
  merged: 'bg-blue-600/20 text-blue-400 border-blue-600/40',
  deprecated: 'bg-slate-600/20 text-slate-500 border-slate-600/30',
};

export default function Badge({ status, className }: BadgeProps) {
  return (
    <span className={cn('inline-flex items-center px-2 py-0.5 text-xs font-medium border rounded-full', STATUS_STYLES[status], className)}>
      {status}
    </span>
  );
}
