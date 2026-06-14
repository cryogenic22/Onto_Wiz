'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { BarChart3, RefreshCw, Brain } from 'lucide-react';
import { PersonaProvider } from '@/lib/persona';
import {
  fetchContributionStats,
  fetchTopContributors,
  fetchContributorSummary,
  fetchSmeContributions,
} from '@/services/api';
import type { ContributionStats as StatsType, ContributorSummary, Contribution } from '@/types/sme';
import ContributionStats from './sme/ContributionStats';
import Leaderboard from './sme/Leaderboard';
import DomainCoverage from './sme/DomainCoverage';
import ContributionHistory from './sme/ContributionHistory';

const REFRESH_INTERVAL = 30_000;

export default function SMEDashboard() {
  const [stats, setStats] = useState<StatsType | null>(null);
  const [contributors, setContributors] = useState<ContributorSummary[]>([]);
  const [selectedSmeId, setSelectedSmeId] = useState<string | null>(null);
  const [selectedSummary, setSelectedSummary] = useState<ContributorSummary | null>(null);
  const [contributions, setContributions] = useState<Contribution[]>([]);

  const [statsLoading, setStatsLoading] = useState(true);
  const [leaderLoading, setLeaderLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadStats = useCallback(async () => {
    setStatsLoading(true);
    try {
      setStats(await fetchContributionStats());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load stats');
    } finally {
      setStatsLoading(false);
    }
  }, []);

  const loadLeaderboard = useCallback(async () => {
    setLeaderLoading(true);
    try {
      setContributors(await fetchTopContributors(10));
    } catch {
      /* non-critical */
    } finally {
      setLeaderLoading(false);
    }
  }, []);

  const refreshAll = useCallback(() => {
    loadStats();
    loadLeaderboard();
  }, [loadStats, loadLeaderboard]);

  useEffect(() => {
    refreshAll();
    const interval = setInterval(refreshAll, REFRESH_INTERVAL);
    return () => clearInterval(interval);
  }, [refreshAll]);

  const handleSelectSme = useCallback(async (smeId: string) => {
    setSelectedSmeId(smeId);
    setDetailLoading(true);
    try {
      const [summary, history] = await Promise.all([
        fetchContributorSummary(smeId),
        fetchSmeContributions(smeId, 20),
      ]);
      setSelectedSummary(summary);
      setContributions(history);
    } catch {
      /* non-critical */
    } finally {
      setDetailLoading(false);
    }
  }, []);

  return (
    <PersonaProvider value="curator">
      <div className="h-screen w-screen bg-slate-950 text-slate-200 flex flex-col overflow-hidden">
        <Header onRefresh={refreshAll} error={error} onDismissError={() => setError(null)} />
        <div className="px-4 py-3 shrink-0">
          <ContributionStats stats={stats} loading={statsLoading} />
        </div>
        <div className="flex-1 flex gap-4 px-4 pb-3 min-h-0">
          <div className="w-[40%] flex flex-col min-h-0 overflow-y-auto">
            <Leaderboard
              contributors={contributors}
              loading={leaderLoading}
              onSelect={handleSelectSme}
              selectedSmeId={selectedSmeId}
            />
          </div>
          <div className="w-[60%] flex flex-col gap-4 min-h-0 overflow-y-auto">
            <DomainCoverage summary={selectedSummary} loading={detailLoading} />
            <ContributionHistory contributions={contributions} loading={detailLoading} />
          </div>
        </div>
      </div>
    </PersonaProvider>
  );
}

function Header({
  onRefresh,
  error,
  onDismissError,
}: {
  onRefresh: () => void;
  error: string | null;
  onDismissError: () => void;
}) {
  return (
    <header className="h-14 border-b border-slate-800/50 flex items-center px-6 bg-slate-900/30 backdrop-blur shrink-0">
      <BarChart3 className="w-5 h-5 text-emerald-400 mr-2" />
      <span className="font-semibold text-slate-200">SME Impact Dashboard</span>
      <Link href="/" className="ml-3 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors">
        <Brain className="w-3.5 h-3.5" />
        SME Game
      </Link>
      <button onClick={onRefresh} className="ml-4 p-1.5 rounded hover:bg-slate-800 transition-colors" title="Refresh">
        <RefreshCw className="w-4 h-4 text-slate-400" />
      </button>
      {error && (
        <div className="ml-4 flex items-center gap-2 px-3 py-1 rounded bg-red-900/20 border border-red-800/50 text-xs text-red-400">
          <span>{error}</span>
          <button onClick={onDismissError} className="text-red-400 hover:text-red-300">&times;</button>
        </div>
      )}
      <div className="ml-auto text-xs text-slate-500">Auto-refreshes every 30s</div>
    </header>
  );
}
