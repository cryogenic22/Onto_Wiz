import { cn } from '@/lib/cn';

interface CardProps {
  /** `inset` uses a lighter surface so a nested Card reads as nested, not doubled. */
  variant?: 'default' | 'inset';
  children: React.ReactNode;
  className?: string;
}

const SURFACES = {
  default: 'bg-carbon border-edge',
  inset: 'bg-slab2 border-edge',
} as const;

export default function Card({ variant = 'default', children, className }: CardProps) {
  return (
    <div className={cn('rounded-lg border p-4', SURFACES[variant] ?? SURFACES.default, className)}>
      {children}
    </div>
  );
}
