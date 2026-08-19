import { cn } from '@/lib/cn';

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  /** When set, shows the message and marks the field invalid (colour + text + ARIA). */
  error?: string;
}

const FIELD =
  'resize-y rounded-md border bg-slab px-3 py-1.5 text-[13px] text-ink placeholder:text-ink3 ' +
  'focus-visible:outline-none disabled:opacity-50 disabled:cursor-not-allowed';

export default function Textarea({ label, error, className, id, ...props }: TextareaProps) {
  const errorId = error && id ? `${id}-error` : undefined;
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label htmlFor={id} className="text-[11px] text-ink2">
          {label}
        </label>
      )}
      <textarea
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={errorId}
        className={cn(
          FIELD,
          error ? 'border-ember focus-visible:ring-1 focus-visible:ring-ember/40'
                : 'border-edge focus-visible:border-cyan focus-visible:ring-1 focus-visible:ring-cyan/40',
          className,
        )}
        {...props}
      />
      {error && (
        <span id={errorId} className="text-[11px] text-ember">
          {error}
        </span>
      )}
    </div>
  );
}
