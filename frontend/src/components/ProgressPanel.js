import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getProgress } from '../api';
import {
  averageAccuracy, chartPoints, trendSummary, recordOf, patternRows,
} from '../utils/progressHelpers';

const OUTCOME_COLOR = { win: '#7fc98f', loss: '#f0766b', draw: '#e3c75a', unknown: '#a9b5a6' };

export default function ProgressPanel({ username, refreshKey }) {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!username) return undefined;
    let alive = true;
    getProgress(username)
      .then((res) => {
        if (alive) {
          setData(res.data);
          setFailed(false);
        }
      })
      .catch(() => {
        if (alive) setFailed(true);
      });
    return () => {
      alive = false;
    };
  }, [username, refreshKey]);

  if (!username || failed || !data) return null;

  const games = data.games || [];
  if (games.length < 2) {
    return (
      <div className="card">
        <h2>Your progress</h2>
        <p className="hint-text">
          Analyze at least 2 games to see how your accuracy changes over time.
        </p>
      </div>
    );
  }

  const chart = chartPoints(games);
  const trend = trendSummary(games);
  const record = recordOf(games);
  const patterns = patternRows(data.pattern_counts);

  return (
    <div className="card progress-card">
      <h2>Your progress</h2>

      <div className="progress-stats">
        <div className="progress-stat">
          <div className="progress-value">{averageAccuracy(games)}%</div>
          <div className="progress-label">Average accuracy, last {games.length} games</div>
        </div>
        <div className="progress-stat">
          <div className={`progress-value ${trend ? (trend.delta >= 0 ? 'up' : 'down') : ''}`}>
            {trend ? `${trend.delta >= 0 ? '+' : ''}${trend.delta}` : '–'}
          </div>
          <div className="progress-label">
            {trend ? `points vs the ${trend.k} games before` : 'Needs a few more games'}
          </div>
        </div>
        <div className="progress-stat">
          <div className="progress-value">{record.win}W {record.loss}L {record.draw}D</div>
          <div className="progress-label">Record</div>
        </div>
      </div>

      <svg className="progress-chart" viewBox="0 0 400 120" role="img"
           aria-label="Accuracy over your analyzed games">
        <line x1="10" y1="10" x2="390" y2="10" stroke="#a9b5a6" strokeOpacity="0.3" strokeWidth="1" />
        <line x1="10" y1="110" x2="390" y2="110" stroke="#a9b5a6" strokeOpacity="0.3" strokeWidth="1" />
        <text x="12" y="8" fontSize="7" fill="#a9b5a6">{chart.hi}%</text>
        <text x="12" y="119" fontSize="7" fill="#a9b5a6">{chart.lo}%</text>
        <polyline points={chart.line} fill="none" stroke="#d3a548" strokeWidth="2" />
        {games.map((g, i) => (
          <circle
            key={g.game_id}
            cx={chart.xs[i]}
            cy={chart.ys[i]}
            r="4"
            fill={OUTCOME_COLOR[g.outcome] || OUTCOME_COLOR.unknown}
            stroke="#14271f"
            strokeWidth="1.5"
            style={{ cursor: 'pointer' }}
            onClick={() => navigate(`/game/${encodeURIComponent(g.game_id)}`)}
          >
            <title>{`${g.date || ''} vs ${g.opponent}: ${g.accuracy_pct}% (${g.outcome})`}</title>
          </circle>
        ))}
      </svg>
      <p className="progress-legend">
        Green dots are wins, red are losses, yellow are draws. Click a dot to open that game.
      </p>

      {patterns.length > 0 && (
        <>
          <h3>Most common mistakes</h3>
          {patterns.map((p) => (
            <div key={p.tag} className="pattern-row">
              <span className="pattern-label">{p.label}</span>
              <div className="pattern-bar">
                <div className="pattern-fill" style={{ width: `${p.pct}%` }} />
              </div>
              <span className="pattern-count">{p.count}</span>
            </div>
          ))}
        </>
      )}
    </div>
  );
}
