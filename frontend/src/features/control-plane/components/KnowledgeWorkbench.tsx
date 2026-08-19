'use client';

import { useEffect, useMemo, useState } from 'react';
import {
  BookOpen,
  ChevronRight,
  Database,
  FileSearch,
  GitCommitHorizontal,
  Link2,
  LoaderCircle,
  Search,
  ShieldCheck,
  Tags,
} from 'lucide-react';

import { httpControlPlaneClient } from '../api';
import styles from '../control-plane.module.css';
import type { ArtifactDetail, ArtifactKind, ControlPlaneSnapshot } from '../types';
import { EmptyState, humanize, SectionTitle, StatusPill } from './Primitives';

type WorkbenchMode = 'artifacts' | 'sources';
type KindFilter = 'all' | ArtifactKind;

interface KnowledgeWorkbenchProps {
  snapshot: ControlPlaneSnapshot;
  query: string;
  onQueryChange: (query: string) => void;
  selectedId: string;
  onSelectedIdChange: (artifactId: string) => void;
  corrected: boolean;
}

const kindOptions: Array<{ id: KindFilter; label: string }> = [
  { id: 'all', label: 'All' },
  { id: 'claim', label: 'Claims' },
  { id: 'business_rule', label: 'Rules' },
  { id: 'metric', label: 'Metrics' },
  { id: 'table_contract', label: 'Tables' },
  { id: 'governed_join', label: 'Joins' },
];

