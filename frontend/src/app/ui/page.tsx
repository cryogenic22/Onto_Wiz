import { FOUNDRY_COLORS, FOUNDRY_FONTS, FOUNDRY_RADII } from '@/ui/tokens';
import { LifecycleBadge, type LifecycleState } from '@/ui/LifecycleBadge';
import {
  AttributionChip,
  LayerChip,
  ONTOLOGY_LAYERS,
  PROVENANCE_SOURCES,
  ProvenanceChip,
  type ProvenanceSource,
} from '@/ui/chips';

/** Realistic locators (icon supplied by the component, not the string). */
const PROVENANCE_DEMO: Record<ProvenanceSource, string> = {
  transcript: '00:12:31 · R. Mehta',
  deck: 'slide 23',
  doc: '§3.2',
  session: 'session',
  forge: 'forge · hunt',
  studio: 'studio',
  intake: 'intake · mined',
  eval: 'scenario → eval',
};

/**
 * /ui — the in-app design-system gallery (the D0 exit demo surface).
 * Each D0 unit appends a <GallerySection>. D0.1 ships the Design Tokens section.
 */

export const metadata = {
  title: 'Onto_Wiz · Design System',
};

function GallerySection({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mb-14">
      <h2 className="mb-5 font-mono text-[11px] uppercase tracking-[1.2px] text-ink3">
        {title}
      </h2>
      {children}
    </section>
  );
}

function Swatch({ name, hex }: { name: string; hex: string }) {
  return (
    <div
      data-testid={`swatch-${name}`}
      className="overflow-hidden rounded-md border border-edge bg-carbon"
    >
      <div className="h-14 w-full" style={{ background: hex }} />
      <div className="px-2.5 py-2">
        <div className="font-mono text-[12px] text-ink">{name}</div>
        <div className="font-mono text-[11px] text-ink3">{hex}</div>
      </div>
    </div>
  );
}

export default function UIGalleryPage() {
  return (
    <main className="min-h-screen bg-void px-8 py-10 text-ink">
      <header className="mb-12">
        <div className="mb-2 font-mono text-[11px] uppercase tracking-[1px] text-cyan">
          Onto_Wiz Foundry
        </div>
        <h1 className="font-display text-[26px] font-semibold tracking-[-0.5px]">
          Design System
        </h1>
        <p className="mt-1 max-w-[70ch] text-[14px] text-ink2">
          Extracted from Prototype 9. Every component below is the source of truth the
          seven stations consume.
        </p>
      </header>

      <GallerySection title="Design Tokens">
        <div className="grid grid-cols-[repeat(auto-fill,minmax(120px,1fr))] gap-3">
          {Object.entries(FOUNDRY_COLORS).map(([name, hex]) => (
            <Swatch key={name} name={name} hex={hex} />
          ))}
        </div>

        <h3 className="mt-9 mb-4 font-mono text-[10.5px] uppercase tracking-[1px] text-ink3">
          Type
        </h3>
        <div className="space-y-3">
          {(
            [
              ['display', 'Space Grotesk — display', FOUNDRY_FONTS.display],
              ['body', 'IBM Plex Sans — body copy', FOUNDRY_FONTS.body],
              ['mono', 'IBM Plex Mono — labels & code', FOUNDRY_FONTS.mono],
            ] as const
          ).map(([key, label, stack]) => (
            <div
              key={key}
              data-testid={`type-${key}`}
              className="rounded-md border border-edge bg-carbon px-4 py-3"
            >
              <div className="text-[20px]" style={{ fontFamily: stack }}>
                {label}
              </div>
              <div className="mt-1 font-mono text-[11px] text-ink3">{stack}</div>
            </div>
          ))}
        </div>

        <h3 className="mt-9 mb-4 font-mono text-[10.5px] uppercase tracking-[1px] text-ink3">
          Radii
        </h3>
        <div className="flex flex-wrap gap-4">
          {Object.entries(FOUNDRY_RADII).map(([name, value]) => (
            <div key={name} className="text-center">
              <div
                className="h-16 w-16 border border-edge2 bg-slab2"
                style={{ borderRadius: value }}
              />
              <div className="mt-1.5 font-mono text-[11px] text-ink3">
                {name} · {value}
              </div>
            </div>
          ))}
        </div>
      </GallerySection>

      <GallerySection title="Lifecycle & Gate">
        {(
          [
            ['Artifact lifecycle', ['draft', 'review', 'verified', 'active', 'deprecated', 'archived']],
            ['Delta status', ['proposed', 'approved', 'rejected', 'merged']],
            ['Gate outcome', ['pass', 'fail', 'warn']],
          ] as [string, LifecycleState[]][]
        ).map(([group, states]) => (
          <div key={group} className="mb-5">
            <div className="mb-2 font-mono text-[10px] uppercase tracking-[1px] text-ink3">
              {group}
            </div>
            <div className="flex flex-wrap items-center gap-2">
              {states.map((state) => (
                <LifecycleBadge key={state} state={state} />
              ))}
            </div>
          </div>
        ))}
      </GallerySection>

      <GallerySection title="Attribution · Provenance · Layer">
        <div className="mb-2 font-mono text-[10px] uppercase tracking-[1px] text-ink3">
          Attribution
        </div>
        <div
          data-testid="gallery-attribution"
          className="mb-5 flex flex-wrap items-center gap-2"
        >
          <AttributionChip name="Priya K." tone="cyan" />
          <AttributionChip name="R. Mehta" tone="info" validated calibration={0.9} />
          <AttributionChip name="A. Shah" tone="iris" href="#a-shah" />
          <AttributionChip name="K. Bose" tone="jade" calibration={0.79} />
        </div>

        <div className="mb-2 font-mono text-[10px] uppercase tracking-[1px] text-ink3">
          Provenance
        </div>
        <div
          data-testid="gallery-provenance"
          className="mb-5 flex flex-wrap items-center gap-2"
        >
          {PROVENANCE_SOURCES.map((source) => (
            <ProvenanceChip key={source} source={source} locator={PROVENANCE_DEMO[source]} />
          ))}
          <ProvenanceChip source="deck" locator="slide 23" href="#deck-23" />
          <ProvenanceChip
            source="doc"
            locator="Claude-drafted — never SME-checked"
            unvalidated
          />
        </div>

        <div className="mb-2 font-mono text-[10px] uppercase tracking-[1px] text-ink3">
          Ontology layer
        </div>
        <div data-testid="gallery-layer" className="flex flex-wrap items-center gap-2">
          {ONTOLOGY_LAYERS.map((layer) => (
            <LayerChip key={layer} layer={layer} />
          ))}
        </div>
      </GallerySection>
    </main>
  );
}
