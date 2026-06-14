'use client';

import { cn } from '@/lib/cn';
import { usePersona } from '@/lib/persona';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

const BASE = 'inline-flex items-center justify-center font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-400/50 disabled:opacity-50 disabled:pointer-events-none';

const VARIANTS: Record<ButtonVariant, string> = {
  primary: 'bg-blue-600 text-white hover:bg-blue-500',
  secondary: 'bg-slate-700 text-slate-200 hover:bg-slate-600',
  ghost: 'text-slate-400 hover:text-slate-200 hover:bg-slate-800',
  danger: 'bg-red-600/20 text-red-400 hover:bg-red-600/30',
};

export default function Button({ variant = 'primary', className, ...props }: ButtonProps) {
  const persona = usePersona();
  const density = persona === 'sme'
    ? 'px-5 py-2.5 text-[length:var(--persona-font-base)] rounded-[var(--persona-radius)]'
    : 'px-3 py-1.5 text-[length:var(--persona-font-sm)] rounded-[var(--persona-radius)]';

  return (
    <button className={cn(BASE, VARIANTS[variant], density, className)} {...props} />
  );
}
