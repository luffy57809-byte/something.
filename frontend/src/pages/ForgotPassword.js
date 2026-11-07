import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { forgotPassword } from '../api';
import './Auth.css';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await forgotPassword(email);
      setSent(true);
    } catch {
      setError('Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1>♟ Chesslytic</h1>
        <p className="auth-subtitle">Reset your password</p>
        {sent ? (
          <p className="auth-subtitle">
            If an account exists for that email, we sent a reset link. It works for one hour.
          </p>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="the email you signed up with"
                required
              />
            </div>
            {error && <p className="error">{error}</p>}
            <button className="btn btn-primary" type="submit" disabled={loading}>
              {loading ? 'Sending...' : 'Send reset link'}
            </button>
          </form>
        )}
        <p className="auth-footer"><Link to="/login">Back to sign in</Link></p>
      </div>
    </div>
  );
}
