import React, { useState, useEffect } from 'react';
import { Chessboard } from 'react-chessboard';
import { Chess } from 'chess.js';
import { getTrainingPuzzles, submitAttempt, getPuzzleStats } from '../api';
import './PuzzleTrainer.css';

export default function PuzzleTrainer() {
  const [chessUsername, setChessUsername] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [puzzles, setPuzzles] = useState([]);
  const [lichessPuzzles, setLichessPuzzles] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [currentType, setCurrentType] = useState('game');
  const [game, setGame] = useState(new Chess());
  const [status, setStatus] = useState('');
  const [solved, setSolved] = useState(false);
  const [failed, setFailed] = useState(false);
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
      const newGame = new Chess(currentPuzzle.fen || currentPuzzle.fen_before);
      setGame(newGame);
      setSolved(false);
      setFailed(false);
      setStatus('Find the best move!');
    }
  }, [currentIndex, currentType, puzzles, lichessPuzzles]);

  const handleLoad = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await getTrainingPuzzles(chessUsername);
      setPuzzles(res.data.game_puzzles || []);
      setLichessPuzzles(res.data.lichess_puzzles || []);
      setCurrentIndex(0);
      setCurrentType('game');
      setSubmitted(true);
    } catch (err) {
      setError('Failed to load puzzles');
    } finally {
      setLoading(false);
    }
  };

  const onDrop = (sourceSquare, targetSquare) => {
    if (solved || failed) return false;

    const bestMove = currentPuzzle?.best_move || '';
    const moveSan = `${sourceSquare}${targetSquare}`;

    // Check if move matches best move (UCI format comparison)
    const tempGame = new Chess(game.fen());
    const move = tempGame.move({
      from: sourceSquare,
      to: targetSquare,
      promotion: 'q',
    });

    if (!move) return false;

    const isCorrect =
      move.san === bestMove ||
      moveSan === bestMove ||
      move.lan === bestMove;

    if (isCorrect) {
      setGame(tempGame);
      setSolved(true);
      setStatus('✓ Correct! Well done.');
      submitAttempt(
        currentPuzzle.puzzle_id,
        currentType,
        true
      ).then(() =>
        getPuzzleStats().then((r) => setPuzzleStats(r.data.puzzle_stats))
      );
    } else {
      setFailed(true);
      setStatus(`✗ Not quite. The best move was ${bestMove}.`);
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
      setStatus('All puzzles complete! Analyze more games to get new puzzles.');
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
          <span>Puzzles attempted: <strong>{puzzleStats.total_attempts}</strong></span>
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

          {currentPuzzle ? (
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
                        Pattern: {currentPuzzle.pattern_tags.join(', ').replace(/_/g, ' ')}
                      </p>
                    )}
                    <p className="puzzle-instruction">{status}</p>
                  </>
                ) : (
                  <>
                    <p className="puzzle-label">
                      Lichess Puzzle — Rating: {currentPuzzle.rating}
                    </p>
                    <p className="puzzle-pattern">
                      Theme: {currentPuzzle.pattern?.replace(/_/g, ' ')}
                    </p>
                    <p className="puzzle-instruction">{status}</p>
                  </>
                )}
              </div>

              <Chessboard
                position={currentPuzzle.fen || currentPuzzle.fen_before || 'start'}
                onPieceDrop={onDrop}
                boardWidth={420}
                customBoardStyle={{
                  borderRadius: '8px',
                  boxShadow: '0 4px 24px rgba(0,0,0,0.4)',
                }}
                customDarkSquareStyle={{ backgroundColor: '#4a5568' }}
                customLightSquareStyle={{ backgroundColor: '#e2e8f0' }}
              />

              {(solved || failed) && (
                <div className="puzzle-feedback">
                  {currentType === 'game' && currentPuzzle.explanation && (
                    <p className="explanation-text">{currentPuzzle.explanation}</p>
                  )}
                  <button className="btn btn-primary" onClick={nextPuzzle}>
                    Next Puzzle →
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="card">
              <p>No puzzles available for this tab. Analyze more games first.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
