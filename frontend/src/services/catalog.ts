/** Domain Intelligence Catalog API client (ontowiz-serve, Tier A).
 *
 * Talks to the catalog REST app — a different backend from the legacy `api.ts`
 * (which targets the `src` app on :8000). Base URL via NEXT_PUBLIC_CATALOG_API_URL.
 */

import type {
  ArtifactView,
  CatalogEntry,
  Comment,
  DiffResult,
  FunctionSlice,
  LoginResponse,
  PackDetail,
  PackUsage,
  Principal,
  RoleCapabilities,
  SearchHit,
} from '@/types/catalog';

// HTTP helpers moved to `./http` by D1.0 so the pack/context client shares them rather
// than duplicating a fetch wrapper against this same backend. Behaviour is unchanged.
import { enc, getJson, postJson } from './http';

// ── Catalog ────────────────────────────────────────────────────────
export function fetchCatalog(): Promise<CatalogEntry[]> {
  return getJson<CatalogEntry[]>('/v1/catalog');
}

export function searchCatalog(
  q: string,
  opts: { function?: string; domain?: string } = {},
): Promise<SearchHit[]> {
  const params = new URLSearchParams({ q });
  if (opts.function) params.set('function', opts.function);
  if (opts.domain) params.set('domain', opts.domain);
  return getJson<SearchHit[]>(`/v1/catalog/search?${params}`);
}

export function fetchCatalogStats(): Promise<PackUsage[]> {
  return getJson<PackUsage[]>('/v1/catalog/stats');
}

// ── Pack views ─────────────────────────────────────────────────────
export function fetchPackFunctions(name: string, version: string): Promise<FunctionSlice[]> {
  return getJson<FunctionSlice[]>(`/v1/packs/${enc(name)}/${enc(version)}/functions`);
}

export function fetchPackDetail(name: string, version: string): Promise<PackDetail> {
  return getJson<PackDetail>(`/v1/packs/${enc(name)}/${enc(version)}/detail`);
}

export function fetchArtifact(name: string, version: string, id: string): Promise<ArtifactView> {
  return getJson<ArtifactView>(`/v1/packs/${enc(name)}/${enc(version)}/artifacts/${enc(id)}`);
}

export function fetchPackDiff(name: string, from: string, to: string): Promise<DiffResult> {
  const params = new URLSearchParams({ from, to });
  return getJson<DiffResult>(`/v1/packs/${enc(name)}/diff?${params}`);
}

// ── Collaboration ──────────────────────────────────────────────────
export function fetchComments(name: string, version: string, id: string): Promise<Comment[]> {
  return getJson<Comment[]>(`/v1/packs/${enc(name)}/${enc(version)}/artifacts/${enc(id)}/comments`);
}

export function postComment(
  name: string, version: string, id: string,
  body: { author: string; text: string }, token?: string,
): Promise<Comment> {
  return postJson<Comment>(
    `/v1/packs/${enc(name)}/${enc(version)}/artifacts/${enc(id)}/comments`, body, token,
  );
}

export function reviewArtifact(
  name: string, version: string, id: string,
  body: { decision: string; note?: string }, token?: string,
): Promise<{ artifact_id: string; decision: string; by: string }> {
  return postJson(`/v1/packs/${enc(name)}/${enc(version)}/artifacts/${enc(id)}/review`, body, token);
}

// ── Auth / roles ───────────────────────────────────────────────────
export function fetchRoles(): Promise<RoleCapabilities> {
  return getJson<RoleCapabilities>('/v1/roles');
}

export function login(email: string, password: string): Promise<LoginResponse> {
  return postJson<LoginResponse>('/v1/auth/login', { email, password });
}

export function fetchMe(token: string): Promise<Principal> {
  return getJson<Principal>('/v1/auth/me', token);
}
