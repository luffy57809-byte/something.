import React, {
  createContext, useCallback, useContext, useEffect, useRef, useState,
} from 'react';
import { useAuth } from './AuthContext';
import { getBoardSettings, saveBoardSettings } from '../api';
import { DEFAULT_SETTINGS, SIZE_PX, normalizeSettings } from '../utils/boardThemes';

const STORAGE_KEY = 'boardSettings';

const BoardSettingsContext = createContext({
  settings: DEFAULT_SETTINGS,
  size: SIZE_PX[DEFAULT_SETTINGS.size],
  update: () => {},
});

function readLocal() {
  try {
    return normalizeSettings(JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'));
  } catch {
    return { ...DEFAULT_SETTINGS };
  }
}

function writeLocal(settings) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  } catch {
    // storage can be unavailable; the settings still work for this visit
  }
}

export function BoardSettingsProvider({ children }) {
  const { user } = useAuth();
  const userId = user ? user.id : null;
  const [settings, setSettings] = useState(readLocal);
  const current = useRef(settings);
  current.current = settings;

  // After login, load the settings saved on the account
  useEffect(() => {
    if (!userId) return undefined;
    let alive = true;
    getBoardSettings()
      .then((res) => {
        if (!alive) return;
        if (res.data.saved) {
          const next = normalizeSettings(res.data.settings);
          current.current = next;
          setSettings(next);
          writeLocal(next);
        } else {
          // nothing saved yet: keep this device's choices and save them to the account
          const local = readLocal();
          if (JSON.stringify(local) !== JSON.stringify(DEFAULT_SETTINGS)) {
            saveBoardSettings(local).catch(() => {});
          }
        }
      })
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, [userId]);

  const update = useCallback((patch) => {
    const next = normalizeSettings({ ...current.current, ...patch });
    current.current = next;
    setSettings(next);
    writeLocal(next);
    if (userId) saveBoardSettings(next).catch(() => {});
  }, [userId]);

  return (
    <BoardSettingsContext.Provider value={{ settings, size: SIZE_PX[settings.size], update }}>
      {children}
    </BoardSettingsContext.Provider>
  );
}

export function useBoardSettings() {
  return useContext(BoardSettingsContext);
}
