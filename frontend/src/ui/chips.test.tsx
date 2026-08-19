import { render, screen, within } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import {
  AttributionChip,
  LayerChip,
  ONTOLOGY_LAYERS,
  PROVENANCE_SOURCES,
  ProvenanceChip,
  type OntologyLayer,
  type ProvenanceSource,
} from './chips';

describe('LayerChip', () => {
  it('represents exactly the sourced ontology layers L1–L5 (no invented layers)', () => {
    expect([...ONTOLOGY_LAYERS]).toEqual(['L1', 'L2', 'L3', 'L4', 'L5']);
  });

  it.each([...ONTOLOGY_LAYERS])('renders %s with a visible default label', (layer) => {
    render(<LayerChip layer={layer} />);
    const chip = screen.getByTestId(`layer-chip-${layer}`);
    // label leads with the layer id and carries a noun — text, not colour
    expect(chip.textContent).toMatch(new RegExp(`^${layer}\\b`));
    expect(chip.textContent?.trim().length ?? 0).toBeGreaterThan(layer.length);
  });

  it('gives every layer a distinct label (meaning never rides on colour alone)', () => {
    const labels = [...ONTOLOGY_LAYERS].map((l) => {
      const view = render(<LayerChip layer={l} />);
      const text = view.getByTestId(`layer-chip-${l}`).textContent?.trim();
      view.unmount();
      return text;
    });
    expect(new Set(labels).size).toBe(ONTOLOGY_LAYERS.length);
  });

  it('lets a caller override the label while keeping the layer', () => {
    render(<LayerChip layer="L1" label="L1 · Entities" />);
    const chip = screen.getByTestId('layer-chip-L1');
    expect(within(chip).getByText('L1 · Entities')).toBeInTheDocument();
    expect(chip).toHaveAttribute('data-layer', 'L1');
  });

  it('falls back for an out-of-union layer without throwing (defensive, §9)', () => {
    render(<LayerChip layer={'L9' as OntologyLayer} />);
    expect(screen.getByTestId('layer-chip-L9')).toHaveTextContent('L9');
  });
});

describe('AttributionChip', () => {
  it('renders the name as text and a decorative avatar with derived initials', () => {
    render(<AttributionChip name="R. Mehta" />);
    const chip = screen.getByTestId('attribution-chip');
    expect(within(chip).getByText('R. Mehta')).toBeInTheDocument();
    const avatar = chip.querySelector('[data-slot="avatar"]');
    expect(avatar).not.toBeNull();
    expect(avatar).toHaveAttribute('aria-hidden', 'true');
    expect(avatar?.textContent).toBe('RM');
  });

  it('derives initials from a single-token name', () => {
    render(<AttributionChip name="Cher" />);
    expect(
      screen.getByTestId('attribution-chip').querySelector('[data-slot="avatar"]')?.textContent,
    ).toBe('CH');
  });

  it('falls back to the raw string when a name has no letters', () => {
    render(<AttributionChip name="42" />);
    expect(
      screen.getByTestId('attribution-chip').querySelector('[data-slot="avatar"]')?.textContent,
    ).toBe('42');
  });

  it('accepts explicit initials', () => {
    render(<AttributionChip name="Priya Kapoor" initials="PK" />);
    expect(screen.getByTestId('attribution-chip').querySelector('[data-slot="avatar"]')?.textContent).toBe(
      'PK',
    );
  });

  it('renders a decorative validated ✓ and the calibration score (icon + text, not colour-only)', () => {
    render(<AttributionChip name="R. Mehta" validated calibration={0.9} />);
    const chip = screen.getByTestId('attribution-chip');
    const check = chip.querySelector('svg');
    expect(check).not.toBeNull();
    expect(check).toHaveAttribute('aria-hidden', 'true');
    expect(chip).toHaveTextContent('0.9');
  });

  it('changes only the avatar tone, never dropping the name (colour never sole signal)', () => {
    render(<AttributionChip name="K. Bose" tone="jade" />);
    const chip = screen.getByTestId('attribution-chip');
    expect(within(chip).getByText('K. Bose')).toBeInTheDocument();
  });

  it('renders a keyboard-accessible native link when href is given', () => {
    render(<AttributionChip name="A. Shah" href="/people/ashah" />);
    const link = screen.getByRole('link', { name: /A\. Shah/ });
    expect(link.tagName).toBe('A');
    expect(link).toHaveAttribute('href', '/people/ashah');
  });
});

describe('ProvenanceChip', () => {
  it('represents exactly the sourced provenance source set', () => {
    expect([...PROVENANCE_SOURCES]).toEqual([
      'transcript',
      'deck',
      'doc',
      'session',
      'forge',
      'studio',
      'intake',
      'eval',
    ]);
  });

  it.each([...PROVENANCE_SOURCES])(
    'renders %s with a decorative source icon and the locator text',
    (source) => {
      render(<ProvenanceChip source={source} locator="ref-1" />);
      const chip = screen.getByTestId(`provenance-chip-${source}`);
      const icon = chip.querySelector('svg');
      expect(icon).not.toBeNull();
      expect(icon).toHaveAttribute('aria-hidden', 'true');
      expect(chip).toHaveTextContent('ref-1');
    },
  );

  it('keeps a long locator responsive: truncates and exposes the full text via title', () => {
    const locator = '00:12:04–00:12:31 · R. Mehta, A. Shah, K. Bose · weak evidence';
    render(<ProvenanceChip source="transcript" locator={locator} />);
    const value = screen.getByTestId('provenance-chip-transcript').querySelector('[data-slot="locator"]');
    expect(value).not.toBeNull();
    expect(value?.className).toMatch(/truncate/);
    expect(value).toHaveAttribute('title', locator);
  });

  it('renders a keyboard-accessible native deep-link when href is given', () => {
    render(<ProvenanceChip source="deck" locator="slide 23" href="/src/deck#23" />);
    const link = screen.getByRole('link', { name: /slide 23/ });
    expect(link.tagName).toBe('A');
    expect(link).toHaveAttribute('href', '/src/deck#23');
  });

  it('renders a plain span (no link role) when href is absent', () => {
    render(<ProvenanceChip source="doc" locator="§3.2" />);
    expect(screen.queryByRole('link')).toBeNull();
  });

  it('shows the unvalidated warning tone with a warning icon and still the locator text', () => {
    render(<ProvenanceChip source="doc" locator="Claude-drafted" unvalidated />);
    const chip = screen.getByTestId('provenance-chip-doc');
    expect(chip).toHaveAttribute('data-unvalidated', 'true');
    expect(chip.querySelector('svg')).not.toBeNull();
    expect(chip).toHaveTextContent('Claude-drafted');
  });

  it('falls back for an out-of-union source without throwing (defensive, §9)', () => {
    render(<ProvenanceChip source={'bogus' as ProvenanceSource} locator="x" />);
    expect(screen.getByTestId('provenance-chip-bogus')).toHaveTextContent('x');
  });
});
