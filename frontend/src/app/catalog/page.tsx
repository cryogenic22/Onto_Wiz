'use client';

import { useCallback, useEffect, useState } from 'react';

import ArtifactDrawer from '@/components/catalog/ArtifactDrawer';
import ArtifactList from '@/components/catalog/ArtifactList';
import CatalogGrid from '@/components/catalog/CatalogGrid';
import FunctionSlices from '@/components/catalog/FunctionSlices';
import LoginBar from '@/components/catalog/LoginBar';
import { useCatalogAuth } from '@/hooks/useCatalogAuth';
import {
  fetchArtifact,
  fetchCatalog,
  fetchComments,
  fetchPackDetail,
  fetchPackFunctions,
  fetchRoles,
  postComment,
  reviewArtifact,
  searchCatalog,
} from '@/services/catalog';
import type {
  ArtifactRow,
  ArtifactView,
  CatalogEntry,
  Comment,
  FunctionSlice,
  RoleCapabilities,
} from '@/types/catalog';

export default function CatalogPage() {
  const auth = useCatalogAuth();
  const [entries, setEntries] = useState<CatalogEntry[]>([]);
  const [query, setQuery] = useState('');
  const [roles, setRoles] = useState<RoleCapabilities>({});

  const [pack, setPack] = useState<CatalogEntry | null>(null);
  const [slices, setSlices] = useState<FunctionSlice[]>([]);
  const [rows, setRows] = useState<ArtifactRow[]>([]);
  const [activeFn, setActiveFn] = useState('all');

  const [artifact, setArtifact] = useState<ArtifactView | null>(null);
  const [comments, setComments] = useState<Comment[]>([]);

  useEffect(() => { fetchRoles().then(setRoles).catch(() => {}); }, []);

  useEffect(() => {
    const run = query
      ? searchCatalog(query).then((hits) => hits.map((h) => h.name))
      : Promise.resolve(null);
    if (!query) { fetchCatalog().then(setEntries).catch(() => setEntries([])); return; }
    Promise.all([fetchCatalog(), run]).then(([all, names]) => {
      const set = new Set(names);
      setEntries(all.filter((e) => set.has(e.name)));
    }).catch(() => setEntries([]));
  }, [query]);

  const openPack = useCallback((entry: CatalogEntry) => {
    setPack(entry);
    setActiveFn('all');
    const v = entry.latest_version;
    fetchPackFunctions(entry.name, v).then(setSlices).catch(() => setSlices([]));
    fetchPackDetail(entry.name, v).then((d) => setRows(d.artifacts)).catch(() => setRows([]));
  }, []);

  const openArtifact = useCallback((id: string) => {
    if (!pack) return;
    const v = pack.latest_version;
    fetchArtifact(pack.name, v, id).then(setArtifact).catch(() => setArtifact(null));
    fetchComments(pack.name, v, id).then(setComments).catch(() => setComments([]));
  }, [pack]);

  const refreshComments = useCallback(() => {
    if (pack && artifact) fetchComments(pack.name, pack.latest_version, artifact.id).then(setComments);
  }, [pack, artifact]);

  const onPostComment = useCallback((text: string) => {
    if (!pack || !artifact) return;
    const author = auth.principal?.email ?? 'You';
    postComment(pack.name, pack.latest_version, artifact.id, { author, text }, auth.token ?? undefined)
      .then(refreshComments).catch(() => {});
  }, [pack, artifact, auth.principal, auth.token, refreshComments]);

  const onReview = useCallback((decision: string) => {
    if (!pack || !artifact || !auth.token) return;
    reviewArtifact(pack.name, pack.latest_version, artifact.id, { decision }, auth.token)
      .then(refreshComments).catch(() => {});
  }, [pack, artifact, auth.token, refreshComments]);

  const canReview = !!auth.principal && (roles[auth.principal.role]?.includes('review') ?? false);
  const visibleRows = activeFn === 'all'
    ? rows
    : rows.filter((r) => slices.find((s) => s.function === activeFn) && r.served);

  return (
    <main className="mx-auto max-w-6xl px-6 py-8 text-slate-100">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Domain Intelligence Catalog</h1>
        <LoginBar principal={auth.principal} error={auth.error} onLogin={auth.login} onLogout={auth.logout} />
      </div>

      {!pack && (
        <>
          <input
            aria-label="Search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search packs, functions, heuristics…"
            className="mb-5 w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-slate-100"
          />
          <CatalogGrid entries={entries} onOpen={openPack} />
        </>
      )}

      {pack && (
        <div>
          <button type="button" onClick={() => { setPack(null); setArtifact(null); }} className="mb-4 font-semibold text-slate-400">
            ← Back to catalog
          </button>
          <h2 className="text-xl font-semibold">{pack.name} <span className="text-slate-500">v{pack.latest_version}</span></h2>

          <section className="mt-4 rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
            <b className="text-slate-200">Function slices</b>
            <div className="mt-2">
              <FunctionSlices slices={slices} total={rows.length} active={activeFn} onSelect={setActiveFn} />
            </div>
          </section>

          <section className="mt-4 rounded-2xl border border-slate-800 bg-slate-900/60 p-4">
            <b className="text-slate-200">Artifacts</b>
            <div className="mt-3">
              <ArtifactList rows={visibleRows} onOpen={openArtifact} />
            </div>
          </section>
        </div>
      )}

      {artifact && (
        <ArtifactDrawer
          artifact={artifact}
          comments={comments}
          canReview={canReview}
          onClose={() => setArtifact(null)}
          onPostComment={onPostComment}
          onReview={onReview}
        />
      )}
    </main>
  );
}
