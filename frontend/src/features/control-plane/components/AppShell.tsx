'use client';

import type { ReactNode } from 'react';
import {
  Boxes,
  ChevronDown,
  FlaskConical,
  LayoutDashboard,
  LibraryBig,
  PackageCheck,
  Search,
  ShieldCheck,
  UserRound,
} from 'lucide-react';

import styles from '../control-plane.module.css';
import type { WorkspaceContext } from '../types';

export type ViewId = 'command' | 'knowledge' | 'evaluations' | 'simulator' | 'release';

const navItems = [
  { id: 'command' as const, label: 'Command center', icon: LayoutDashboard },
  { id: 'knowledge' as const, label: 'Knowledge', icon: LibraryBig },
  { id: 'evaluations' as const, label: 'Evaluations', icon: ShieldCheck },
  { id: 'simulator' as const, label: 'Agent simulator', icon: FlaskConical },
  { id: 'release' as const, label: 'Release center', icon: PackageCheck },
];

interface AppShellProps {
  workspace: WorkspaceContext;
  activeView: ViewId;
  onViewChange: (view: ViewId) => void;
  query: string;
  onQueryChange: (query: string) => void;
  children: ReactNode;
}

export function AppShell({
  workspace,
  activeView,
  onViewChange,
  query,
  onQueryChange,
  children,
}: AppShellProps) {
  return (
    <div className={styles.appShell}>
      <a className={styles.skipLink} href="#control-plane-main">Skip to content</a>
      <aside className={styles.sidebar}>
        <div className={styles.productMark}>
          <span className={styles.productIcon}><Boxes size={19} aria-hidden="true" /></span>
          <span><strong>OntoWiz</strong><small>Context Foundry</small></span>
        </div>

        <nav className={styles.navigation} aria-label="Control plane">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                type="button"
                key={item.id}
                className={activeView === item.id ? styles.navActive : styles.navItem}
                onClick={() => onViewChange(item.id)}
                aria-current={activeView === item.id ? 'page' : undefined}
              >
                <Icon size={17} aria-hidden="true" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className={styles.sidebarFooter}>
          <span className={styles.syntheticDot} />
          <span><strong>Synthetic reference</strong><small>Production ineligible</small></span>
        </div>
      </aside>

      <div className={styles.workspace}>
        <header className={styles.topbar}>
          <div className={styles.contextSelectors}>
            <label>
              <span>Client / pack</span>
              <span className={styles.selectWrap}>
                <select aria-label="Client and pack" defaultValue="auravia">
                  <option value="auravia">{workspace.client} | Auravia</option>
                </select>
                <ChevronDown size={14} aria-hidden="true" />
              </span>
            </label>
            <div className={styles.contextDivider} />
            <div className={styles.environmentLabel}>
              <span>Environment</span>
              <strong><span className={styles.candidateDot} /> Candidate</strong>
            </div>
          </div>

          <div className={styles.topbarActions}>
            <label className={styles.globalSearch}>
              <Search size={15} aria-hidden="true" />
              <span className={styles.srOnly}>Search context</span>
              <input
                value={query}
                onChange={(event) => onQueryChange(event.target.value)}
                onFocus={() => onViewChange('knowledge')}
                placeholder="Search artifacts, metrics, policies..."
              />
              <kbd>/</kbd>
            </label>
            <label className={styles.roleSelect}>
              <UserRound size={15} aria-hidden="true" />
              <span className={styles.srOnly}>Active role</span>
              <select aria-label="Active role" defaultValue="owner">
                <option value="owner">Pack owner</option>
                <option value="curator">Curator</option>
                <option value="mlr">MLR reviewer</option>
                <option value="data">Data steward</option>
              </select>
              <ChevronDown size={13} aria-hidden="true" />
            </label>
          </div>
        </header>

        <main id="control-plane-main" className={styles.mainContent}>{children}</main>
      </div>
    </div>
  );
}
