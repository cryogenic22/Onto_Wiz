import type { LucideIcon } from 'lucide-react';
import {
  Aperture,
  Check,
  FileText,
  FlaskConical,
  Hammer,
  Mic,
  Pickaxe,
  Presentation,
  Target,
  TriangleAlert,
} from 'lucide-react';
import { cn } from '@/lib/cn';

/**
 * Foundry chips — attribution / provenance / layer. Presentational only: they carry
 * "provenance on every object" (Prototype 9's north-star) as icon + text on foundry
 * tokens. Colour is never the sole signal — the identifying text (name / locator /
 * layer label) is always rendered; avatars and icons are decorative (`aria-hidden`).
 * They read state and drive no transition (Tier-A read-only; R1 untouched).
 *
 * Taxonomies are sourced from Prototype 9 + the ontology-layer model, not invented.
 */

/** L1 entity · L2 relation · L3 rule · L4 metric · L5 scenario. */
export const ONTOLOGY_LAYERS = ['L1', 'L2', 'L3', 'L4', 'L5'] as const;
export type OntologyLayer = (typeof ONTOLOGY_LAYERS)[number];

/** The `.chip.src` glyph set actually used in Prototype 9. */
export const PROVENANCE_SOURCES = [
  'transcript',
  'deck',
  'doc',
  'session',
  'forge',
  'studio',
  'intake',
  'eval',
] as const;
export type ProvenanceSource = (typeof PROVENANCE_SOURCES)[number];

type AvatarTone = 'cyan' | 'info' | 'iris' | 'jade';

// ── shared link/span polymorphism ──────────────────────────────────────────────
// A chip with an href is a real, keyboard-focusable <a>; otherwise an inert <span>.
const LINK_CLASSES =
  'no-underline transition-colors hover:border-edge2 focus-visible:outline-none ' +
  'focus-visible:ring-2 focus-visible:ring-cyan focus-visible:ring-offset-1 ' +
  'focus-visible:ring-offset-void';

function chipTag(href: string | undefined) {
  return {
    Tag: (href ? 'a' : 'span') as 'a' | 'span',
    linkProps: href ? { href } : {},
    linkClass: href ? LINK_CLASSES : undefined,
  };
}

// ── LayerChip ───────────────────────────────────────────────────────────────────
const LAYER_NOUNS: Record<OntologyLayer, string> = {
  L1: 'entity',
  L2: 'relation',
  L3: 'rule',
  L4: 'metric',
  L5: 'scenario',
};
// Faithful to Prototype 9: only .tag.l1 (cyan) and .tag.l3 (molten) are toned;
// L2/L4/L5 use the neutral .tag tone. The label always carries the meaning.
const LAYER_TONES: Record<OntologyLayer, string> = {
  L1: 'border-cyan/30 text-cyan',
  L2: 'border-edge text-ink2',
  L3: 'border-molten/30 text-molten',
  L4: 'border-edge text-ink2',
  L5: 'border-edge text-ink2',
};

export interface LayerChipProps {
  layer: OntologyLayer;
  /** Override the default text (e.g. "L1 · Entities"); layer + tone stay fixed. */
  label?: string;
  className?: string;
}

export function LayerChip({ layer, label, className }: LayerChipProps) {
  const noun = LAYER_NOUNS[layer];
  const tone = LAYER_TONES[layer] ?? 'border-edge text-ink2';
  const text = label ?? (noun ? `${layer} ${noun}` : layer);
  return (
    <span
      data-testid={`layer-chip-${layer}`}
      data-layer={layer}
      className={cn(
        'inline-flex items-center rounded-sm border bg-slab px-[7px] py-0.5 font-mono text-[11px] font-medium',
        tone,
        className,
      )}
    >
      {text}
    </span>
  );
}

// ── AttributionChip ───────────────────────────────────────────────────────────────
const AVATAR_TONES: Record<AvatarTone, string> = {
  cyan: 'bg-cyan',
  info: 'bg-info',
  iris: 'bg-iris',
  jade: 'bg-jade',
};

