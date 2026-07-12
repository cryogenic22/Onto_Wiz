import { cn } from '@/lib/cn';

interface ProgressDotsProps {
  steps: string[];
  currentIndex: number;
  className?: string;
}

export default function ProgressDots({ steps, currentIndex, className }: ProgressDotsProps) {
  return (
    <div className={cn('flex items-center gap-1', className)} role="list" aria-label="Progress">
      {steps.map((step, i) => (
        <div
          key={step}
          data-slot="dot"
          role="listitem"
          aria-current={i === currentIndex ? 'step' : undefined}
          className={cn(
            'h-2 w-2 rounded-full transition-colors',
            i < currentIndex ? 'bg-jade' : i === currentIndex ? 'bg-cyan' : 'bg-edge2',
          )}
          title={step}
        />
      ))}
    </div>
  );
}
