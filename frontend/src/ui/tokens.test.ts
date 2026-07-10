import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { FOUNDRY_COLORS, FOUNDRY_FONTS, FOUNDRY_RADII } from './tokens';

// Verbatim from Prototype 9 `:root` — the UI source of truth
// (docs/reviews/ontowiz_nextgen_prototype_9.html).
const EXPECTED_COLORS: Record<string, string> = {
  void: '#0A1519',
  carbon: '#0E1D22',
  slab: '#15282E',
  slab2: '#1C333A',
  edge: '#26414A',
  edge2: '#365660',
  ink: '#E8EFEC',
  ink2: '#9FB4B2',
  ink3: '#647C7B',
  cyan: '#4CC6D4',
  molten: '#EDA93C',
  'molten-hot': '#FFC44D',
  jade: '#46C08A',
  ember: '#EF6A50',
  info: '#6BA8E8',
  iris: '#9E8BEE',
};

describe('foundry tokens', () => {
  it('exposes every Prototype 9 colour token with the exact hex', () => {
    expect(FOUNDRY_COLORS).toEqual(EXPECTED_COLORS);
  });

  it('exposes display/body/mono font stacks and an ordered radius scale', () => {
    expect(FOUNDRY_FONTS.display).toMatch(/Space Grotesk/);
    expect(FOUNDRY_FONTS.body).toMatch(/IBM Plex Sans/);
    expect(FOUNDRY_FONTS.mono).toMatch(/IBM Plex Mono/);
    expect(Object.keys(FOUNDRY_RADII)).toEqual(['sm', 'md', 'lg', 'pill']);
  });

  it('keeps tokens.css in sync with tokens.ts (no silent CSS/TS drift)', () => {
    const css = readFileSync(
      resolve(process.cwd(), 'src/ui/tokens.css'),
      'utf8',
    ).toLowerCase();
    for (const hex of Object.values(FOUNDRY_COLORS)) {
      expect(css, `tokens.css is missing ${hex}`).toContain(hex.toLowerCase());
    }
  });
});
