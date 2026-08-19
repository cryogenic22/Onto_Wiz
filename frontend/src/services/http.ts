/** Shared HTTP layer for the `ontowiz-serve` REST app (Tier A read API).
 *
 * PROVENANCE: `getJson` / `postJson` / `authHeaders` / `enc` are **ported verbatim** from
 * the private helpers in `src/services/catalog.ts` (behaviour-identical, including the
 * exact error-message formats its tests assert). Extracted by D1.0 so the pack/context
 * client reuses them instead of adding a second fetch wrapper against the same backend
 * (anti-bloat gate 1). `catalog.ts` now imports from here.
 *
 * The only behavioural addition is the typed `ApiError`: it subclasses `Error` with the
 * same message, so existing `rejects.toThrow(/…/)` assertions are unaffected, while new
 * callers can branch on `status` (404 "missing" vs 500 "broken") instead of regexing text.
 */

/** Base URL of the ontowiz-serve app.
 *
 * `NEXT_PUBLIC_ONTOWIZ_API_URL` is the canonical name; `NEXT_PUBLIC_CATALOG_API_URL` is
 * still honoured because deployments already set it — the catalog and the pack explorer
 * are the same backend, so this stays ONE host, not two.
 */
export const BASE_URL =
  process.env.NEXT_PUBLIC_ONTOWIZ_API_URL ??
  process.env.NEXT_PUBLIC_CATALOG_API_URL ??
  'http://localhost:8080';

export type Json = Record<string, unknown>;

/** A failed API call, carrying the HTTP status so callers can distinguish failure modes. */
export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly path: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export function authHeaders(token?: string): Record<string, string> {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function getJson<T>(path: string, token?: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, { headers: authHeaders(token) });
  if (!res.ok) throw new ApiError(`GET ${path} failed: ${res.status}`, res.status, path);
  return res.json() as Promise<T>;
}

export async function postJson<T>(
  path: string,
  body: Json,
  token?: string,
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders(token) },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    const msg =
      (detail as { detail?: string } | null)?.detail ??
      `POST ${path} failed: ${res.status}`;
    throw new ApiError(
      typeof msg === 'string' ? msg : JSON.stringify(msg),
      res.status,
      path,
    );
  }
  return res.json() as Promise<T>;
}

export const enc = encodeURIComponent;
