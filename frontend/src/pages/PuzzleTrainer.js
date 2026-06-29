import React, { useState, useEffect } from 'react';
import ChessBoard from '../components/ChessBoard';
import { getTrainingPuzzles, submitAttempt, getPuzzleStats } from '../api';
import './PuzzleTrainer.css';

export default function PuzzleTrainer() {
  const [chessUsername, setChessUsername] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [puzzles, setPuzzles] = useState([]);
  const [lichessPuzzles, setLichessPuzzles] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [currentType, setCurrentType] = useState('game');
  const [currentFen, setCurrentFen] = useState(null);
  const [moveStatus, setMoveStatus] = useState('');
  const [puzzleStats, setPuzzleStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const currentPuzzle = currentType === 'game'
    ? puzzles[currentIndex]
    : lichessPuzzles[currentIndex];

  useEffect(() => {
    getPuzzleStats().then((res) => setPuzzleStats(res.data.puzzle_stats));
  }, []);

  useEffect(() => {
    if (currentPuzzle) {
      const fen = currentPuzzle.fen_before || currentPuzzle.fen;
      if (fen) setCurrentFen(fen);
      setMoveStatus('');
    }
  }, [currentIndex, currentType, currentPuzzle]);

  const handleLoad = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await getTrainingPuzzles(chessUsername);
      const gamePuzzles = res.data.game_puzzles || [];
      const lichess = res.data.lichess_puzzles || [];
      setPuzzles(gamePuzzles);
      setLichessPuzzles(lichess);
      setCurrentIndex(0);
      setCurrentType(gamePuzzles.length > 0 ? 'game' : 'lichess');
      setSubmitted(true);
      if (gamePuzzles.length === 0 && lichess.length === 0) {
        setError('No puzzles found. Analyze your games on the Dashboard first.');
        setSubmitted(false);
      }
    } catch (err) {
      setError('Failed to load puzzles. Analyze your games on the Dashboard first.');
    } finally {
      setLoading(false);
    }
  };

  const onDrop = (from, to) => {
    if (!currentPuzzle || moveStatus) return false;
    const best = currentPuzzle.best_move || currentPuzzle.moves?.split(' ')[0] || '';
    const move = `${from}${to}`;
    const isCorrect = move === best || from + to === best;

    if (isCorrect) {
      setMoveStatus('correct');
      submitAttempt(currentPuzzle.puzzle_id, currentType, true)
        .then(() => getPuzzleStats()
          .then((r) => setPuzzleStats(r.data.puzzle_stats)));
    } else {
      setMoveStatus('wrong');
      submitAttempt(currentPuzzle.puzzle_id, currentType, false);
    }
    return true;
  };

  const nextPuzzle = () => {
    const list = currentType === 'game' ? puzzles : lichessPuzzles;
    if (currentIndex + 1 < list.length) {
      setCurrentIndex(currentIndex + 1);
    } else if (currentType === 'game' && lichessPuzzles.length > 0) {
      setCurrentType('lichess');
      setCurrentIndex(0);
    } else {
      setMoveStatus('done');
    }
  };

  const resetPuzzle = () => {
    if (currentPuzzle) {
      const fen = currentPuzzle.fen_before || currentPuzzle.fen;
      if (fen) setCurrentFen(fen);
      setMoveStatus('');
    }
  };

  return (
    <div className="puzzle-trainer">
      <div className="trainer-header">
        <h1>Puzzle Trainer</h1>
        <p>Personalized puzzles based on your actual game mistakes</p>
      </div>

      {puzzleStats && (
        <div className="puzzle-stats-bar">
          <span>Attempted: <strong>{puzzleStats.total_attempts}</strong></span>
          <span>Solved: <strong>{puzzleStats.total_solved || 0}</strong></span>
          <span>Solve rate: <strong>{puzzleStats.solve_rate_pct}%</strong></span>
        </div>
      )}

      {!submitted ? (
        <div className="card">
          <h2>Load Your Puzzles</h2>
          <form onSubmit={handleLoad}>
            <div className="form-group">
              <label>Your Chess Username</label>
              <input
                type="text"
                value={chessUsername}
                onChange={(e) => setChessUsername(e.target.value)}
                placeholder="e.g. Walid_150"
                required
              />
            </div>
            {error && <p className="error">{error}</p>}
            <button className="btn btn-primary" type="submit" disabled={loading}>
              {loading ? 'Loading...' : 'Load Puzzles'}
            </button>
          </form>
        </div>
      ) : (
        <div className="trainer-body">
          <div className="puzzle-tabs">
            <button
              className={`tab ${currentType === 'game' ? 'active' : ''}`}
              onClick={() => { setCurrentType('game'); setCurrentIndex(0); }}
            >
              From Your Games ({puzzles.length})
            </button>
            <button
              className={`tab ${currentType === 'lichess' ? 'active' : ''}`}
              onClick={() => { setCurrentType('lichess'); setCurrentIndex(0); }}
            >
              Themed Puzzles ({lichessPuzzles.length})
            </button>
          </div>

          {currentPuzzle && currentFen ? (
            <div className="puzzle-body">
              <div className="puzzle-info">
                {currentType === 'game' ? (
                  <>
                    <p className="puzzle-label">
                      Move {currentPuzzle.move_number} ({currentPuzzle.color}) —{' '}
                      <span className={`badge badge-${currentPuzzle.classification}`}>
                        {currentPuzzle.classification}
                      </span>
                    </p>
                    {currentPuzzle.pattern_tags?.length > 0 && (
                      <p className="puzzle-pattern">
                        Pattern: {JSON.parse(typeof currentPuzzle.pattern_tags === 'string'
                          ? currentPuzzle.pattern_tags : JSON.stringify(currentPuzzle.pattern_tags)
                        ).join(', ').replace(/_/g, ' ')}
                      </p>
                    )}
                  </>
                ) : (
                  <>
                    <p className="puzzle-label">
                      Lichess Puzzle — Rating: {currentPuzzle.rating}
                    </p>
                    <p className="puzzle-pattern">
                      Theme: {currentPuzzle.pattern?.replace(/_/g, ' ')}
                    </p>
                  </>
                )}

                <p className="puzzle-instruction">
                  {moveStatus === '' && '🎯 Find the best move — drag a piece!'}
                  {moveStatus === 'correct' && '✓ Correct! Well done.'}
                  {moveStatus === 'wrong' && `✗ Not quite. Best was ${currentPuzzle.best_move || ''}`}
                  {moveStatus === 'done' && 'All puzzles complete!'}
                </p>
              </div>

              <ChessBoard
                key={currentFen}
                fen={currentFen}
                onDrop={onDrop}
                draggable={!moveStatus}
              />

              {moveStatus && moveStatus !== 'done' && (
                <div className="puzzle-feedback">
                  {currentType === 'game' && currentPuzzle.explanation && (
                    <p className="explanation-text">{currentPuzzle.explanation}</p>
                  )}
                  <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
                    <button className="btn btn-ghost" onClick={resetPuzzle}>
                      Try Again
                    </button>
                    <button className="btn btn-primary" onClick={nextPuzzle}>
                      Next Puzzle →
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="card">
              <p style={{color: '#94a3b8'}}>
                No puzzles available. Analyze more games on the Dashboard first.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
