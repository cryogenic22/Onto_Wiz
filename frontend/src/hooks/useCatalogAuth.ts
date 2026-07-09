'use client';

import { useCallback, useEffect, useState } from 'react';

import { fetchMe, login as loginRequest } from '@/services/catalog';
import type { Principal } from '@/types/catalog';

const TOKEN_KEY = 'ontowiz.catalog.token';

/** Catalog auth: a JWT in localStorage + the resolved principal. The token is
 * the source of truth for the caller's role (the server derives capabilities
 * from it), replacing the old trusted X-OntoWiz-Role header. */
export function useCatalogAuth() {
  const [token, setToken] = useState<string | null>(null);
  const [principal, setPrincipal] = useState<Principal | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const saved = typeof window !== 'undefined' ? window.localStorage.getItem(TOKEN_KEY) : null;
    if (!saved) return;
    // Only adopt the token once /me validates it — state is set in the async
    // callback, never synchronously in the effect body.
    fetchMe(saved)
      .then((p) => { setToken(saved); setPrincipal(p); })
      .catch(() => window.localStorage.removeItem(TOKEN_KEY));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setError(null);
    try {
      const res = await loginRequest(email, password);
      window.localStorage.setItem(TOKEN_KEY, res.access_token);
      setToken(res.access_token);
      setPrincipal({ sub: res.email, role: res.role, email: res.email });
    } catch {
      setError('Invalid credentials');
    }
  }, []);

  const logout = useCallback(() => {
    window.localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setPrincipal(null);
  }, []);

  return { token, principal, error, login, logout };
}
