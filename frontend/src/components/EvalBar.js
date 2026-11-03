import React from 'react';

export default function EvalBar({ evalScore, color = 'white' }) {
  // evalScore is in centipawns from white's perspective
  // Clamp between -1000 and 1000 for display
  const clamp = (val, min, max) => Math.min(Math.max(val, min), max);
  
  const cp = clamp(evalScore || 0, -1000, 1000);
  
  // Convert to percentage (50% = equal, 0% = black winning, 100% = white winning)
  const whitePercent = ((cp + 1000) / 2000) * 100;
  
  // Format display text
  const formatEval = (cp) => {
    if (Math.abs(cp) >= 900) {
      const mateIn = Math.ceil((1000 - Math.abs(cp)) / 10);
      return cp > 0 ? `M${mateIn}` : `-M${mateIn}`;
    }
    const pawns = (Math.abs(cp) / 100).toFixed(1);
    return cp >= 0 ? `+${pawns}` : `-${pawns}`;
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: '4px',
      marginRight: '8px',
    }}>
      <div style={{
        width: '24px',
        height: '416px',
        borderRadius: '4px',
        overflow: 'hidden',
        border: '1px solid #7a4f35',
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
      }}>
        {/* Black's portion (top) */}
        <div style={{
          width: '100%',
          height: `${100 - whitePercent}%`,
          background: '#2b1d14',
          transition: 'height 0.5s ease',
        }} />
        {/* White's portion (bottom) */}
        <div style={{
          width: '100%',
          height: `${whitePercent}%`,
          background: '#ecdcb8',
          transition: 'height 0.5s ease',
        }} />
        {/* Center line */}
        <div style={{
          position: 'absolute',
          top: '50%',
          left: 0,
          right: 0,
          height: '1px',
          background: '#d3a548',
        }} />
      </div>
      <div style={{
        fontSize: '0.7rem',
        color: cp >= 0 ? '#ece6d6' : '#a9b5a6',
        fontWeight: '600',
        fontFamily: 'monospace',
      }}>
        {formatEval(cp)}
      </div>
    </div>
  );
}
