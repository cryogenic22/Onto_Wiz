import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError, authHeaders, getJson } from './http';

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

describe('shared http layer', () => {
  it('omits the Authorization header when no token is supplied', () => {
    expect(authHeaders()).toEqual({});
    expect(authHeaders(undefined)).toEqual({});
  });

  it('sends a Bearer token when one is supplied', async () => {
    expect(authHeaders('abc')).toEqual({ Authorization: 'Bearer abc' });
    fetchMock.mockResolvedValue(jsonResponse({}));
    await getJson('/v1/auth/me', 'abc');
    const init = fetchMock.mock.calls[0][1] as RequestInit;
    expect((init.headers as Record<string, string>).Authorization).toBe('Bearer abc');
  });

  it('falls back to a generic message when the error body is not JSON at all', async () => {
    // e.g. a proxy or gateway returns an HTML error page rather than the API envelope
    const { postJson } = await import('./http');
    fetchMock.mockResolvedValue({
      ok: false,
      status: 502,
      json: () => Promise.reject(new SyntaxError('Unexpected token <')),
    } as unknown as Response);
    await expect(postJson('/v1/context', { q: 1 })).rejects.toMatchObject({
      status: 502,
      message: 'POST /v1/context failed: 502',
    });
  });

  it('ApiError carries the status and the path for the caller to branch on', async () => {
    fetchMock.mockResolvedValue(jsonResponse(null, 404));
    await expect(getJson('/v1/nope')).rejects.toMatchObject({
      status: 404,
      path: '/v1/nope',
      name: 'ApiError',
    });
    expect(new ApiError('x', 500, '/p')).toBeInstanceOf(Error);
  });
});
