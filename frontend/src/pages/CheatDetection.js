import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { detectCheating } from '../api';
import './CheatDetection.css';

const VERDICT_CONFIG = {
  'clean': { color: '#22c55e', emoji: '✅', label: 'Clean' },
  'suspicious': { color: '#f97316', emoji: '⚠️', label: 'Suspicious' },
  'likely cheating': { color: '#ef4444', emoji: '🚨', label: 'Likely Cheating' },
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

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setResult(null);
    setLoading(true);
    try {
      const res = await detectCheating(chessUsername, maxGames, source);
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Detection failed');
    } finally {
      setLoading(false);
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
            {loading ? 'Analyzing... (this may take a few minutes)' : 'Run Detection'}
          </button>
        </form>
      </div>

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
                                      background: f.score > 60 ? '#ef4444'
                                        : f.score > 30 ? '#f97316' : '#22c55e'
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