export function KnowledgeWorkbench({
  snapshot,
  query,
  onQueryChange,
  selectedId,
  onSelectedIdChange,
  corrected,
}: KnowledgeWorkbenchProps) {
  const [mode, setMode] = useState<WorkbenchMode>('artifacts');
  const [kind, setKind] = useState<KindFilter>('all');
  const [detail, setDetail] = useState<ArtifactDetail | null>(null);
  const [detailFailure, setDetailFailure] = useState<{ artifactId: string; message: string } | null>(null);
  const detailLoading = detail?.id !== selectedId && detailFailure?.artifactId !== selectedId;
  const detailError = detailFailure?.artifactId === selectedId ? detailFailure.message : '';

  const [selectedSourceId, setSelectedSourceId] = useState(snapshot.sources[0]?.id ?? '');

  useEffect(() => {
    let active = true;


    httpControlPlaneClient.getArtifact(selectedId)
      .then((response) => { if (active) setDetail(response.data); })
      .catch((error: unknown) => {
        if (active) setDetailFailure({
          artifactId: selectedId,
          message: error instanceof Error ? error.message : 'Artifact detail could not be loaded.',
        });
      })
      ;
    return () => { active = false; };
  }, [selectedId]);

  const artifacts = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return snapshot.artifacts.filter((item) => {
      const kindMatches = kind === 'all' || item.kind === kind;
      const queryMatches = !needle || [item.id, item.name, item.domain, item.shortDefinition, ...item.tags]
        .some((value) => value.toLowerCase().includes(needle));
      return kindMatches && queryMatches;
    });
  }, [kind, query, snapshot.artifacts]);

  const selectedSource = snapshot.sources.find((source) => source.id === selectedSourceId) ?? snapshot.sources[0];

  return (
    <div className={styles.viewStack}>
      <SectionTitle
        eyebrow="Knowledge workbench"
        title="Inspect the compiled context"
        description="Trace definitions to exact evidence, scope, relationships, data contracts and consumers."
        action={
          <div className={styles.segmentedControl} aria-label="Knowledge view">
            <button type="button" className={mode === 'artifacts' ? styles.segmentActive : ''} onClick={() => setMode('artifacts')}><BookOpen size={14} /> Artifacts</button>
            <button type="button" className={mode === 'sources' ? styles.segmentActive : ''} onClick={() => setMode('sources')}><Database size={14} /> Sources</button>
          </div>
        }
      />

      {mode === 'artifacts' ? (
        <>
          <div className={styles.catalogToolbar}>
            <label className={styles.catalogSearch}>
              <Search size={15} aria-hidden="true" />
              <span className={styles.srOnly}>Search artifacts</span>
              <input value={query} onChange={(event) => onQueryChange(event.target.value)} placeholder="Search ID, definition, tag or owner" />
            </label>
            <div className={styles.filterRail} aria-label="Artifact type">
              {kindOptions.map((option) => <button type="button" key={option.id} onClick={() => setKind(option.id)} className={kind === option.id ? styles.filterActive : ''}>{option.label}</button>)}
            </div>
            <span className={styles.resultCount}>{artifacts.length} shown</span>
          </div>

          <div className={styles.workbenchGrid}>
            <section className={styles.catalogTableWrap} aria-label="Compiled artifacts">
              <div className={styles.catalogHeader}>
                <span>Artifact</span><span>Domain / type</span><span>State</span><span>Evals</span><span />
              </div>
              <div className={styles.catalogRows}>
                {artifacts.map((item) => {
                  const isCorrectedVariant = corrected && item.id === 'claim_variant_easi75_us_hcp_v1';
                  return (
                    <button
                      type="button"
                      className={selectedId === item.id ? styles.catalogRowActive : styles.catalogRow}
                      key={item.id}
                      onClick={() => onSelectedIdChange(item.id)}
                    >
                      <span><strong>{item.name}</strong><code>{item.id}</code></span>
                      <span><strong>{item.domain}</strong><small>{humanize(item.kind)}</small></span>
                      <span><StatusPill status={isCorrectedVariant ? 'candidate' : item.status} label={isCorrectedVariant ? 'Corrected rc2' : undefined} /></span>
                      <span className={styles.evalCell}><b>{isCorrectedVariant ? item.evalTotal : item.evalPassed}/{item.evalTotal}</b><small>passing</small></span>
                      <ChevronRight size={15} aria-hidden="true" />
                    </button>
                  );
                })}
                {artifacts.length === 0 && <EmptyState>No artifacts match this search and type filter.</EmptyState>}
              </div>
            </section>

            <aside className={styles.inspector} aria-label="Artifact inspector">
              {detailLoading && <div className={styles.loadingInline}><LoaderCircle className={styles.spin} size={18} /> Loading governed detail...</div>}
              {detailError && <EmptyState>{detailError}</EmptyState>}
              {!detailLoading && !detailError && detail && (
                <>
                  <div className={styles.inspectorHeader}>
                    <div><span className={styles.eyebrow}>{humanize(detail.kind)}</span><h3>{detail.name}</h3><code>{detail.id} | v{detail.version}</code></div>
                    <StatusPill status={corrected && detail.id === 'claim_variant_easi75_us_hcp_v1' ? 'candidate' : detail.status} label={corrected && detail.id === 'claim_variant_easi75_us_hcp_v1' ? 'Corrected rc2' : undefined} />
                  </div>

                  {corrected && detail.id === 'claim_variant_easi75_us_hcp_v1' && (
                    <div className={styles.correctionNotice}><ShieldCheck size={16} /><span><strong>Semantic invariant restored</strong><small>timepoint_week_16 is present; affected evaluations passed.</small></span></div>
                  )}

                  <div className={styles.inspectorSection}>
                    <h4><BookOpen size={14} /> Semantic definition</h4>
                    <p className={styles.definitionText}>{detail.semanticDefinition}</p>
                    <div className={styles.fieldGrid}>{detail.fields.map((field) => <div key={field.label}><span>{field.label}</span><strong>{field.value}</strong></div>)}</div>
                  </div>

                  <div className={styles.inspectorSection}>
                    <h4><Tags size={14} /> Applicability and limits</h4>
                    <div className={styles.scopeColumns}>
                      <div><span>Permitted scope</span>{detail.applicability.map((item) => <p key={item}>+ {item}</p>)}</div>
                      <div><span>Prohibited</span>{detail.prohibitedUses.map((item) => <p key={item}>- {item}</p>)}</div>
                    </div>
                  </div>

                  <div className={styles.inspectorSection}>
                    <h4><FileSearch size={14} /> Exact evidence</h4>
                    {detail.evidence.length === 0 ? <p className={styles.mutedCopy}>No material evidence span is required for this artifact kind.</p> : detail.evidence.map((evidence) => (
                      <article className={styles.evidenceBlock} key={`${evidence.sourceId}-${evidence.locator}`}>
                        <div><strong>{evidence.sourceName}</strong><StatusPill status={evidence.authority === 'authoritative' ? 'current' : 'candidate'} label={evidence.authority} /></div>
                        <code>{evidence.locator} | {evidence.version}</code>
                        <blockquote>{evidence.excerpt}</blockquote>
                      </article>
                    ))}
                  </div>

                  <div className={styles.inspectorSection}>
                    <h4><Link2 size={14} /> Relationships</h4>
                    <div className={styles.relationshipList}>{detail.relationships.length === 0 ? <p className={styles.mutedCopy}>No compiled relationships in this view.</p> : detail.relationships.map((relation) => <button type="button" key={`${relation.predicate}-${relation.targetId}`} onClick={() => onSelectedIdChange(relation.targetId)}><span>{relation.predicate}</span><strong>{relation.targetName}</strong><ChevronRight size={13} /></button>)}</div>
                  </div>

                  <div className={styles.inspectorSection}>
                    <h4><GitCommitHorizontal size={14} /> Lineage and receipts</h4>
                    <div className={styles.lineageList}>{detail.lineage.map((step) => <div key={step.receipt}><i /><span><strong>{step.stage}</strong><small>{step.artifact} | {step.at}</small></span><code>{step.receipt}</code></div>)}</div>
                  </div>
                </>
              )}
            </aside>
          </div>
        </>
      ) : (
        <div className={styles.sourceWorkbench}>
          <section className={styles.sourceRegistry} aria-label="Source registry">
            <div className={styles.catalogHeader}><span>Source</span><span>Authority</span><span>State</span><span>Parsed</span></div>
            {snapshot.sources.map((source) => (
              <button type="button" key={source.id} className={selectedSource?.id === source.id ? styles.sourceRowActive : styles.sourceRow} onClick={() => setSelectedSourceId(source.id)}>
                <span><strong>{source.name}</strong><code>{source.id} | {source.version}</code></span>
                <span>{humanize(source.authority)}</span>
                <StatusPill status={source.state} />
                <span><b>{source.parsed}%</b><small>{source.lastChecked}</small></span>
              </button>
            ))}
          </section>
          <aside className={styles.sourcePreview}>
            {selectedSource && (
              <>
                <div className={styles.inspectorHeader}><div><span className={styles.eyebrow}>Immutable source instance</span><h3>{selectedSource.name}</h3><code>{selectedSource.id} | {selectedSource.version}</code></div><StatusPill status={selectedSource.state} /></div>
                <div className={styles.sourceMetaGrid}><div><span>Authority</span><strong>{humanize(selectedSource.authority)}</strong></div><div><span>Parse coverage</span><strong>{selectedSource.parsed}%</strong></div><div><span>Last checked</span><strong>{selectedSource.lastChecked}</strong></div></div>
                <div className={styles.documentPreview}>
                  <div className={styles.documentToolbar}><span>Structured evidence preview</span><code>READ ONLY</code></div>
                  <h4>Synthetic efficacy summary</h4>
                  <p>In the synthetic VELA-1 fixture, trial-eligible adults were evaluated against the fictional EASI-75 endpoint.</p>
                  <p className={styles.highlightSpan}>At week 16, 62% receiving fictional Auravia achieved EASI-75, compared with 28% receiving placebo.</p>
                  <p>This fixture is synthetic and must not be used for real clinical, promotional or patient-level decisions.</p>
                </div>
                <div className={styles.extractionSummary}><div><strong>3</strong><span>accepted candidates</span></div><div><strong>1</strong><span>needs SME review</span></div><div><strong>0</strong><span>released automatically</span></div></div>
              </>
            )}
          </aside>
        </div>
      )}
    </div>
  );
}
