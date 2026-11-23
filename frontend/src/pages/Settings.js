import React, { useState } from 'react';
import { Chess } from 'chess.js';
import ChessBoard from '../components/ChessBoard';
import { useBoardSettings } from '../context/BoardSettingsContext';
import { BOARD_THEMES, HIGHLIGHTS, DEFAULT_SETTINGS } from '../utils/boardThemes';
import './Settings.css';

const START = 'r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4';

const SIZE_LABELS = [['small', 'Small'], ['medium', 'Medium'], ['large', 'Large']];
const ANIMATION_LABELS = [['off', 'Off'], ['fast', 'Fast'], ['normal', 'Normal'], ['slow', 'Slow']];

export default function Settings() {
  const { settings, update } = useBoardSettings();
  const [fen, setFen] = useState(START);

  const onDrop = (from, to) => {
    try {
      const g = new Chess(fen);
      if (!g.move({ from, to, promotion: 'q' })) return false;
      setFen(g.fen());
      return true;
    } catch {
      return false;
    }
  };

  return (
    <div className="settings-page">
      <div className="settings-header">
        <h1>Board settings</h1>
        <p>Your choices are saved to your account and follow you to other devices.</p>
      </div>

      <div className="settings-body">
        <div className="card settings-controls">
          <h3 className="settings-sub">Board colors</h3>
          <div className="swatch-grid">
            {Object.entries(BOARD_THEMES).map(([id, t]) => (
              <button
                key={id}
                type="button"
                className={`swatch-btn ${settings.theme === id ? 'active' : ''}`}
                onClick={() => update({ theme: id })}
              >
                <span className="swatch">
                  <i style={{ background: t.light }} />
                  <i style={{ background: t.dark }} />
                  <i style={{ background: t.dark }} />
                  <i style={{ background: t.light }} />
                </span>
                {t.label}
              </button>
            ))}
          </div>

          <h3 className="settings-sub">Highlight color</h3>
          <div className="swatch-grid">
            {Object.entries(HIGHLIGHTS).map(([id, h]) => (
              <button
                key={id}
                type="button"
                className={`swatch-btn ${settings.highlight === id ? 'active' : ''}`}
                onClick={() => update({ highlight: id })}
              >
                <span className="swatch">
                  <i style={{ background: h.lastLight }} />
                  <i style={{ background: h.lastDark }} />
                  <i style={{ background: h.lastDark }} />
                  <i style={{ background: h.lastLight }} />
                </span>
                {h.label}
              </button>
            ))}
          </div>

          <h3 className="settings-sub">Board size</h3>
          <div className="seg">
            {SIZE_LABELS.map(([id, label]) => (
              <button
                key={id}
                type="button"
                className={`seg-btn ${settings.size === id ? 'active' : ''}`}
                onClick={() => update({ size: id })}
              >
                {label}
              </button>
            ))}
          </div>

          <h3 className="settings-sub">Piece animation</h3>
          <div className="seg">
            {ANIMATION_LABELS.map(([id, label]) => (
              <button
                key={id}
                type="button"
                className={`seg-btn ${settings.animation === id ? 'active' : ''}`}
                onClick={() => update({ animation: id })}
              >
                {label}
              </button>
            ))}
          </div>

          <h3 className="settings-sub">Board options</h3>
          <label className="check-row">
            <input
              type="checkbox"
              checked={settings.coordinates}
              onChange={(e) => update({ coordinates: e.target.checked })}
            />
            Show coordinates on the board
          </label>
          <label className="check-row">
            <input
              type="checkbox"
              checked={settings.legalMoves}
              onChange={(e) => update({ legalMoves: e.target.checked })}
            />
            Show legal moves when you select a piece
          </label>

          <button type="button" className="btn btn-ghost" onClick={() => update(DEFAULT_SETTINGS)}>
            Reset to defaults
          </button>
        </div>

        <div className="settings-preview">
          <h3 className="settings-sub">Preview</h3>
          <p className="hint-text">Drag a piece, or click one, to try your settings.</p>
          <ChessBoard fen={fen} onDrop={onDrop} draggable />
          <button type="button" className="btn btn-ghost" onClick={() => setFen(START)}>
            Reset position
          </button>
        </div>
      </div>
    </div>
  );
}
