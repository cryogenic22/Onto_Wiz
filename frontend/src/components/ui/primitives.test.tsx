import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import Button from './Button';
import Card from './Card';
import Input from './Input';
import Textarea from './Textarea';
import Modal from './Modal';
import ProgressDots from './ProgressDots';

const LEGACY_PALETTE = /\b(?:slate|blue|emerald|amber|red)-\d/;

describe('Button', () => {
  it.each([
    ['primary', 'bg-cyan'],
    ['secondary', 'bg-slab'],
    ['ghost', 'text-ink2'],
    ['danger', 'text-ember'],
  ] as const)('renders the %s variant on Foundry tokens', (variant, token) => {
    render(<Button variant={variant}>Go</Button>);
    expect(screen.getByRole('button', { name: 'Go' }).className).toContain(token);
  });

  it('is keyboard-focusable (focus-visible ring) and honours disabled', () => {
    render(<Button disabled>Go</Button>);
    const btn = screen.getByRole('button', { name: 'Go' });
    expect(btn.className).toMatch(/focus-visible:ring-cyan/);
    expect(btn).toBeDisabled();
  });

  it('forwards onClick', () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Go</Button>);
    fireEvent.click(screen.getByRole('button', { name: 'Go' }));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it('leaks no legacy palette class', () => {
    render(<Button variant="danger">Go</Button>);
    expect(screen.getByRole('button', { name: 'Go' }).className).not.toMatch(LEGACY_PALETTE);
  });
});

describe('Card', () => {
  it('uses the carbon surface by default and a distinct inset surface when nested', () => {
    render(
      <Card>
        <span>outer</span>
        <Card variant="inset">inner</Card>
      </Card>,
    );
    const outer = screen.getByText('outer').closest('div');
    const inner = screen.getByText('inner');
    expect(outer?.className).toContain('bg-carbon');
    expect(inner.className).toContain('bg-slab2');
    expect(inner.className).not.toBe(outer?.className); // no nested-card regression
  });

  it('leaks no legacy palette class', () => {
    render(<Card>x</Card>);
    expect(screen.getByText('x').className).not.toMatch(LEGACY_PALETTE);
  });
});

describe('Input', () => {
  it('renders a linked label on a Foundry field', () => {
    render(<Input id="q" label="Query" />);
    const input = screen.getByLabelText('Query');
    expect(input.className).toContain('bg-slab');
    expect(input.className).not.toMatch(LEGACY_PALETTE);
  });

  it('exposes error via ARIA + text, not colour alone', () => {
    render(<Input id="q" label="Query" error="Required" />);
    const input = screen.getByLabelText('Query');
    expect(input).toHaveAttribute('aria-invalid', 'true');
    const msg = screen.getByText('Required');
    expect(input.getAttribute('aria-describedby')).toBe(msg.id);
    expect(input.className).toContain('border-ember');
  });

  it('honours disabled', () => {
    render(<Input id="q" label="Query" disabled />);
    expect(screen.getByLabelText('Query')).toBeDisabled();
  });
});

describe('Textarea', () => {
  it('renders a Foundry field and error state', () => {
    render(<Textarea id="notes" label="Notes" error="Too long" />);
    const ta = screen.getByLabelText('Notes');
    expect(ta.className).toContain('bg-slab');
    expect(ta).toHaveAttribute('aria-invalid', 'true');
    expect(ta.getAttribute('aria-describedby')).toBe(screen.getByText('Too long').id);
    expect(ta.className).not.toMatch(LEGACY_PALETTE);
  });
});

describe('Modal', () => {
  it('renders nothing when closed', () => {
    render(<Modal open={false} onClose={() => {}} title="T">body</Modal>);
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('is an accessible dialog when open', () => {
    render(<Modal open onClose={() => {}} title="Confirm">body</Modal>);
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    const labelId = dialog.getAttribute('aria-labelledby');
    expect(labelId).toBeTruthy();
    expect(document.getElementById(labelId as string)?.textContent).toBe('Confirm');
    expect(dialog.className).not.toMatch(LEGACY_PALETTE);
  });

  it('closes on Escape and on the close button', () => {
    const onClose = vi.fn();
    render(<Modal open onClose={onClose} title="T">body</Modal>);
    fireEvent.keyDown(document, { key: 'Escape' });
    fireEvent.click(screen.getByRole('button', { name: /close/i }));
    expect(onClose).toHaveBeenCalledTimes(2);
  });
});

describe('ProgressDots', () => {
  it('marks the current step and tones done/current/upcoming on Foundry tokens', () => {
    const { container } = render(
      <ProgressDots steps={['a', 'b', 'c']} currentIndex={1} />,
    );
    const dots = container.querySelectorAll('[data-slot="dot"]');
    expect(dots).toHaveLength(3);
    expect(dots[0].className).toContain('bg-jade'); // done
    expect(dots[1].className).toContain('bg-cyan'); // current
    expect(dots[1]).toHaveAttribute('aria-current', 'step');
    expect(dots[2].className).toContain('bg-edge2'); // upcoming
    dots.forEach((d) => expect(d.className).not.toMatch(LEGACY_PALETTE));
  });
});
