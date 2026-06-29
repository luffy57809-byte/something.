import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { analyzeGames, getUserGames, getUserStats, clearCache } from '../api';
import { useAuth } from '../context/AuthContext';
import './Dashboard.css';

function getResultClass(game, chessUsername) {
  const isWhite = game.white.toLowerCase() === chessUsername.toLowerCase();
  if (game.result === '1-0') return isWhite ? 'result-win' : 'result-loss';
  if (game.result === '0-1') return isWhite ? 'result-loss' : 'result-win';
  return 'result-draw';
}

export default function Dashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [chessUsername, setChessUsername] = useState('');
  const [source, setSource] = useState('chesscom');
  const [maxGames, setMaxGames] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [stats, setStats] = useState(null);
  const [games, setGames] = useState([]);
  const [analyzed, setAnalyzed] = useState(false);
  const [analyzedUsername, setAnalyzedUsername] = useState('');

  const handleRefresh = async () => {
    setError('');
    setLoading(true);
    try {
      await clearCache(chessUsername);
      await analyzeGames(chessUsername, source, maxGames);
      const [statsRes, gamesRes] = await Promise.all([
        getUserStats(chessUsername),
        getUserGames(chessUsername),
      ]);
      setStats(statsRes.data.stats);
      setGames(gamesRes.data.games);
      setAnalyzedUsername(chessUsername);
      setAnalyzed(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Refresh failed');
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await analyzeGames(chessUsername, source, maxGames);
      const [statsRes, gamesRes] = await Promise.all([
        getUserStats(chessUsername),
        getUserGames(chessUsername),
      ]);
      setStats(statsRes.data.stats);
      setGames(gamesRes.data.games);
      setAnalyzedUsername(chessUsername);
      setAnalyzed(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Welcome back, {user.username}</h1>
        <p>Analyze your games and track your improvement</p>
      </div>

      <div className="card">
        <h2>Analyze Games</h2>
        <form className="analyze-form" onSubmit={handleAnalyze}>
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
              <select value={maxGames}
                onChange={(e) => setMaxGames(Number(e.target.value))}>
                <option value={3}>3 games</option>
                <option value={5}>5 games</option>
                {user.is_premium && <option value={10}>10 games</option>}
                {user.is_premium && <option value={20}>20 games</option>}
              </select>
            </div>
          </div>
          {error && <p className="error">{error}</p>}
          <button className="btn btn-primary" type="submit" disabled={loading}>
            {loading ? 'Analyzing... (this may take a minute)' : 'Analyze Games'}
          </button>
          {analyzed && (
            <button className='btn btn-ghost' type='button' onClick={handleRefresh} disabled={loading} style={{marginTop: '0.5rem'}}>
              🔄 Refresh (fetch latest games)
            </button>
          )}
        </form>
      </div>

      {analyzed && stats && (
        <>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-value">{stats.accuracy_pct}%</div>
              <div className="stat-label">Accuracy</div>
            </div>
            <div className="stat-card">
              <div className="stat-value blunder">{stats.blunders}</div>
              <div className="stat-label">Blunders</div>
            </div>
            <div className="stat-card">
              <div className="stat-value mistake">{stats.mistakes}</div>
              <div className="stat-label">Mistakes</div>
            </div>
            <div className="stat-card">
              <div className="stat-value inaccuracy">{stats.inaccuracies}</div>
              <div className="stat-label">Inaccuracies</div>
            </div>
          </div>

          {stats.top_weakness && (
            <div className="card weakness-card">
              <h2>Top Weakness</h2>
              <p className="weakness-text">
                ⚠️ You most often struggle with{' '}
                <strong>{stats.top_weakness.replace(/_/g, ' ')}</strong>.
                Head to the{' '}
                <span className="link" onClick={() => navigate('/puzzles')}>
                  Puzzle Trainer
                </span>{' '}
                to work on this.
              </p>
            </div>
          )}

          <div className="card">
            <h2>Recent Games</h2>
            <div className="games-list">
              {games.map((g) => (
                <div
                  key={g.game_id}
                  className="game-row"
                  onClick={() =>
                    navigate(`/game/${encodeURIComponent(g.game_id)}`)
                  }
                >
                  <div className="game-players">
                    {g.white} vs {g.black}
                  </div>
                  <div className="game-meta">
                    <span className={`result ${getResultClass(g, analyzedUsername)}`}>
                      {g.result}
                    </span>
                    <span className="game-date">{g.date}</span>
                    <span className="game-tc">{g.time_control}s</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
