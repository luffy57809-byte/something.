import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { startDetection, getDetectionStatus } from '../api';
import './CheatDetection.css';

const VERDICT_CONFIG = {
  'clean': { color: '#7fc98f', emoji: '✅', label: 'No unusual patterns' },
  'suspicious': { color: '#f0a04b', emoji: '⚠️', label: 'Some unusual patterns' },
  'likely cheating': { color: '#f0766b', emoji: '🚨', label: 'Highly unusual play' },
};

export default function CheatDetection() {
  const { user } = useAuth();
  const [chessUsername, setChessUsername] = useState('');
  const [source, setSource] = useState('chesscom');
  const [maxGames, setMaxGames] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [expandedGame, setExpandedGame] = useState(null);
  const [progress, setProgress] = useState(null);
  const [partial, setPartial] = useState([]);
  const cancelled = useRef(false);

  useEffect(() => {
    cancelled.current = false;
    return () => { cancelled.current = true; };
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setResult(null);
    setPartial([]);
    setProgress(null);
    setLoading(true);
    try {
      const start = await startDetection(chessUsername, maxGames, source);
      const jobId = start.data.job_id;
      let failures = 0;
      for (;;) {
        await new Promise((r) => setTimeout(r, 2500));
        if (cancelled.current) return;
        let st;
        try {
          st = (await getDetectionStatus(jobId)).data;
          failures = 0;
        } catch (err) {
          failures += 1;
          if ((err.response && err.response.status === 404) || failures >= 5) throw err;
          continue;
        }
        setProgress({ total: st.total, state: st.state, position: st.position });
        setPartial(st.reports);
        if (st.state === 'done') {
          setResult({
            username: st.username,
            games_analyzed: st.games_analyzed,
            average_score: st.average_score,
            overall_verdict: st.overall_verdict,
            reports: st.reports,
          });
          break;
        }
        if (st.state === 'error') {
          setError(st.error || 'Detection failed');
          break;
        }
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Detection failed');
    } finally {
      setLoading(false);
      setProgress(null);
    }
  };

  const verdictConfig = result ? VERDICT_CONFIG[result.overall_verdict] : null;

  return (
    <div className="cheat-detection">
      <div className="detection-header">
        <h1>🔍 Cheat Detection</h1>
        <p>Analyze a player's games for suspicious patterns using engine match rate, move timing, and statistical analysis.</p>
      </div>

      <div className="card">
        <h2>Analyze Player</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Chess Username</label>
            <input
              type="text"
              value={chessUsername}
              onChange={(e) => setChessUsername(e.target.value)}
              placeholder="e.g. Walid_150"
              required
            />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Platform</label>
              <select value={source} onChange={(e) => setSource(e.target.value)}>
                <option value="chesscom">Chess.com</option>
                <option value="lichess">Lichess</option>
              </select>
            </div>
            <div className="form-group">
              <label>Games to analyze</label>
              <div className="game-count-options">
                {[3, 5, 10].map((n) => (
                  <button
                    key={n}
                    type="button"
                    className={`count-btn ${maxGames === n ? 'active' : ''}`}
                    onClick={() => setMaxGames(n)}
                  >
                    {n}
                  </button>
                ))}
              </div>
            </div>
          </div>
          {error && <p className="error">{error}</p>}
          <button className="btn btn-primary" type="submit" disabled={loading}>
            {loading ? 'Analyzing...' : 'Run Detection'}
          </button>
        </form>
      </div>

      {loading && progress && (
        <div className="card">
          <p>
            {progress.state === 'queued'
              ? (progress.position > 0
                  ? `Waiting in line: ${progress.position} ahead of you...`
                  : 'Starting...')
              : `Analyzing game ${Math.min(partial.length + 1, progress.total)} of ${progress.total}...`}
          </p>
          <div className="verdict-score-bar">
            <div
              className="verdict-score-fill"
              style={{
                width: `${(partial.length / progress.total) * 100}%`,
                background: 'var(--brass)',
              }}
            />
          </div>
          {partial.map((r, i) => (
            <p key={i} className="feature-note">
              Game {i + 1} ({r.color}): score {r.overall_score}
            </p>
          ))}
        </div>
      )}

      {result && verdictConfig && (
        <>
          <div className="verdict-card" style={{ borderColor: verdictConfig.color }}>
            <div className="verdict-emoji">{verdictConfig.emoji}</div>
            <div className="verdict-info">
              <div className="verdict-label" style={{ color: verdictConfig.color }}>
                {verdictConfig.label}
              </div>
              <div className="verdict-username">{result.username}</div>
              <div className="verdict-detail">
                Score: <strong>{result.average_score}/100</strong> across {result.games_analyzed} games
              </div>
            </div>
            <div className="verdict-score-bar">
              <div
                className="verdict-score-fill"
                style={{
                  width: `${result.average_score}%`,
                  background: verdictConfig.color,
                }}
              />
            </div>
          </div>

          <div className="card">
            <h2>Game Breakdown</h2>
            {result.reports.map((report, i) => {
              const cfg = VERDICT_CONFIG[report.verdict] || VERDICT_CONFIG['clean'];
              const isExpanded = expandedGame === i;
              return (
                <div key={i} className="game-report-row">
                  <div
                    className="game-report-header"
                    onClick={() => setExpandedGame(isExpanded ? null : i)}
                  >
                    <span className="game-report-id">Game {i + 1}</span>
                    <span className="game-report-color">({report.color})</span>
                    <span className="game-report-score">
                      Score: <strong>{report.overall_score}</strong>
                    </span>
                    <span
                      className="game-report-verdict"
                      style={{ color: cfg.color }}
                    >
                      {cfg.emoji} {cfg.label}
                    </span>
                    <span className="expand-icon">{isExpanded ? '▲' : '▼'}</span>
                  </div>

                  {isExpanded && (
                    <div className="game-report-details">
                      <table className="features-table">
                        <thead>
                          <tr>
                            <th>Feature</th>
                            <th>Score</th>
                            <th>Detail</th>
                          </tr>
                        </thead>
                        <tbody>
                          {report.features.map((f, j) => (
                            <tr key={j}>
                              <td>{f.name}</td>
                              <td>
                                <div className="feature-score-bar">
                                  <div
                                    className="feature-score-fill"
                                    style={{
                                      width: `${f.score}%`,
                                      background: f.score > 60 ? '#f0766b'
                                        : f.score > 30 ? '#f0a04b' : '#7fc98f'
                                    }}
                                  />
                                  <span>{f.score.toFixed(1)}</span>
                                </div>
                              </td>
                              <td className="feature-note">{f.note}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      {report.flagged_moves.length > 0 && (
                        <p className="flagged-moves">
                          🚩 Flagged plies: {report.flagged_moves.join(', ')}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
