import React, { useState, useEffect, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { Chess } from 'chess.js';
import ChessBoard from '../components/ChessBoard';
import EvalBar from '../components/EvalBar';
import { getGameReport } from '../api';
import {
  MARK, isFlagged, whitePov, formatEval, buildRows, graphPoints,
  indexFromClick, movesFromReport,
} from '../utils/reportHelpers';
import './GameReport.css';

function squaresOf(fen, san) {
  if (!fen || !san) return null;
  try {
    const mv = new Chess(fen).move(san);
    return mv ? { from: mv.from, to: mv.to } : null;
  } catch {
    return null;
  }
}

export default function GameReport() {
  const { gameId } = useParams();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sel, setSel] = useState(0);
  const [tab, setTab] = useState('all');
  const [mode, setMode] = useState('view');
  const [showAfter, setShowAfter] = useState(false);
  const [playFen, setPlayFen] = useState(null);
  const [moveStatus, setMoveStatus] = useState('');
  const [flipped, setFlipped] = useState(false);

  const moves = useMemo(() => (report ? movesFromReport(report) : []), [report]);

  useEffect(() => {
    getGameReport(decodeURIComponent(gameId))
      .then((res) => {
        setReport(res.data);
        const first = movesFromReport(res.data).findIndex(isFlagged);
        setSel(first >= 0 ? first : 0);
      })
      .catch(() => setError('Failed to load game report'))
      .finally(() => setLoading(false));
  }, [gameId]);

  const select = (i) => {
    if (!moves.length) return;
    setSel(Math.max(0, Math.min(moves.length - 1, i)));
    setMode('view');
    setShowAfter(false);
    setPlayFen(null);
    setMoveStatus('');
  };

  useEffect(() => {
    const onKey = (e) => {
      if (e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return;
      const tag = e.target && e.target.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
      if (e.key === 'ArrowLeft') { e.preventDefault(); select(sel - 1); }
      else if (e.key === 'ArrowRight') { e.preventDefault(); select(sel + 1); }
      else if (e.key === 'Home') { e.preventDefault(); select(0); }
      else if (e.key === 'End') { e.preventDefault(); select(moves.length - 1); }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  });

  if (loading) return <div className="loading">Loading game report...</div>;
  if (error) return <div className="error">{error}</div>;
  if (!report) return null;
  if (!moves.length) {
    return (
      <div className="card">
        <p>This game has no analyzed moves yet.</p>
      </div>
    );
  }

  const { summary } = report;
  const hasAllMoves = Boolean(report.moves && report.moves.length);
  const m = moves[sel];
  const flagged = isFlagged(m);

  let fenAfter = m.fen_after;
  if (!fenAfter) {
    try {
      const g = new Chess(m.fen_before);
      g.move(m.move_san);
      fenAfter = g.fen();
    } catch {
      fenAfter = m.fen_before;
    }
  }

  const baseFen = showAfter ? fenAfter : m.fen_before;
  const displayFen = playFen || baseFen;

  const playedSq = squaresOf(m.fen_before, m.move_san);
  const bestSq = squaresOf(m.fen_before, m.best_move_san);
  const prev = hasAllMoves && sel > 0 ? moves[sel - 1] : null;
  const prevSq = prev ? squaresOf(prev.fen_before, prev.move_san) : null;

  const viewing = mode === 'view' && !playFen;
  const highlight = viewing ? (showAfter ? playedSq : prevSq) : null;

  let arrows = null;
  if (viewing && !showAfter && flagged) {
    arrows = [];
    if (playedSq) arrows.push({ startSquare: playedSq.from, endSquare: playedSq.to, color: '#f0766b' });
    if (bestSq) arrows.push({ startSquare: bestSq.from, endSquare: bestSq.to, color: '#7fc98f' });
  }

  const defaultSide = summary.player_color || 'white';
  const orientation = flipped ? (defaultSide === 'white' ? 'black' : 'white') : defaultSide;

  const evalWhite = whitePov(m, showAfter ? 'after' : 'before');
  const barEval = Math.max(-890, Math.min(890, evalWhite));
  const graph = graphPoints(moves);
  const activeTab = hasAllMoves ? tab : 'flagged';

  const handlePieceDrop = (from, to) => {
    if (mode !== 'play') return false;
    try {
      const g = new Chess(playFen || m.fen_before);
      const move = g.move({ from, to, promotion: 'q' });
      if (!move) return false;
      if (!playFen) {
        const best = m.best_move_san || '';
        const ok = move.san === best || move.lan === best || `${from}${to}` === best;
        setMoveStatus(ok ? 'correct' : 'wrong');
      }
      setPlayFen(g.fen());
      return true;
    } catch {
      return false;
    }
  };

  const backToView = (after) => {
    setMode('view');
    setPlayFen(null);
    setMoveStatus('');
    setShowAfter(after);
  };

  const startQuiz = () => {
    setMode('play');
    setShowAfter(false);
    setPlayFen(null);
    setMoveStatus('');
  };

  const resetBoard = () => {
    setPlayFen(null);
    setMoveStatus('');
  };

  const showAnswer = () => {
    try {
      const g = new Chess(m.fen_before);
      g.move(m.best_move_san);
      setPlayFen(g.fen());
    } catch {
      // keep the board as it is
    }
    setMoveStatus('shown');
  };

  const onGraphClick = (e) => {
    const r = e.currentTarget.getBoundingClientRect();
    select(indexFromClick((e.clientX - r.left) / r.width, moves.length));
  };

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
      {summary.opponent && (
        <p className="opp-line">
          Opponent: {summary.opponent.accuracy_pct}% accuracy · {summary.opponent.blunders} blunders ·{' '}
          {summary.opponent.mistakes} mistakes · {summary.opponent.inaccuracies} inaccuracies
        </p>
      )}

      <div className="report-body">
        <div className="moves-panel">
          {hasAllMoves && (
            <div className="rep-tabs">
              <button
                className={`rep-tab ${activeTab === 'all' ? 'active' : ''}`}
                onClick={() => setTab('all')}
              >
                All moves
              </button>
              <button
                className={`rep-tab ${activeTab === 'flagged' ? 'active' : ''}`}
                onClick={() => setTab('flagged')}
              >
                Mistakes
              </button>
            </div>
          )}

          {activeTab === 'all' ? (
            <div className="move-grid">
              {buildRows(moves).map((r) => (
                <div className="mv-row" key={`${r.n}-${r.w}-${r.b}`}>
                  <span className="mv-num">{r.n}.</span>
                  {[r.w, r.b].map((idx, k) =>
                    idx === null ? (
                      <span key={k} className="mv mv-empty" />
                    ) : (
                      <button
                        key={k}
                        className={`mv mv-${moves[idx].classification} ${sel === idx ? 'selected' : ''}`}
                        onClick={() => select(idx)}
                      >
                        {moves[idx].move_san}{MARK[moves[idx].classification] || ''}
                      </button>
                    )
                  )}
                </div>
              ))}
            </div>
          ) : (
            moves.map((mv, i) =>
              isFlagged(mv) ? (
                <div
                  key={i}
                  className={`move-item ${sel === i ? 'selected' : ''}`}
                  onClick={() => select(i)}
                >
                  <div className="move-header">
                    <span className="move-notation">
                      {mv.move_number}.{mv.color === 'black' ? '..' : ''}{mv.move_san}
                    </span>
                    <span className={`badge badge-${mv.classification}`}>
                      {mv.classification}
                    </span>
                  </div>
                  {mv.pattern_tags.length > 0 && (
                    <div className="move-tags">
                      {mv.pattern_tags.map((t) => (
                        <span key={t} className="tag">{t.replace(/_/g, ' ')}</span>
                      ))}
                    </div>
                  )}
                </div>
              ) : null
            )
          )}
        </div>

        <div className="board-panel">
          <div className="board-mode-label">
            {mode === 'play'
              ? '🎯 Drag a piece to find the best move!'
              : showAfter ? 'Position after the move' : 'Position before the move'}
          </div>

          <div className="board-controls">
            <button className="btn btn-ghost" aria-label="First move" title="First move (Home)"
                    onClick={() => select(0)}>⏮</button>
            <button className="btn btn-ghost" aria-label="Previous move" title="Previous move (←)"
                    onClick={() => select(sel - 1)}>◀</button>
            <button className="btn btn-ghost" aria-label="Next move" title="Next move (→)"
                    onClick={() => select(sel + 1)}>▶</button>
            <button className="btn btn-ghost" aria-label="Last move" title="Last move (End)"
                    onClick={() => select(moves.length - 1)}>⏭</button>
            <button className="btn btn-ghost" onClick={() => setFlipped(!flipped)}>Flip board</button>
          </div>

          <div className="board-controls">
            <button
              className={`btn ${mode === 'view' && !showAfter ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => backToView(false)}
            >
              Before move
            </button>
            <button
              className={`btn ${mode === 'view' && showAfter ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => backToView(true)}
            >
              After move
            </button>
            <button
              className={`btn ${mode === 'play' ? 'btn-primary' : 'btn-ghost'}`}
              onClick={startQuiz}
            >
              Try best move
            </button>
            {mode === 'play' && (
              <>
                <button className="btn btn-ghost" onClick={resetBoard}>Reset</button>
                <button className="btn btn-ghost" onClick={showAnswer}>Show answer</button>
              </>
            )}
          </div>

          {moveStatus === 'correct' && (
            <div className="move-feedback correct">✓ Correct! That was the best move.</div>
          )}
          {moveStatus === 'wrong' && (
            <div className="move-feedback wrong">
              ✗ Not quite — try again or click Show answer.
            </div>
          )}
          {moveStatus === 'shown' && (
            <div className="move-feedback shown">
              Best move was <strong>{m.best_move_san}</strong>
            </div>
          )}

          <div style={{ display: 'flex', alignItems: 'flex-start' }}>
            <EvalBar evalScore={barEval} />
            <ChessBoard
              fen={displayFen}
              onDrop={handlePieceDrop}
              draggable={mode === 'play'}
              orientation={orientation}
              arrows={arrows}
              highlightMove={highlight}
            />
          </div>

          {hasAllMoves && moves.length > 1 && (
            <div className="eval-graph" onClick={onGraphClick}>
              <svg viewBox="0 0 400 100" preserveAspectRatio="none" width="100%" height="90"
                   role="img" aria-label="Evaluation over the game">
                <rect width="400" height="100" fill="#2b1d14" />
                <path d={graph.area} fill="#ecdcb8" />
                <line x1="0" y1="50" x2="400" y2="50" stroke="#a9b5a6" strokeWidth="1"
                      strokeDasharray="4 4" vectorEffect="non-scaling-stroke" />
                <line x1={graph.xs[sel]} y1="0" x2={graph.xs[sel]} y2="100" stroke="#d3a548"
                      strokeWidth="2" vectorEffect="non-scaling-stroke" />
              </svg>
            </div>
          )}

          <div className="move-explanation">
            <div className="explanation-header">
              <strong>
                Move {m.move_number}{m.color === 'black' ? '...' : '.'}{m.move_san}
              </strong>
              <span className={`badge badge-${m.classification}`}>{m.classification}</span>
            </div>
            {hasAllMoves && (
              <p className="eval-line">
                Evaluation (from White’s side): {formatEval(whitePov(m, 'before'))} before,{' '}
                {formatEval(whitePov(m, 'after'))} after
              </p>
            )}
            {flagged ? (
              <>
                <p className="best-move">
                  ✓ Best move: <strong>{m.best_move_san}</strong> (eval drop: {m.eval_drop} cp)
                </p>
                <p className="explanation-text">{m.explanation}</p>
              </>
            ) : (
              <p className="best-move">
                {m.best_move_san && m.best_move_san !== m.move_san
                  ? `The engine’s top choice was ${m.best_move_san}, but this move is fine.`
                  : 'This was the engine’s top choice.'}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
