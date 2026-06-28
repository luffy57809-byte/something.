import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import ChessBoard from '../components/ChessBoard';
import { Chess } from 'chess.js';
import { getGameReport } from '../api';
import './GameReport.css';

export default function GameReport() {
  const { gameId } = useParams();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [currentFen, setCurrentFen] = useState('start');
  const [mode, setMode] = useState('view');
  const [moveStatus, setMoveStatus] = useState('');
  const fenRef = useRef('start');

  useEffect(() => {
    getGameReport(decodeURIComponent(gameId))
      .then((res) => {
        setReport(res.data);
        if (res.data.flagged_moves.length > 0) {
          const fen = res.data.flagged_moves[0].fen_before;
          fenRef.current = fen;
          setCurrentFen(fen);
          setSelectedIndex(0);
        }
      })
      .catch(() => setError('Failed to load game report'))
      .finally(() => setLoading(false));
  }, [gameId]);

  const selectedMove = report?.flagged_moves[selectedIndex];

  const loadMove = (index) => {
    const m = report.flagged_moves[index];
    fenRef.current = m.fen_before;
    setSelectedIndex(index);
    setCurrentFen(m.fen_before);
    setMode('view');
    setMoveStatus('');
  };

  const handlePieceDrop = (sourceSquare, targetSquare) => {
    if (mode !== 'play' || !selectedMove) return false;
    try {
      const tempGame = new Chess(fenRef.current);
      const move = tempGame.move({
        from: sourceSquare,
        to: targetSquare,
        promotion: 'q',
      });
      if (!move) return false;
      const best = selectedMove.best_move_san || '';
      const isCorrect =
        move.san === best ||
        move.lan === best ||
        `${sourceSquare}${targetSquare}` === best;
      fenRef.current = tempGame.fen();
      setCurrentFen(tempGame.fen());
      setMoveStatus(isCorrect ? 'correct' : 'wrong');
      return true;
    } catch {
      return false;
    }
  };

  const resetBoard = () => {
    if (selectedMove) {
      fenRef.current = selectedMove.fen_before;
      setCurrentFen(selectedMove.fen_before);
      setMoveStatus('');
    }
  };

  const showBestMove = () => {
    if (!selectedMove) return;
    try {
      const tempGame = new Chess(selectedMove.fen_before);
      tempGame.move(selectedMove.best_move_san);
      fenRef.current = tempGame.fen();
      setCurrentFen(tempGame.fen());
      setMoveStatus('shown');
    } catch {
      setMoveStatus('shown');
    }
  };

  if (loading) return <div className="loading">Loading game report...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!report) return null;

  const { summary } = report;

  return (
    <div className="game-report">
      <div className="report-header">
        <h1>{report.white} vs {report.black}</h1>
        <p>{report.date} — Result: <strong>{report.result}</strong></p>
      </div>

      <div className="report-summary">
        <div className="summary-stat">
          <span className="summary-value">{summary.accuracy_pct}%</span>
          <span className="summary-label">Accuracy</span>
        </div>
        <div className="summary-stat">
          <span className="summary-value blunder">{summary.blunders}</span>
          <span className="summary-label">Blunders</span>
        </div>
        <div className="summary-stat">
          <span className="summary-value mistake">{summary.mistakes}</span>
          <span className="summary-label">Mistakes</span>
        </div>
        <div className="summary-stat">
          <span className="summary-value inaccuracy">{summary.inaccuracies}</span>
          <span className="summary-label">Inaccuracies</span>
        </div>
      </div>

      <div className="report-body">
        <div className="moves-panel">
          <h2>Flagged Moves</h2>
          {report.flagged_moves.map((m, i) => (
            <div
              key={i}
              className={`move-item ${selectedIndex === i ? 'selected' : ''}`}
              onClick={() => loadMove(i)}
            >
              <div className="move-header">
                <span className="move-notation">
                  {m.move_number}.{m.color === 'black' ? '..' : ''}{m.move_san}
                </span>
                <span className={`badge badge-${m.classification}`}>
                  {m.classification}
                </span>
              </div>
              {m.pattern_tags.length > 0 && (
                <div className="move-tags">
                  {m.pattern_tags.map((t) => (
                    <span key={t} className="tag">
                      {t.replace(/_/g, ' ')}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="board-panel">
          {selectedMove ? (
            <>
              <div className="board-mode-label">
                {mode === 'view'
                  ? '👁 Position before the move'
                  : '🎯 Drag a piece to find the best move!'}
              </div>

              <div className="board-controls">
                <button
                  className={`btn ${mode === 'view' ? 'btn-primary' : 'btn-ghost'}`}
                  onClick={() => { setMode('view'); resetBoard(); }}
                >
                  View Position
                </button>
                <button
                  className={`btn ${mode === 'play' ? 'btn-primary' : 'btn-ghost'}`}
                  onClick={() => { setMode('play'); resetBoard(); }}
                >
                  Try Best Move
                </button>
                <button className="btn btn-ghost" onClick={resetBoard}>
                  Reset
                </button>
                <button className="btn btn-ghost" onClick={showBestMove}>
                  Show Answer
                </button>
              </div>

              {moveStatus === 'correct' && (
                <div className="move-feedback correct">
                  ✓ Correct! That was the best move.
                </div>
              )}
              {moveStatus === 'wrong' && (
                <div className="move-feedback wrong">
                  ✗ Not quite — try again or click Show Answer.
                </div>
              )}
              {moveStatus === 'shown' && (
                <div className="move-feedback shown">
                  Best move was <strong>{selectedMove.best_move_san}</strong>
                </div>
              )}

              <p style={{color:'#555', fontSize:'0.8rem', marginBottom:'0.5rem'}}>
                FEN: {currentFen.substring(0, 40)}...
              </p>

              <ChessBoard
                key={currentFen}
                fen={currentFen}
                onDrop={handlePieceDrop}
                draggable={mode === 'play'}
              />

              <div className="move-explanation">
                <div className="explanation-header">
                  <strong>
                    Move {selectedMove.move_number}
                    {selectedMove.color === 'black' ? '...' : '.'}
                    {selectedMove.move_san}
                  </strong>
                  <span className={`badge badge-${selectedMove.classification}`}>
                    {selectedMove.classification}
                  </span>
                </div>
                <p className="best-move">
                  ✓ Best move: <strong>{selectedMove.best_move_san}</strong>
                  {' '}(eval drop: {selectedMove.eval_drop} cp)
                </p>
                <p className="explanation-text">{selectedMove.explanation}</p>
              </div>
            </>
          ) : (
            <div className="card">
              <p style={{color: '#94a3b8'}}>
                Click a move on the left to see the position.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
