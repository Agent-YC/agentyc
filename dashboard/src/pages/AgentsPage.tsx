import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchAgents } from '../api';
import type { Agent } from '../api';

function gradeFromScore(score: number | null): { letter: string; color: string } {
  if (score === null) return { letter: '—', color: 'var(--text-muted)' };
  if (score >= 90) return { letter: 'A+', color: '#4ade80' };
  if (score >= 80) return { letter: 'A', color: '#86efac' };
  if (score >= 70) return { letter: 'B', color: 'var(--accent)' };
  if (score >= 60) return { letter: 'C', color: '#fb923c' };
  return { letter: 'F', color: '#ef4444' };
}

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchAgents()
      .then(setAgents)
      .catch(() => setError('Could not reach API. Is `agent-yc dashboard` running?'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="page-center"><span className="text-muted">Loading agents…</span></div>;
  }

  if (error) {
    return (
      <div className="page-center">
        <div className="card" style={{ textAlign: 'center', maxWidth: 480 }}>
          <h2 style={{ marginBottom: '0.5rem' }}>No connection</h2>
          <p className="text-secondary text-sm">{error}</p>
        </div>
      </div>
    );
  }

  if (agents.length === 0) {
    return (
      <div className="page-center">
        <div className="card" style={{ textAlign: 'center', maxWidth: 480 }}>
          <h2 style={{ marginBottom: '0.5rem' }}>No agents yet</h2>
          <p className="text-secondary text-sm">
            Run <code style={{ color: 'var(--accent)' }}>agent-yc init</code> and{' '}
            <code style={{ color: 'var(--accent)' }}>agent-yc eval</code> to get started.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h1 className="text-2xl" style={{ marginBottom: '0.25rem' }}>Your Agents</h1>
        <p className="text-secondary text-sm">{agents.length} agent{agents.length !== 1 ? 's' : ''} submitted</p>
      </div>

      <div className="grid-2">
        {agents.map((agent) => {
          const grade = gradeFromScore(agent.score_overall);
          return (
            <div
              key={agent.id}
              className="card clickable"
              onClick={() => navigate(`/agents/${agent.id}`)}
              style={{ cursor: 'pointer' }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <h3 className="text-lg" style={{ marginBottom: '0.25rem' }}>{agent.name}</h3>
                  <p className="text-secondary text-xs" style={{ marginBottom: '0.75rem' }}>
                    {agent.author || 'Unknown author'} · {agent.status}
                  </p>
                </div>
                <div
                  style={{
                    fontSize: '1.75rem',
                    fontWeight: 800,
                    color: grade.color,
                    lineHeight: 1,
                  }}
                >
                  {grade.letter}
                </div>
              </div>

              {agent.description && (
                <p className="text-sm text-muted" style={{ marginBottom: '1rem' }}>
                  {agent.description.slice(0, 120)}
                  {agent.description.length > 120 ? '…' : ''}
                </p>
              )}

              {agent.score_overall !== null && (
                <div className="progress-bg">
                  <div className="progress-fill" style={{ width: `${agent.score_overall}%` }} />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
