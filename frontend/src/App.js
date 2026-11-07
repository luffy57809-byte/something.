import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import GameReport from './pages/GameReport';
import PuzzleTrainer from './pages/PuzzleTrainer';
import CheatDetection from './pages/CheatDetection';
import VerifyEmail from './pages/VerifyEmail';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import { resendVerification } from './api';
import Navbar from './components/Navbar';
import './App.css';

function PrivateRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="loading">Loading...</div>;
  return user ? children : <Navigate to="/login" />;
}

function VerifyBanner() {
  const { user } = useAuth();
  const [msg, setMsg] = React.useState('');
  if (!user || user.email_verified !== false) return null;

  const resend = async () => {
    try {
      await resendVerification();
      setMsg('Verification email sent. Check your inbox and spam folder.');
    } catch (err) {
      setMsg(err.response?.data?.detail || 'Could not send the email right now.');
    }
  };

  return (
    <div style={{ background: 'var(--table-raised)', color: 'var(--text)', padding: '0.6rem 1.5rem', fontSize: '0.9rem', display: 'flex', flexWrap: 'wrap', gap: '0.75rem', alignItems: 'center' }}>
      <span>{msg || 'Please verify your email to start analyzing games. We sent you a link.'}</span>
      <button className="btn btn-ghost" style={{ padding: '0.25rem 0.9rem', fontSize: '0.85rem' }} onClick={resend}>Resend email</button>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Navbar />
        <VerifyBanner />
        <div className="app-container">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/verify" element={<VerifyEmail />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            <Route path="/" element={
              <PrivateRoute><Dashboard /></PrivateRoute>
            } />
            <Route path="/game/:gameId" element={
              <PrivateRoute><GameReport /></PrivateRoute>
            } />
            <Route path="/detect" element={
              <PrivateRoute><CheatDetection /></PrivateRoute>
            } />
            <Route path="/puzzles" element={
              <PrivateRoute><PuzzleTrainer /></PrivateRoute>
            } />
          </Routes>
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
