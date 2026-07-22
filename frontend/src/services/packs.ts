/** Pack Explorer client (D1.0) — `ontowiz-serve` Tier A read API.
 *
 * Read-only. Three calls against endpoints that are already `VERIFIED` (F3 `/v1/context`,
 * F5 UX-2 `/detail`). Shares the HTTP layer with `catalog.ts` via `./http`.
 *
 * OVERLAP NOTE (declared, not silently duplicated): `catalog.ts::fetchPackDetail` hits the
 * same `/detail` URL but returns `@/types/catalog`'s weaker shape — `evals` is an untyped
 * `Record<string, unknown>` and its `ArtifactRow` has no `confidence`. That shape cannot
 * express D1.0's §5b "no eval evidence" invariant, so this module types the response
 * accurately instead. Converging the two clients is a follow-up: changing the catalog's
 * return type would ripple into `/catalog`'s verified components, which is outside this
 * unit's blast radius.
 */

import { enc, getJson, postJson } from './http';
import type {
  ContextRequest,
  ContextResponse,
  PackDetail,
  PackSummary,
} from '@/types/packs';

/** `GET /v1/packs` — every compiled pack the registry can serve. */
export function fetchPacks(): Promise<PackSummary[]> {
  return getJson<PackSummary[]>('/v1/packs');
}

/** `GET /v1/packs/{name}/{version}/detail` — artifact inventory + eval-coverage gaps. */
export function fetchPackDetail(
  name: string,
  version: string,
): Promise<PackDetail> {
  return getJson<PackDetail>(`/v1/packs/${enc(name)}/${enc(version)}/detail`);
}

/** `POST /v1/context` — compile query-ranked context and return its trust envelope.
 *
 * A POST that mutates nothing: the body carries the query, the response is a read.
 */
export function fetchContext(request: ContextRequest): Promise<ContextResponse> {
  return postJson<ContextResponse>('/v1/context', {
    ...request,
  } as unknown as Record<string, unknown>);
}
