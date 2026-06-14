import SMEDashboard from '@/components/SMEDashboard';

export const metadata = {
  title: 'Onto Wiz | SME Impact Dashboard',
  description: 'Contributor profiles, leaderboard, and domain coverage',
};

export default function SMEDashboardPage() {
  return (
    <main>
      <SMEDashboard />
    </main>
  );
}
