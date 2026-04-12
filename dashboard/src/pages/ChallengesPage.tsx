import { useEffect, useState } from 'react';
import { fetchChallenges } from '../api';
import type { ChallengeSpec } from '../api';

const DIFFICULTY_COLORS: Record<string, string> = {
  easy: '#4ade80',
  medium: 'var(--accent)',
  hard: '#fb923c',
  extreme: '#ef4444',
};

const CATEGORY_LABELS: Record<string, string> = {
  reliability: '🔒 Reliability',
  cost: '💰 Cost',
  safety: '🛡️ Safety',
  speed: '⚡ Speed',
};

export default function ChallengesPage() {
  const [challenges, setChallenges] = useState<ChallengeSpec[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');

  useEffect(() => {
    fetchChallenges()
      .then(setChallenges)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const categories = ['all', ...Array.from(new Set(challenges.map((c) => c.category)))];
  const filtered = filter === 'all' ? challenges : challenges.filter((c) => c.category === filter);

  if (loading) {
    return <div className="page-center"><span className="text-muted">Loading challenges…</span></div>;
  }

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h1 className="text-2xl" style={{ marginBottom: '0.25rem' }}>Challenge Registry</h1>
        <p className="text-secondary text-sm">
          {challenges.length} challenges across {categories.length - 1} categories
        </p>
      </div>

      {/* Filter pills */}
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        {categories.map((cat) => (
          <button
            key={cat}
            className={`btn ${cat === filter ? 'btn-primary' : ''}`}
            onClick={() => setFilter(cat)}
            style={{ padding: '0.4rem 0.9rem', fontSize: '0.8rem' }}
          >
            {cat === 'all' ? 'All' : CATEGORY_LABELS[cat] || cat}
          </button>
        ))}
      </div>

      {/* Challenge grid */}
      <div className="grid-2">
        {filtered.map((ch) => (
          <div key={ch.id} className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
              <h3 className="text-base font-medium" style={{ margin: 0 }}>{ch.name}</h3>
              <span
                className="badge"
                style={{
                  color: DIFFICULTY_COLORS[ch.difficulty] || 'var(--text-muted)',
                  borderColor: DIFFICULTY_COLORS[ch.difficulty] || 'var(--border)',
                  border: '1px solid',
                }}
              >
                {ch.difficulty}
              </span>
            </div>
            <span className="text-xs text-muted" style={{ display: 'block', marginBottom: '0.75rem' }}>
              {CATEGORY_LABELS[ch.category] || ch.category} · {ch.id}
            </span>
            {ch.description && (
              <p className="text-sm text-secondary" style={{ margin: 0 }}>
                {ch.description.slice(0, 160)}{ch.description.length > 160 ? '…' : ''}
              </p>
            )}
          </div>
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="card" style={{ textAlign: 'center', marginTop: '2rem' }}>
          <p className="text-muted">No challenges match this filter.</p>
        </div>
      )}

      {/* Community CTA */}
      <div className="card" style={{ marginTop: '3rem', textAlign: 'center' }}>
        <h3 className="text-lg" style={{ marginBottom: '0.5rem' }}>Contribute a Challenge</h3>
        <p className="text-secondary text-sm" style={{ maxWidth: 460, margin: '0 auto 1rem' }}>
          Drop a YAML file into <code style={{ color: 'var(--accent)' }}>/challenges/</code> and open a PR.
          Community-authored challenges help every agent builder.
        </p>
        <a
          href="https://github.com/agent-yc/agent-yc/tree/main/challenges"
          target="_blank"
          rel="noreferrer"
          className="btn btn-primary"
        >
          View on GitHub →
        </a>
      </div>
    </div>
  );
}
