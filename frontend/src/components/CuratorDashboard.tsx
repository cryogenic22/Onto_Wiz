'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { Shield, RefreshCw, Brain, BarChart3 } from 'lucide-react';
import { PersonaProvider } from '@/lib/persona';
import {
  fetchReviewQueue,
  fetchQueueStats,
  fetchAuditLog,
  approveDelta,
  rejectDelta,
  escalateDelta,
  exportAuditLog,
} from '@/services/api';
import type { ReviewQueueItem, QueueStatsResponse, AuditEntry } from '@/types/curator';
import QueueStats from './curator/QueueStats';
import ReviewQueue from './curator/ReviewQueue';
import DeltaDetail from './curator/DeltaDetail';
import AuditTrail from './curator/AuditTrail';

const REFRESH_INTERVAL = 30_000;

export default function CuratorDashboard() {
  const [queueItems, setQueueItems] = useState<ReviewQueueItem[]>([]);
  const [stats, setStats] = useState<QueueStatsResponse | null>(null);
  const [auditEntries, setAuditEntries] = useState<AuditEntry[]>([]);
  const [selectedItem, setSelectedItem] = useState<ReviewQueueItem | null>(null);
  const [roleFilter, setRoleFilter] = useState('');

  const [queueLoading, setQueueLoading] = useState(true);
  const [statsLoading, setStatsLoading] = useState(true);
  const [auditLoading, setAuditLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadQueue = useCallback(async (role?: string) => {
    setQueueLoading(true);
    try {
      const items = await fetchReviewQueue(role || undefined, 50);
      setQueueItems(items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load queue');
    } finally {
      setQueueLoading(false);
    }
  }, []);

  const loadStats = useCallback(async () => {
    setStatsLoading(true);
    try {
      setStats(await fetchQueueStats());
    } catch {
      /* stats are non-critical */
    } finally {
      setStatsLoading(false);
    }
  }, []);

  const loadAudit = useCallback(async () => {
    setAuditLoading(true);
    try {
      setAuditEntries(await fetchAuditLog(50));
    } catch {
      /* audit is non-critical */
    } finally {
      setAuditLoading(false);
    }
  }, []);

  const refreshAll = useCallback(() => {
    loadQueue(roleFilter);
    loadStats();
    loadAudit();
  }, [loadQueue, loadStats, loadAudit, roleFilter]);

  // Initial load + auto-refresh
  useEffect(() => {
    refreshAll();
    const interval = setInterval(refreshAll, REFRESH_INTERVAL);
    return () => clearInterval(interval);
  }, [refreshAll]);

  // Reload queue when filter changes
  useEffect(() => {
    loadQueue(roleFilter);
  }, [roleFilter, loadQueue]);

  const handleApprove = async (deltaId: string, reviewer: string) => {
    setActionLoading(true);
    try {
      await approveDelta(deltaId, reviewer);
      setSelectedItem(null);
      refreshAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Approve failed');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async (deltaId: string, reviewer: string, reason: string) => {
    setActionLoading(true);
    try {
      await rejectDelta(deltaId, reviewer, reason);
      setSelectedItem(null);
      refreshAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Reject failed');
    } finally {
      setActionLoading(false);
    }
  };

  const handleEscalate = async (deltaId: string, reason: string) => {
    setActionLoading(true);
    try {
      await escalateDelta(deltaId, reason);
      setSelectedItem(null);
      refreshAll();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Escalate failed');
    } finally {
      setActionLoading(false);
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const blob = await exportAuditLog(500);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit_log_${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
    } finally {
      setExporting(false);
    }
  };

  return (
    <PersonaProvider value="curator">
      <div className="h-screen w-screen bg-slate-950 text-slate-200 flex flex-col overflow-hidden">
        <Header onRefresh={refreshAll} error={error} onDismissError={() => setError(null)} />
        <div className="px-4 py-3 shrink-0">
          <QueueStats stats={stats} loading={statsLoading} />
        </div>
        <div className="flex-1 flex gap-4 px-4 pb-3 min-h-0">
          <div className="w-[55%] flex flex-col min-h-0">
            <ReviewQueue
              items={queueItems}
              loading={queueLoading}
              selectedId={selectedItem?.delta.id ?? null}
              onSelect={setSelectedItem}
              roleFilter={roleFilter}
              onRoleFilterChange={setRoleFilter}
            />
          </div>
          <div className="w-[45%] flex flex-col min-h-0">
            <DeltaDetail
              item={selectedItem}
              onApprove={handleApprove}
              onReject={handleReject}
              onEscalate={handleEscalate}
              actionLoading={actionLoading}
            />
          </div>
        </div>
        <div className="px-4 pb-3 shrink-0">
          <AuditTrail entries={auditEntries} loading={auditLoading} onExport={handleExport} exporting={exporting} />
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
      <Shield className="w-5 h-5 text-blue-400 mr-2" />
      <span className="font-semibold text-slate-200">Curator Dashboard</span>
      <Link href="/" className="ml-3 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors">
        <Brain className="w-3.5 h-3.5" />
        SME Game
      </Link>
      <Link href="/sme-dashboard" className="ml-1 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors">
        <BarChart3 className="w-3.5 h-3.5" />
        SME Impact
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
