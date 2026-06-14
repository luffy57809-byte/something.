import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Chessboard } from 'react-chessboard';
import { getGameReport } from '../api';
import './GameReport.css';

export default function GameReport() {
  const { gameId } = useParams();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedMove, setSelectedMove] = useState(null);

  useEffect(() => {
    getGameReport(decodeURIComponent(gameId))
      .then((res) => {
        setReport(res.data);
        if (res.data.flagged_moves.length > 0) {
          setSelectedMove(res.data.flagged_moves[0]);
        }
      })
      .catch(() => setError('Failed to load game report'))
      .finally(() => setLoading(false));
  }, [gameId]);

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
              className={`move-item ${selectedMove === m ? 'selected' : ''}`}
              onClick={() => setSelectedMove(m)}
            >
              <div className="move-header">
                <span className="move-notation">
                  {m.move_number}. {m.color === 'black' ? '...' : ''}{m.move_san}
                </span>
                <span className={`badge badge-${m.classification}`}>
                  {m.classification}
                </span>
              </div>
              {m.pattern_tags.length > 0 && (
                <div className="move-tags">
                  {m.pattern_tags.map((t) => (
                    <span key={t} className="tag">{t.replace(/_/g, ' ')}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="board-panel">
          {selectedMove && (
            <>
              <Chessboard
                position={selectedMove.fen_before}
                boardWidth={420}
                arePiecesDraggable={false}
                customBoardStyle={{
                  borderRadius: '8px',
                  boxShadow: '0 4px 24px rgba(0,0,0,0.4)',
                }}
                customDarkSquareStyle={{ backgroundColor: '#4a5568' }}
                customLightSquareStyle={{ backgroundColor: '#e2e8f0' }}
              />
              <div className="move-explanation">
                <div className="explanation-header">
                  <strong>
                    Move {selectedMove.move_number}
                    {selectedMove.color === 'black' ? '...' : '.'}{' '}
                    {selectedMove.move_san}
                  </strong>
                  <span className={`badge badge-${selectedMove.classification}`}>
                    {selectedMove.classification}
                  </span>
                </div>
                <p className="best-move">
                  ✓ Best move was: <strong>{selectedMove.best_move_san}</strong>
                  {' '}(eval drop: {selectedMove.eval_drop} cp)
                </p>
                <p className="explanation-text">{selectedMove.explanation}</p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
