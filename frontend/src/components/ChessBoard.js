import React, { useState, useEffect } from 'react';

const PIECES = {
  'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
  'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟',
};

const PIECE_COLORS = {
  'K': '#fff', 'Q': '#fff', 'R': '#fff', 'B': '#fff', 'N': '#fff', 'P': '#fff',
  'k': '#111', 'q': '#111', 'r': '#111', 'b': '#111', 'n': '#111', 'p': '#111',
};

function parseFen(fen) {
  const board = Array(8).fill(null).map(() => Array(8).fill(null));
  const rows = fen.split(' ')[0].split('/');
  rows.forEach((row, rankIdx) => {
    let fileIdx = 0;
    for (const ch of row) {
      if (ch >= '1' && ch <= '8') {
        fileIdx += parseInt(ch);
      } else {
        board[rankIdx][fileIdx] = ch;
        fileIdx++;
      }
    }
  });
  return board;
}

function squareName(rankIdx, fileIdx) {
  return String.fromCharCode(97 + fileIdx) + (8 - rankIdx);
}

function isWhitePiece(p) { return p && p === p.toUpperCase() && p !== p.toLowerCase(); }
function isBlackPiece(p) { return p && p === p.toLowerCase() && p !== p.toUpperCase(); }

export default function ChessBoard({ fen, onDrop, draggable }) {
  const [board, setBoard] = useState([]);
  const [dragFrom, setDragFrom] = useState(null);
  const [dragOver, setDragOver] = useState(null);

  useEffect(() => {
    if (fen && fen !== 'start') {
      setBoard(parseFen(fen));
      setDragFrom(null);
      setDragOver(null);
    }
  }, [fen]);

  const handleDragStart = (e, rankIdx, fileIdx) => {
    if (!draggable) { e.preventDefault(); return; }
    const piece = board[rankIdx][fileIdx];
    if (!piece) { e.preventDefault(); return; }
    setDragFrom([rankIdx, fileIdx]);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', squareName(rankIdx, fileIdx));
  };

  const handleDragOver = (e, rankIdx, fileIdx) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOver([rankIdx, fileIdx]);
  };

  const handleDragLeave = () => {
    setDragOver(null);
  };

  const handleDrop = (e, rankIdx, fileIdx) => {
    e.preventDefault();
    setDragOver(null);
    if (!dragFrom) return;

    const [fromRank, fromFile] = dragFrom;
    if (fromRank === rankIdx && fromFile === fileIdx) {
      setDragFrom(null);
      return;
    }

    const from = squareName(fromRank, fromFile);
    const to = squareName(rankIdx, fileIdx);
    console.log('Drop:', from, '->', to);
    if (onDrop) onDrop(from, to);
    setDragFrom(null);
  };

  const handleDragEnd = () => {
    setDragFrom(null);
    setDragOver(null);
  };

  if (!board.length) return <div style={{color:'#94a3b8'}}>Loading board...</div>;

  return (
    <div style={{ userSelect: 'none' }}>
      <div style={{ display: 'flex' }}>
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          {[8,7,6,5,4,3,2,1].map(n => (
            <div key={n} style={{
              width: 20, height: 52,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: '#94a3b8', fontSize: '0.75rem'
            }}>{n}</div>
          ))}
        </div>

        <div>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(8, 52px)',
            gridTemplateRows: 'repeat(8, 52px)',
            border: '2px solid #4a5568',
            borderRadius: '4px',
            overflow: 'hidden',
          }}>
            {board.map((row, rankIdx) =>
              row.map((piece, fileIdx) => {
                const isLight = (rankIdx + fileIdx) % 2 === 0;
                const isDragSource = dragFrom &&
                  dragFrom[0] === rankIdx && dragFrom[1] === fileIdx;
                const isDragTarget = dragOver &&
                  dragOver[0] === rankIdx && dragOver[1] === fileIdx;

                return (
                  <div
                    key={`${rankIdx}-${fileIdx}`}
                    onDragOver={(e) => handleDragOver(e, rankIdx, fileIdx)}
                    onDragLeave={handleDragLeave}
                    onDrop={(e) => handleDrop(e, rankIdx, fileIdx)}
                    style={{
                      width: 52,
                      height: 52,
                      background: isDragSource ? '#f6f669'
                        : isDragTarget ? '#baca2b'
                        : isLight ? '#e2e8f0' : '#4a5568',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '36px',
                      cursor: draggable && piece ? 'grab' : 'default',
                      transition: 'background 0.1s',
                    }}
                  >
                    {piece && (
                      <span
                        draggable={draggable}
                        onDragStart={(e) => handleDragStart(e, rankIdx, fileIdx)}
                        onDragEnd={handleDragEnd}
                        style={{
                          color: PIECE_COLORS[piece],
                          textShadow: PIECE_COLORS[piece] === '#fff'
                            ? '0 0 2px #000, 0 0 2px #000'
                            : '0 0 2px #fff',
                          lineHeight: 1,
                          cursor: draggable ? 'grab' : 'default',
                          display: 'block',
                        }}
                      >
                        {PIECES[piece]}
                      </span>
                    )}
                  </div>
                );
              })
            )}
          </div>

          <div style={{ display: 'flex', marginTop: '2px' }}>
            {['a','b','c','d','e','f','g','h'].map(f => (
              <div key={f} style={{
                width: 52, textAlign: 'center',
                color: '#94a3b8', fontSize: '0.75rem'
              }}>{f}</div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
