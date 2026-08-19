import { cn } from '@/lib/cn';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

const BASE =
  'inline-flex items-center justify-center gap-1.5 rounded-md px-3 py-1.5 text-[13px] ' +
  'font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 ' +
  'focus-visible:ring-cyan focus-visible:ring-offset-1 focus-visible:ring-offset-void ' +
  'disabled:opacity-50 disabled:pointer-events-none';

const VARIANTS: Record<ButtonVariant, string> = {
  primary: 'bg-cyan text-void hover:bg-cyan/90',
  secondary: 'border border-edge bg-slab text-ink hover:border-edge2',
  ghost: 'text-ink2 hover:bg-slab hover:text-ink',
  danger: 'border border-ember/40 bg-ember-soft text-ember hover:bg-ember/20',
};

export default function Button({ variant = 'primary', className, ...props }: ButtonProps) {
  return <button className={cn(BASE, VARIANTS[variant] ?? VARIANTS.primary, className)} {...props} />;
}
