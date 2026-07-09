'use client';

import { useState } from 'react';

import type { Principal } from '@/types/catalog';

interface Props {
  principal: Principal | null;
  error?: string | null;
  onLogin: (email: string, password: string) => void;
  onLogout: () => void;
}

/** Sign-in / identity strip. A real Bearer principal replaces the old trusted
 * X-OntoWiz-Role header — the role shown here is the authenticated one. */
export default function LoginBar({ principal, error, onLogin, onLogout }: Props) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  if (principal) {
    return (
      <div className="flex items-center gap-2 text-sm text-slate-300">
        Signed in as <b className="text-slate-100">{principal.email}</b>
        <span className="rounded-full border border-slate-700 px-2 py-0.5 text-[11px] text-teal-400">{principal.role}</span>
        <button type="button" onClick={onLogout} className="ml-2 text-slate-400 underline">Sign out</button>
      </div>
    );
  }

  return (
    <form
      onSubmit={(e) => { e.preventDefault(); onLogin(email, password); }}
      className="flex items-center gap-2"
    >
      <input
        aria-label="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="email"
        className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1 text-sm text-slate-100"
      />
      <input
        aria-label="Password"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="password"
        className="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1 text-sm text-slate-100"
      />
      <button type="submit" className="rounded-lg border border-slate-700 px-3 py-1 text-sm text-slate-200">Sign in</button>
      {error && <span role="alert" className="text-xs text-rose-400">{error}</span>}
    </form>
  );
}
