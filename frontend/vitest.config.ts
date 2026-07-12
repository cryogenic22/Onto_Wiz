import react from '@vitejs/plugin-react';
import tsconfigPaths from 'vite-tsconfig-paths';
import { defineConfig } from 'vitest/config';

// Frontend test gate (ADR-017). Mirrors market_zero's vitest setup: jsdom + RTL.
// Coverage is scoped to the catalog code this unit adds, so the >=85%-on-new-code
// bar (ADR-015) is measured against the port, not the whole legacy app.
export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./vitest.setup.ts'],
    include: ['src/**/*.test.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'text-summary'],
      include: [
        'src/services/catalog.ts',
        'src/types/catalog.ts',
        'src/components/catalog/**',
        // D0 design system (foundry tokens + gallery + ui/ primitives)
        'src/ui/**/*.{ts,tsx}',
        'src/app/ui/**/*.tsx',
        'src/components/ui/**/*.tsx',
      ],
      thresholds: { lines: 85, functions: 85, statements: 85 },
    },
  },
});
