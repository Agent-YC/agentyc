import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchAgent, fetchEvals, sendCoachMessage } from '../api';
import type { Agent, EvalRecord } from '../api';

/* ── Scorecard bar ─────────────────────────────────────────── */
function ScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div style={{ marginBottom: '1.25rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
        <span className="text-sm font-medium">{label}</span>
        <span className="text-sm text-accent font-bold">{value}</span>
      </div>
      <div className="progress-bg">
        <div className="progress-fill" style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}

/* ── Chat message ──────────────────────────────────────────── */
interface ChatMsg {
  role: 'user' | 'partner';
  text: string;
}

export default function AgentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [agent, setAgent] = useState<Agent | null>(null);
  const [evals, setEvals] = useState<EvalRecord[]>([]);
  const [loading, setLoading] = useState(true);

  // Coach chat
  const [messages, setMessages] = useState<ChatMsg[]>([
    { role: 'partner', text: 'Hey founder — I\'m your YC partner. Ask me anything about your agent\'s performance.' },
  ]);
  const [draft, setDraft] = useState('');
  const [sending, setSending] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!id) return;
    Promise.all([fetchAgent(id), fetchEvals(id)])
      .then(([a, e]) => {
        setAgent(a);
        setEvals(e);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!draft.trim() || !id) return;
    const userMsg = draft.trim();
    setDraft('');
    setMessages((m) => [...m, { role: 'user', text: userMsg }]);
    setSending(true);
    try {
      const reply = await sendCoachMessage(id, userMsg);
      setMessages((m) => [...m, { role: 'partner', text: reply }]);
    } catch {
      setMessages((m) => [...m, { role: 'partner', text: 'Connection error — is Ollama running?' }]);
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return <div className="page-center"><span className="text-muted">Loading…</span></div>;
  }

  if (!agent) {
    return (
      <div className="page-center">
        <div className="card" style={{ textAlign: 'center' }}>
          <p>Agent not found.</p>
          <button className="btn" onClick={() => navigate('/')} style={{ marginTop: '1rem' }}>← Back</button>
        </div>
      </div>
    );
  }

  const latest = evals[0] || null;

  return (
    <div>
      {/* Header */}
      <button
        className="btn"
        onClick={() => navigate('/')}
        style={{ marginBottom: '1.5rem', padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}
      >
        ← All Agents
      </button>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1 className="text-2xl" style={{ marginBottom: '0.15rem' }}>{agent.name}</h1>
          <p className="text-secondary text-sm">{agent.author || 'Unknown'} · {agent.status}</p>
        </div>
        {latest && (
          <div style={{ textAlign: 'right' }}>
            <div className="text-accent font-bold" style={{ fontSize: '2.5rem', lineHeight: 1 }}>
              {latest.score_overall}
            </div>
            <span className="text-muted text-xs">overall</span>
          </div>
        )}
      </div>

      {agent.description && (
        <p className="text-sm text-secondary" style={{ marginBottom: '2rem' }}>{agent.description}</p>
      )}

      {/* Two-column layout */}
      <div className="grid-2" style={{ alignItems: 'start' }}>
        {/* Scorecard */}
        <div className="card">
          <h3 className="text-base font-medium" style={{ marginBottom: '1.5rem' }}>Scorecard</h3>
          {latest ? (
            <>
              <ScoreBar label="Reliability" value={latest.score_reliability} />
              <ScoreBar label="Safety" value={latest.score_safety} />
              <ScoreBar label="Cost" value={latest.score_cost} />
              <ScoreBar label="Speed" value={latest.score_speed} />
            </>
          ) : (
            <p className="text-muted text-sm">No evaluations yet. Run <code style={{ color: 'var(--accent)' }}>agent-yc eval</code>.</p>
          )}

          {/* Challenge breakdown */}
          {latest && latest.challenges && latest.challenges.length > 0 && (
            <div style={{ marginTop: '1.5rem', borderTop: '1px solid var(--border)', paddingTop: '1rem' }}>
              <h4 className="text-sm font-medium text-secondary" style={{ marginBottom: '0.75rem' }}>Challenges</h4>
              {latest.challenges.map((ch, i) => (
                <div
                  key={i}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '0.4rem 0',
                    borderBottom: '1px solid var(--border)',
                  }}
                >
                  <span className="text-sm">{ch.name || ch.id}</span>
                  <span className={`badge ${ch.passed ? 'badge-accent' : 'badge-outline'}`}>
                    {ch.passed ? '✓ pass' : '✗ fail'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Coach Chat */}
        <div className="chat-window">
          <div
            style={{
              padding: '1rem 1.5rem',
              borderBottom: '1px solid var(--border)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
            }}
          >
            <span style={{ fontSize: '1.1rem' }}>🎓</span>
            <span className="text-sm font-medium">YC Partner</span>
          </div>

          <div className="chat-history">
            {messages.map((msg, i) => (
              <div key={i} className={`chat-msg ${msg.role === 'user' ? 'msg-user' : 'msg-partner'}`}>
                <span className="msg-sender">{msg.role === 'user' ? 'You' : 'YC Partner'}</span>
                <div className="msg-bubble">{msg.text}</div>
              </div>
            ))}
            {sending && (
              <div className="chat-msg msg-partner">
                <span className="msg-sender">YC Partner</span>
                <div className="msg-bubble text-muted">Thinking…</div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <div className="chat-input-area">
            <input
              className="input-reset"
              placeholder="Ask your YC partner…"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
              disabled={sending}
            />
            <button className="btn btn-primary" onClick={handleSend} disabled={sending}>
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
