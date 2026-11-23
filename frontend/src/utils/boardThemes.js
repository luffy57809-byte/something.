export const BOARD_THEMES = {
  walnut: { label: 'Walnut', light: '#ecdcb8', dark: '#7a4f35' },
  green: { label: 'Green', light: '#eeeed2', dark: '#769656' },
  blue: { label: 'Blue', light: '#dee3e6', dark: '#8ca2ad' },
  brown: { label: 'Classic brown', light: '#f0d9b5', dark: '#b58863' },
  gray: { label: 'Gray', light: '#e6e6e6', dark: '#8a8a8a' },
  purple: { label: 'Purple', light: '#ebe6f2', dark: '#8877b7' },
  slate: { label: 'Slate', light: '#a7b4c2', dark: '#4a5a6a' },
};

export const HIGHLIGHTS = {
  gold: { label: 'Gold', lastLight: '#efd98f', lastDark: '#b89242', selLight: '#f3c969', selDark: '#c99a2e' },
  lime: { label: 'Lime', lastLight: '#f6f669', lastDark: '#baca2b', selLight: '#ffff77', selDark: '#d5d63a' },
  sky: { label: 'Sky', lastLight: '#bfe0f5', lastDark: '#6aa6c9', selLight: '#9fd1f0', selDark: '#4f8fb5' },
  rose: { label: 'Rose', lastLight: '#f4c2c2', lastDark: '#c97a7a', selLight: '#f2a8a8', selDark: '#b95c5c' },
};

export const SIZE_PX = { small: 352, medium: 416, large: 480 };
export const ANIMATION_MS = { off: 0, fast: 100, normal: 180, slow: 350 };

export const DEFAULT_SETTINGS = {
  theme: 'walnut',
  highlight: 'gold',
  coordinates: true,
  legalMoves: true,
  animation: 'normal',
  size: 'medium',
};

// Keep only known keys with allowed values (the server does the same check)
const has = (obj, key) => Object.prototype.hasOwnProperty.call(obj, key);

export function normalizeSettings(raw) {
  const src = raw && typeof raw === 'object' && !Array.isArray(raw) ? raw : {};
  const out = { ...DEFAULT_SETTINGS };
  if (typeof src.theme === 'string' && has(BOARD_THEMES, src.theme)) out.theme = src.theme;
  if (typeof src.highlight === 'string' && has(HIGHLIGHTS, src.highlight)) out.highlight = src.highlight;
  if (typeof src.animation === 'string' && has(ANIMATION_MS, src.animation)) out.animation = src.animation;
  if (typeof src.size === 'string' && has(SIZE_PX, src.size)) out.size = src.size;
  if (typeof src.coordinates === 'boolean') out.coordinates = src.coordinates;
  if (typeof src.legalMoves === 'boolean') out.legalMoves = src.legalMoves;
  return out;
}
