'use client';

import { cn } from '@/lib/cn';
import { usePersona } from '@/lib/persona';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export default function Input({ label, className, id, ...props }: InputProps) {
  const persona = usePersona();
  const density = persona === 'sme'
    ? 'px-4 py-2.5 text-[length:var(--persona-font-base)] rounded-[var(--persona-radius)]'
    : 'px-3 py-1.5 text-[length:var(--persona-font-sm)] rounded-[var(--persona-radius)]';

  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label htmlFor={id} className="text-[length:var(--persona-font-sm)] text-slate-400">
          {label}
        </label>
      )}
      <input
        id={id}
        className={cn(
          'bg-slate-800 border border-slate-600 text-slate-200 placeholder:text-slate-500 focus:border-blue-500 focus:outline-none',
          density,
          className,
        )}
        {...props}
      />
    </div>
  );
}
