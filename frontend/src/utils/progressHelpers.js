export function averageAccuracy(games) {
  if (!games.length) return 0;
  return +(games.reduce((s, g) => s + g.accuracy_pct, 0) / games.length).toFixed(1);
}

// Positions for the accuracy chart (SVG coordinates)
export function chartPoints(games, width = 400, height = 120, pad = 10) {
  const n = games.length;
  const accs = games.map((g) => g.accuracy_pct);
  const lo = Math.max(0, Math.floor((Math.min(...accs) - 5) / 10) * 10);
  const hi = 100;
  const xs = games.map((_, i) => (n === 1 ? width / 2 : pad + (i / (n - 1)) * (width - 2 * pad)));
  const ys = accs.map((a) => pad + (1 - (a - lo) / (hi - lo)) * (height - 2 * pad));
  const line = xs.map((x, i) => `${x.toFixed(1)},${ys[i].toFixed(1)}`).join(' ');
  return { xs, ys, lo, hi, line };
}

// Average of the latest games compared with the games before them
export function trendSummary(games) {
  const n = games.length;
  const k = Math.min(5, Math.floor(n / 2));
  if (k < 2) return null;
  const avg = (arr) => arr.reduce((s, g) => s + g.accuracy_pct, 0) / arr.length;
  const recent = avg(games.slice(n - k));
  const previous = avg(games.slice(n - 2 * k, n - k));
  return {
    k,
    recent: +recent.toFixed(1),
    previous: +previous.toFixed(1),
    delta: +(recent - previous).toFixed(1),
  };
}

export function recordOf(games) {
  const r = { win: 0, loss: 0, draw: 0 };
  games.forEach((g) => {
    if (r[g.outcome] !== undefined) r[g.outcome] += 1;
  });
  return r;
}

// Mistake types, most common first, with a bar width relative to the biggest
export function patternRows(counts) {
  const entries = Object.entries(counts || {}).sort((a, b) => b[1] - a[1]);
  const max = entries.length ? entries[0][1] : 1;
  return entries.map(([tag, count]) => ({
    tag,
    label: tag.replace(/_/g, ' '),
    count,
    pct: Math.round((count / max) * 100),
  }));
}
