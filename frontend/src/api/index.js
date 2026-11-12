import axios from 'axios';

const API = axios.create({
  baseURL: process.env.REACT_APP_API_URL ||
    (process.env.NODE_ENV === 'development' ? '' : 'https://something-p8bx.onrender.com'),
});

API.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const register = (username, email, password) =>
  API.post('/auth/register', { username, email, password });

export const login = (username, password) =>
  API.post('/auth/login', { username, password });

export const getMe = () => API.get('/auth/me');

export const analyzeGames = (chess_username, source = 'chesscom', max_games = 5) =>
  API.post('/analyze', { chess_username, source, max_games });

export const getUserStats = (username) =>
  API.get(`/user/${username}/stats`);

export const getUserGames = (username) =>
  API.get(`/user/${username}/games`);

export const getGameReport = (game_id) =>
  API.get(`/game/${game_id}`);

export const getTrainingPuzzles = (chess_username) =>
  API.get(`/puzzles/training?chess_username=${chess_username}`);

export const submitAttempt = (puzzle_id, puzzle_source, solved) =>
  API.post('/puzzles/attempt', { puzzle_id, puzzle_source, solved });

export const getPuzzleStats = () =>
  API.get('/puzzles/stats');

export default API;

export const clearCache = (username) =>
  API.delete(`/user/${username}/cache`);

export const detectCheating = (chess_username, max_games = 5, source = 'chesscom') =>
  API.post('/detect', { chess_username, max_games, source });

export const verifyEmail = (token) =>
  API.post('/auth/verify-email', { token });

export const resendVerification = () =>
  API.post('/auth/resend-verification');

export const forgotPassword = (email) =>
  API.post('/auth/forgot-password', { email });

export const resetPassword = (token, password) =>
  API.post('/auth/reset-password', { token, password });

export const startDetection = (chess_username, max_games, source) =>
  API.post('/detect/start', { chess_username, max_games, source });

export const getDetectionStatus = (jobId) =>
  API.get(`/detect/status/${jobId}`);
