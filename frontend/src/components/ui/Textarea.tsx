'use client';

import { cn } from '@/lib/cn';
import { usePersona } from '@/lib/persona';

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
}

export default function Textarea({ label, className, id, ...props }: TextareaProps) {
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
      <textarea
        id={id}
        className={cn(
          'bg-slate-800 border border-slate-600 text-slate-200 placeholder:text-slate-500 focus:border-blue-500 focus:outline-none resize-none',
          density,
          className,
        )}
        {...props}
      />
    </div>
  );
}
