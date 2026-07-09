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

const BASE_URL =
  process.env.NEXT_PUBLIC_CATALOG_API_URL ?? 'http://localhost:8080';

type Json = Record<string, unknown>;

function authHeaders(token?: string): Record<string, string> {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function getJson<T>(path: string, token?: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, { headers: authHeaders(token) });
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return res.json() as Promise<T>;
}

async function postJson<T>(path: string, body: Json, token?: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders(token) },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    const msg = (detail as { detail?: string } | null)?.detail ?? `POST ${path} failed: ${res.status}`;
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
  }
  return res.json() as Promise<T>;
}

const enc = encodeURIComponent;

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
