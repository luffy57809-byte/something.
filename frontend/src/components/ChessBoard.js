import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Chessboard } from 'react-chessboard';
import { Chess } from 'chess.js';
import { BOARD_THEMES, HIGHLIGHTS, ANIMATION_MS } from '../utils/boardThemes';
import { useBoardSettings } from '../context/BoardSettingsContext';

const isLight = (sq) => (sq.charCodeAt(0) - 97 + Number(sq[1])) % 2 === 0;

export default function ChessBoard({
  fen, onDrop, draggable = true, orientation = 'white', arrows = null, highlightMove = null,
}) {
  const { settings, size } = useBoardSettings();
  const theme = BOARD_THEMES[settings.theme] || BOARD_THEMES.walnut;
  const hl = HIGHLIGHTS[settings.highlight] || HIGHLIGHTS.gold;

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
        styles[sq] = { backgroundColor: isLight(sq) ? hl.lastLight : hl.lastDark };
      });
    }
    if (selected) {
      styles[selected] = { backgroundColor: isLight(selected) ? hl.selLight : hl.selDark };
    }
    if (settings.legalMoves) {
      legalMoves.forEach((m) => {
        const capture = m.captured || (m.flags || '').includes('e');
        const marker = capture
          ? 'radial-gradient(circle, transparent 62%, rgba(0,0,0,0.28) 64%)'
          : 'radial-gradient(circle, rgba(0,0,0,0.28) 20%, transparent 22%)';
        styles[m.to] = { ...(styles[m.to] || {}), backgroundImage: marker };
      });
    }
    return styles;
  }, [lastMove, highlightMove, selected, legalMoves, hl, settings.legalMoves]);

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
    lightSquareStyle: { backgroundColor: theme.light },
    darkSquareStyle: { backgroundColor: theme.dark },
    lightSquareNotationStyle: { color: theme.dark },
    darkSquareNotationStyle: { color: theme.light },
    showNotation: settings.coordinates,
    boardStyle: { borderRadius: 4, boxShadow: `0 0 0 3px ${theme.dark}` },
    showAnimations: settings.animation !== 'off',
    animationDurationInMs: ANIMATION_MS[settings.animation],
    ...(arrows ? { arrows } : {}),
  };

  return (
    <div style={{ width: size, maxWidth: '100%', minWidth: 0 }}>
      <Chessboard options={options} />
    </div>
  );
}
