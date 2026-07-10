/**
 * Foundry design tokens — the typed source of truth for the Onto_Wiz design system.
 *
 * Values are lifted verbatim from Prototype 9's `:root`
 * (docs/reviews/ontowiz_nextgen_prototype_9.html), which is the UI source of truth.
 * `tokens.css` mirrors these into Tailwind 4 `@theme` utilities; the drift-guard test
 * in `tokens.test.ts` keeps the two in sync so there is a single source of truth.
 */

/** Named colour tokens (surfaces → borders → text → accents). */
export const FOUNDRY_COLORS = {
  // Surfaces (dark → light)
  void: '#0A1519',
  carbon: '#0E1D22',
  slab: '#15282E',
  slab2: '#1C333A',
  // Borders
  edge: '#26414A',
  edge2: '#365660',
  // Text (bright → dim)
  ink: '#E8EFEC',
  ink2: '#9FB4B2',
  ink3: '#647C7B',
  // Accents
  cyan: '#4CC6D4',
  molten: '#EDA93C',
  'molten-hot': '#FFC44D',
  jade: '#46C08A',
  ember: '#EF6A50',
  info: '#6BA8E8',
  iris: '#9E8BEE',
} as const;

export type FoundryColor = keyof typeof FOUNDRY_COLORS;

/** Font-family stacks. Webfont *loading* (next/font) is a later unit; the stacks
 *  fall back to system fonts so the design reads correctly offline today. */
export const FOUNDRY_FONTS = {
  display: '"Space Grotesk", system-ui, sans-serif',
  body: '"IBM Plex Sans", system-ui, sans-serif',
  mono: '"IBM Plex Mono", ui-monospace, Consolas, monospace',
} as const;

/** Radius scale distilled from Prototype 9 (badge → button → card → pill). */
export const FOUNDRY_RADII = {
  sm: '6px',
  md: '9px',
  lg: '14px',
  pill: '20px',
} as const;
