import PackExplorer from '@/features/packs/PackExplorer';

export const metadata = {
  title: 'Onto_Wiz · Pack Explorer',
};

/**
 * `/packs` — D1.0's vertical slice: the first screen driven by real `ontowiz-serve`
 * data and rendered entirely in the D0 Foundry design system.
 */
export default function PacksPage() {
  return <PackExplorer />;
}
