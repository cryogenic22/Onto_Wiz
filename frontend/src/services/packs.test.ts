import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from './http';
import { fetchContext, fetchPackDetail, fetchPacks } from './packs';

/** Default base URL when NEXT_PUBLIC_ONTOWIZ_API_URL is unset (see D1.0 §2). */
const BASE = 'http://localhost:8080';

function jsonResponse(body: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
  } as unknown as Response;
}

let fetchMock: ReturnType<typeof vi.fn>;

beforeEach(() => {
  fetchMock = vi.fn();
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('packs client', () => {
  it('fetchPacks GETs /v1/packs on the configured base URL', async () => {
    fetchMock.mockResolvedValue(jsonResponse([]));
    await fetchPacks();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toBe(`${BASE}/v1/packs`);
  });

  it('fetchPacks returns the parsed rows', async () => {
    fetchMock.mockResolvedValue(
      jsonResponse([{ name: 'commercial_analytics', version: '0.1.0' }]),
    );
    const rows = await fetchPacks();
    expect(rows).toHaveLength(1);
    expect(rows[0].name).toBe('commercial_analytics');
  });

  it('fetchPackDetail URL-encodes the name and version', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ artifacts: [] }));
    await fetchPackDetail('evil/name', '1.0/../x');
    const url = fetchMock.mock.calls[0][0] as string;
    // the path separators of the *route* survive; the injected ones must not
    expect(url).toBe(`${BASE}/v1/packs/evil%2Fname/1.0%2F..%2Fx/detail`);
    expect(url).not.toContain('/../');
  });

  it('fetchContext POSTs the request body as JSON', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ eligible: [], tokens_estimate: 0 }));
    await fetchContext({
      pack_name: 'commercial_analytics',
      pack_version: '0.3.0',
      query: 'formulary exclusion',
    });
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe(`${BASE}/v1/context`);
    expect(init.method).toBe('POST');
    expect((init.headers as Record<string, string>)['Content-Type']).toBe(
      'application/json',
    );
    expect(JSON.parse(init.body as string)).toMatchObject({
      pack_name: 'commercial_analytics',
      pack_version: '0.3.0',
      query: 'formulary exclusion',
    });
  });

  it('surfaces a typed ApiError on a non-2xx response (never an empty result)', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: 'boom' }, 500));
    await expect(fetchPacks()).rejects.toBeInstanceOf(ApiError);
    fetchMock.mockResolvedValue(jsonResponse({ detail: 'boom' }, 500));
    await expect(fetchPacks()).rejects.toMatchObject({ status: 500 });
  });

  it('surfaces the server detail verbatim when a POST fails', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: 'pack not loaded' }, 503));
    await expect(
      fetchContext({ pack_name: 'p', pack_version: '1', query: 'q' }),
    ).rejects.toMatchObject({ message: 'pack not loaded', status: 503 });
  });

  it('stringifies a non-string POST error detail rather than rendering [object Object]', async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({ detail: [{ loc: ['body', 'query'], msg: 'required' }] }, 422),
    );
    await expect(
      fetchContext({ pack_name: 'p', pack_version: '1', query: '' }),
    ).rejects.toMatchObject({ status: 422 });
    fetchMock.mockResolvedValue(
      jsonResponse({ detail: [{ msg: 'required' }] }, 422),
    );
    await expect(
      fetchContext({ pack_name: 'p', pack_version: '1', query: '' }),
    ).rejects.toThrow(/required/);
  });

  it('falls back to a generic POST message when the body carries no detail', async () => {
    fetchMock.mockResolvedValue(jsonResponse(null, 502));
    await expect(
      fetchContext({ pack_name: 'p', pack_version: '1', query: 'q' }),
    ).rejects.toThrow(/POST \/v1\/context failed: 502/);
  });

  it('preserves a 404 status so the UI can distinguish missing from broken', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: 'pack not found' }, 404));
    await expect(fetchPackDetail('nope', '0.0.0')).rejects.toMatchObject({
      status: 404,
    });
  });
});
