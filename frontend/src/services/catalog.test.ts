import { afterEach, describe, expect, it, vi } from 'vitest';

import {
  fetchArtifact,
  fetchCatalog,
  fetchCatalogStats,
  fetchComments,
  fetchMe,
  fetchPackDetail,
  fetchPackDiff,
  fetchPackFunctions,
  fetchRoles,
  login,
  postComment,
  reviewArtifact,
  searchCatalog,
} from './catalog';

function mockFetch(payload: unknown, ok = true, status = 200) {
  const fn = vi.fn().mockResolvedValue({
    ok,
    status,
    json: () => Promise.resolve(payload),
  });
  vi.stubGlobal('fetch', fn);
  return fn;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('catalog client', () => {
  it('fetchCatalog returns the parsed array', async () => {
    const fn = mockFetch([{ name: 'commercial_analytics', domain: 'commercial' }]);
    const out = await fetchCatalog();
    expect(out[0].name).toBe('commercial_analytics');
    expect(fn).toHaveBeenCalledWith(
      expect.stringContaining('/v1/catalog'),
      expect.any(Object),
    );
  });

  it('searchCatalog encodes q and optional function filter', async () => {
    const fn = mockFetch([]);
    await searchCatalog('lost share', { function: 'forecasting' });
    const url = fn.mock.calls[0][0] as string;
    expect(url).toContain('/v1/catalog/search?');
    expect(url).toContain('q=lost+share');
    expect(url).toContain('function=forecasting');
  });

  it('fetchArtifact URL-encodes path segments', async () => {
    const fn = mockFetch({ id: 'a b' });
    await fetchArtifact('commercial_analytics', '0.1.0', 'rule x');
    expect(fn.mock.calls[0][0]).toContain('/artifacts/rule%20x');
  });

  it('postComment sends a Bearer token and JSON body', async () => {
    const fn = mockFetch({ author: 'Me', text: 'hi' });
    await postComment('p', '0.1.0', 'a1', { author: 'Me', text: 'hi' }, 'tok123');
    const init = fn.mock.calls[0][1] as RequestInit;
    expect(init.method).toBe('POST');
    expect((init.headers as Record<string, string>).Authorization).toBe('Bearer tok123');
    expect(JSON.parse(init.body as string)).toEqual({ author: 'Me', text: 'hi' });
  });

  it('login posts credentials and returns a token', async () => {
    mockFetch({ access_token: 't', token_type: 'bearer', role: 'curator', email: 'c@x.io' });
    const res = await login('c@x.io', 'pw');
    expect(res.access_token).toBe('t');
    expect(res.role).toBe('curator');
  });

  it('surfaces the server detail on a failed write', async () => {
    mockFetch({ detail: "role 'sme' lacks capability 'review'" }, false, 403);
    await expect(
      reviewArtifact('p', '0.1.0', 'a1', { decision: 'approve' }, 'tok'),
    ).rejects.toThrow(/lacks capability/);
  });

  it('throws on a failed read', async () => {
    mockFetch(null, false, 500);
    await expect(fetchCatalog()).rejects.toThrow(/failed: 500/);
  });

  it('builds the expected URLs for the GET wrappers', async () => {
    const cases: Array<[() => Promise<unknown>, string]> = [
      [() => fetchPackFunctions('p', '0.1.0'), '/v1/packs/p/0.1.0/functions'],
      [() => fetchPackDetail('p', '0.1.0'), '/v1/packs/p/0.1.0/detail'],
      [() => fetchPackDiff('p', '0.1.0', '0.2.0'), '/v1/packs/p/diff?from=0.1.0&to=0.2.0'],
      [() => fetchCatalogStats(), '/v1/catalog/stats'],
      [() => fetchComments('p', '0.1.0', 'a1'), '/v1/packs/p/0.1.0/artifacts/a1/comments'],
      [() => fetchRoles(), '/v1/roles'],
      [() => searchCatalog('q', { domain: 'commercial' }), 'domain=commercial'],
    ];
    for (const [call, expected] of cases) {
      const fn = mockFetch([]);
      await call();
      expect(fn.mock.calls[0][0]).toContain(expected);
      vi.unstubAllGlobals();
    }
  });

  it('fetchMe sends the bearer token', async () => {
    const fn = mockFetch({ sub: 'curator', role: 'curator', email: 'c@x.io' });
    const me = await fetchMe('tok');
    expect(me.role).toBe('curator');
    const init = fn.mock.calls[0][1] as RequestInit;
    expect((init.headers as Record<string, string>).Authorization).toBe('Bearer tok');
  });
});
