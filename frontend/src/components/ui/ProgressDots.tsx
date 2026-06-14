import { cn } from '@/lib/cn';

interface ProgressDotsProps {
  steps: string[];
  currentIndex: number;
  className?: string;
}

export default function ProgressDots({ steps, currentIndex, className }: ProgressDotsProps) {
  return (
    <div className={cn('flex items-center gap-1', className)}>
      {steps.map((step, i) => (
        <div
          key={step}
          className={cn(
            'w-2 h-2 rounded-full transition-colors',
            i < currentIndex ? 'bg-emerald-500' : i === currentIndex ? 'bg-blue-400' : 'bg-slate-700',
          )}
          title={step}
        />
      ))}
    </div>
  );
}
