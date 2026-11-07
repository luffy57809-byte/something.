import React, { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { resetPassword } from '../api';
import './Auth.css';

export default function ResetPassword() {
  const [params] = useSearchParams();
  const token = params.get('token') || '';
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [done, setDone] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (password.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    if (password !== confirm) {
      setError('The two passwords do not match.');
      return;
    }
    setLoading(true);
    try {
      await resetPassword(token, password);
      setDone(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1>♟ Chesslytic</h1>
        <p className="auth-subtitle">Choose a new password</p>
        {done ? (
          <>
            <p className="auth-subtitle">Your password was changed.</p>
            <Link className="btn btn-primary" to="/login"
                  style={{ display: 'block', textAlign: 'center', textDecoration: 'none' }}>
              Sign in
            </Link>
          </>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>New password</label>
              <input type="password" value={password}
                     onChange={(e) => setPassword(e.target.value)} required />
            </div>
            <div className="form-group">
              <label>Confirm new password</label>
              <input type="password" value={confirm}
                     onChange={(e) => setConfirm(e.target.value)} required />
            </div>
            {error && <p className="error">{error}</p>}
            <button className="btn btn-primary" type="submit" disabled={loading}>
              {loading ? 'Saving...' : 'Change password'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
