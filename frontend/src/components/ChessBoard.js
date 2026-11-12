import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Chessboard } from 'react-chessboard';
import { Chess } from 'chess.js';

// To use chess.com's green instead of the wood look, set
// light: '#eeeed2' and dark: '#769656'.
const THEME = {
  light: '#ecdcb8',
  dark: '#7a4f35',
  lastLight: '#efd98f',
  lastDark: '#b89242',
  selLight: '#f3c969',
  selDark: '#c99a2e',
};

const isLight = (sq) => (sq.charCodeAt(0) - 97 + Number(sq[1])) % 2 === 0;

export default function ChessBoard({ fen, onDrop, draggable = true, orientation = 'white', arrows = null, highlightMove = null }) {
  const position = !fen || fen === 'start' ? new Chess().fen() : fen;
  const [selected, setSelected] = useState(null);
  const [lastMove, setLastMove] = useState(null);
  const pending = useRef(null);

  // When the position changes, highlight the move that caused it (if we made it)
  useEffect(() => {
    setLastMove(pending.current);
    pending.current = null;
    setSelected(null);
  }, [position]);

  const legalMoves = useMemo(() => {
    if (!selected) return [];
    try {
      return new Chess(position).moves({ square: selected, verbose: true });
    } catch {
      return [];
    }
  }, [selected, position]);

  const tryMove = (from, to) => {
    const ok = onDrop ? onDrop(from, to) !== false : false;
    if (ok) pending.current = { from, to };
    setSelected(null);
    return ok;
  };

  const handleSquareClick = (arg) => {
    if (!draggable) return;
    const square = typeof arg === 'string' ? arg : arg && arg.square;
    if (!square) return;

    if (selected && legalMoves.some((m) => m.to === square)) {
      tryMove(selected, square);
      return;
    }
    try {
      const game = new Chess(position);
      const piece = game.get(square);
      if (piece && piece.color === game.turn()) {
        setSelected(square === selected ? null : square);
      } else {
        setSelected(null);
      }
    } catch {
      setSelected(null);
    }
  };

  const squareStyles = useMemo(() => {
    const styles = {};
    const shownLast = highlightMove || lastMove;
    if (shownLast) {
      [shownLast.from, shownLast.to].forEach((sq) => {
        styles[sq] = { backgroundColor: isLight(sq) ? THEME.lastLight : THEME.lastDark };
      });
    }
    if (selected) {
      styles[selected] = { backgroundColor: isLight(selected) ? THEME.selLight : THEME.selDark };
    }
    legalMoves.forEach((m) => {
      const capture = m.captured || (m.flags || '').includes('e');
      const marker = capture
        ? 'radial-gradient(circle, transparent 62%, rgba(0,0,0,0.28) 64%)'
        : 'radial-gradient(circle, rgba(0,0,0,0.28) 20%, transparent 22%)';
      styles[m.to] = { ...(styles[m.to] || {}), backgroundImage: marker };
    });
    return styles;
  }, [lastMove, highlightMove, selected, legalMoves]);

  const options = {
    id: 'chesslytic-board',
    position,
    boardOrientation: orientation,
    allowDragging: !!draggable,
    onPieceDrop: ({ sourceSquare, targetSquare }) => {
      if (!targetSquare || targetSquare === sourceSquare) return false;
      return tryMove(sourceSquare, targetSquare);
    },
    onSquareClick: handleSquareClick,
    squareStyles,
    lightSquareStyle: { backgroundColor: THEME.light },
    darkSquareStyle: { backgroundColor: THEME.dark },
    lightSquareNotationStyle: { color: THEME.dark },
    darkSquareNotationStyle: { color: THEME.light },
    boardStyle: { borderRadius: 4, boxShadow: '0 0 0 3px #7a4f35' },
    animationDurationInMs: 180,
    ...(arrows ? { arrows } : {}),
  };

  return (
    <div style={{ width: 416, maxWidth: '100%', minWidth: 0 }}>
      <Chessboard options={options} />
    </div>
  );
}
