import CuratorDashboard from '@/components/CuratorDashboard';

export const metadata = {
  title: 'Onto Wiz | Curator Dashboard',
  description: 'Delta review queue and governance dashboard',
};

export default function CuratorPage() {
  return (
    <main>
      <CuratorDashboard />
    </main>
  );
}
