'use client';

import { useState } from 'react';

import type { ArtifactView, Comment } from '@/types/catalog';

interface Props {
  artifact: ArtifactView;
  comments: Comment[];
  canReview: boolean;
  onClose: () => void;
  onPostComment: (text: string) => void;
  onReview: (decision: string) => void;
}

/** Slide-over with the artifact's verdict, anti-patterns, governance trail, raw
 * YAML, discussion, and (for curators/managers) a review action. */
export default function ArtifactDrawer({
  artifact, comments, canReview, onClose, onPostComment, onReview,
}: Props) {
  const [draft, setDraft] = useState('');

  const post = () => {
    const text = draft.trim();
    if (text) {
      onPostComment(text);
      setDraft('');
    }
  };

  return (
    <aside
      role="dialog"
      aria-label={`Artifact ${artifact.id}`}
      className="fixed right-0 top-0 h-full w-[min(540px,94vw)] overflow-auto border-l border-slate-700 bg-slate-950 p-6"
    >
      <button type="button" onClick={onClose} aria-label="Close" className="float-right text-slate-500">
        ✕
      </button>
      <div className="text-xs text-slate-500">{artifact.id}</div>
      <h2 className="my-1 text-xl font-semibold text-slate-100">{artifact.name}</h2>

      <div className="mt-2 flex flex-wrap gap-1.5">
        {artifact.tags.map((t) => (
          <span key={`${t.dimension}:${t.value}`} className="rounded-full border border-slate-700 px-2 py-0.5 text-[11px] text-slate-300">
            {t.dimension}:{t.value}
          </span>
        ))}
      </div>

      <h3 className="mt-4 font-semibold text-slate-200">Concludes</h3>
      <div className="rounded-lg border border-slate-700 bg-slate-900 p-3 text-slate-200">{artifact.summary}</div>

      {artifact.anti_patterns.map((a, i) => (
        <p key={i} className="mt-2 border-l-2 border-rose-500 pl-2 text-sm text-slate-400">
          <b>Not →</b> {a.wrong_conclusion}. {a.why_wrong}
        </p>
      ))}

      <h3 className="mt-4 font-semibold text-slate-200">Governance</h3>
      {artifact.governance.map((g, i) => (
        <div key={i} className="text-sm text-slate-400">
          → {g.to_state} by {g.changed_by}{g.delta_id ? ` · ${g.delta_id}` : ''}
        </div>
      ))}

      <h3 className="mt-4 font-semibold text-slate-200">YAML</h3>
      <pre className="overflow-auto rounded-lg border border-slate-800 bg-black p-3 text-xs text-slate-300">{artifact.yaml}</pre>

      <h3 className="mt-4 font-semibold text-slate-200">Discussion · {comments.length}</h3>
      <div>
        {comments.length === 0 && <p className="text-sm text-slate-500">No comments yet.</p>}
        {comments.map((c, i) => (
          <div key={i} className="mt-2 text-sm text-slate-400">
            <b className="text-slate-200">{c.author}</b>{' '}
            <span className="rounded-full border border-slate-700 px-1.5 text-[11px]">{c.role}</span> — {c.text}
          </div>
        ))}
      </div>

      <div className="mt-3 flex gap-2">
        <input
          aria-label="Comment"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Add a comment…"
          className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-1.5 text-sm text-slate-100"
        />
        <button type="button" onClick={post} className="rounded-lg border border-slate-700 px-3 text-sm text-slate-200">
          Post
        </button>
      </div>

      {canReview && (
        <div className="mt-4 flex gap-2">
          <button type="button" onClick={() => onReview('approve')} className="rounded-lg border border-emerald-600/40 px-3 py-1.5 text-sm text-emerald-400">
            Approve
          </button>
          <button type="button" onClick={() => onReview('request_changes')} className="rounded-lg border border-amber-600/40 px-3 py-1.5 text-sm text-amber-400">
            Request changes
          </button>
        </div>
      )}
    </aside>
  );
}