function deriveInitials(name: string): string {
  const parts = name
    .split(/\s+/)
    .map((p) => p.replace(/[^A-Za-z]/g, ''))
    .filter(Boolean);
  if (parts.length === 0) return name.slice(0, 2).toUpperCase();
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

export interface AttributionChipProps {
  /** The person; always rendered as text (colour is never the sole signal). */
  name: string;
  /** Avatar initials; derived from `name` when omitted. */
  initials?: string;
  /** Avatar background only; the name text is unaffected. */
  tone?: AvatarTone;
  /** Trailing decorative ✓ — a validated-by marker. */
  validated?: boolean;
  /** Trailing calibration score, e.g. 0.9 → "· 0.9". */
  calibration?: number;
  /** Optional link → renders a keyboard-focusable native `<a>`. */
  href?: string;
  className?: string;
}

export function AttributionChip({
  name,
  initials,
  tone = 'cyan',
  validated,
  calibration,
  href,
  className,
}: AttributionChipProps) {
  const { Tag, linkProps, linkClass } = chipTag(href);
  return (
    <Tag
      {...linkProps}
      data-testid="attribution-chip"
      className={cn(
        'inline-flex max-w-full min-w-0 items-center gap-1.5 rounded-pill border border-edge bg-slab py-0.5 pl-[3px] pr-2.5 text-[11.5px] text-ink2',
        linkClass,
        className,
      )}
    >
      <span
        data-slot="avatar"
        aria-hidden="true"
        className={cn(
          'flex h-[17px] w-[17px] shrink-0 items-center justify-center rounded-full font-display text-[8.5px] font-bold text-void',
          AVATAR_TONES[tone],
        )}
      >
        {initials ?? deriveInitials(name)}
      </span>
      <span data-slot="name" title={name} className="min-w-0 truncate">
        {name}
      </span>
      {validated ? (
        <Check aria-hidden="true" size={12} strokeWidth={3} className="shrink-0 text-jade" />
      ) : null}
      {calibration !== undefined ? (
        <span className="shrink-0 font-mono text-ink3">· {calibration}</span>
      ) : null}
    </Tag>
  );
}

// ── ProvenanceChip ────────────────────────────────────────────────────────────────
const SOURCE_ICONS: Record<ProvenanceSource, LucideIcon> = {
  transcript: Mic,
  deck: Presentation,
  doc: FileText,
  session: Target,
  forge: Hammer,
  studio: Aperture,
  intake: Pickaxe,
  eval: FlaskConical,
};

export interface ProvenanceChipProps {
  /** Origin type; drives the leading decorative icon. */
  source: ProvenanceSource;
  /** The locator, e.g. "00:12:31 · R. Mehta" | "slide 23" | "§3.2"; always text. */
  locator: string;
  /** Optional deep-link to the source → keyboard-focusable native `<a>`. */
  href?: string;
  /** Claude-drafted / never SME-checked → molten warning tone + warning icon. */
  unvalidated?: boolean;
  className?: string;
}

export function ProvenanceChip({
  source,
  locator,
  href,
  unvalidated,
  className,
}: ProvenanceChipProps) {
  const { Tag, linkProps, linkClass } = chipTag(href);
  const Icon = unvalidated ? TriangleAlert : (SOURCE_ICONS[source] ?? FileText);
  return (
    <Tag
      {...linkProps}
      data-testid={`provenance-chip-${source}`}
      data-unvalidated={unvalidated ? 'true' : undefined}
      className={cn(
        'inline-flex max-w-full min-w-0 items-center gap-1.5 rounded-sm border px-2.5 py-0.5 font-mono text-[11px]',
        unvalidated
          ? 'border-molten/40 bg-molten-soft text-molten'
          : 'border-edge bg-slab text-ink2',
        linkClass,
        className,
      )}
    >
      <Icon aria-hidden="true" size={12} strokeWidth={2} className="shrink-0" />
      <span data-slot="locator" title={locator} className="min-w-0 truncate">
        {locator}
      </span>
    </Tag>
  );
}
