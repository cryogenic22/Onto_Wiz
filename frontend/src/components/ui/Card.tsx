'use client';

import { cn } from '@/lib/cn';
import { usePersona } from '@/lib/persona';

interface CardProps {
  children: React.ReactNode;
  className?: string;
}

export default function Card({ children, className }: CardProps) {
  const persona = usePersona();
  const density = persona === 'sme'
    ? 'p-[var(--persona-spacing-lg)] rounded-[var(--persona-radius)]'
    : 'p-[var(--persona-spacing-md)] rounded-[var(--persona-radius)]';

  return (
    <div className={cn('bg-slate-800/50 border border-slate-700/50', density, className)}>
      {children}
    </div>
  );
}
