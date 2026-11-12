export const MARK = { blunder: '??', mistake: '?', inaccuracy: '?!' };

export const isFlagged = (m) =>
  m.classification === 'blunder' || m.classification === 'mistake' || m.classification === 'inaccuracy';

// Win chance (0-100) from a centipawn score, same curve the backend uses
export function winPct(cp) {
  return 50 + 50 * (2 / (1 + Math.exp(-0.00368208 * cp)) - 1);
}

// Engine scores are stored from the mover's point of view; convert to White's
export function whitePov(m, which) {
  const v = which === 'after' ? m.eval_after : m.eval_before;
  if (v === null || v === undefined) return 0;
  return m.color === 'white' ? v : -v;
}

export function formatEval(cp) {
  if (Math.abs(cp) >= 9000) return cp > 0 ? '+M' : '-M';
  return (cp >= 0 ? '+' : '') + (cp / 100).toFixed(1);
}

// Pair white and black moves into rows for the move list
export function buildRows(moves) {
  const rows = [];
  moves.forEach((m, i) => {
    const last = rows[rows.length - 1];
    if (m.color === 'white') {
      rows.push({ n: m.move_number, w: i, b: null });
    } else if (last && last.b === null && last.n === m.move_number) {
      last.b = i;
    } else {
      rows.push({ n: m.move_number, w: null, b: i });
    }
  });
  return rows;
}

// Points for the evaluation graph (White's share of the winning chances)
export function graphPoints(moves, width = 400, height = 100) {
  const n = moves.length;
  if (!n) return { area: '', xs: [] };
  const xs = moves.map((_, i) => (n === 1 ? 0 : (i / (n - 1)) * width));
  const ys = moves.map((m) => height - (winPct(whitePov(m, 'before')) / 100) * height);
  const pts = xs.map((x, i) => `${x.toFixed(1)},${ys[i].toFixed(1)}`);
  const line = 'M' + pts.join(' L');
  return { area: `${line} L${width},${height} L0,${height} Z`, xs };
}

export function indexFromClick(fraction, n) {
  return Math.max(0, Math.min(n - 1, Math.round(fraction * (n - 1))));
}

// Attach pattern tags (only the flagged list has them) to every move
export function withTags(moves, flagged) {
  const tags = {};
  (flagged || []).forEach((f) => {
    tags[`${f.move_number}-${f.color}`] = f.pattern_tags || [];
  });
  return moves.map((m) => ({
    ...m,
    pattern_tags: m.pattern_tags || tags[`${m.move_number}-${m.color}`] || [],
  }));
}

// Older servers send only flagged moves; newer ones send every move
export function movesFromReport(report) {
  const base = report.moves && report.moves.length ? report.moves : report.flagged_moves || [];
  return withTags(base, report.flagged_moves);
}
