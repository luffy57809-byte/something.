import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { verifyEmail } from '../api';
import './Auth.css';

export default function VerifyEmail() {
  const [params] = useSearchParams();
  const [status, setStatus] = useState('working');

  useEffect(() => {
    const token = params.get('token');
    if (!token) {
      setStatus('error');
      return;
    }
    verifyEmail(token)
      .then(() => setStatus('ok'))
      .catch(() => setStatus('error'));
  }, [params]);

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1>♟ Chesslytic</h1>
        {status === 'working' && <p className="auth-subtitle">Verifying your email...</p>}
        {status === 'ok' && (
          <>
            <p className="auth-subtitle">Your email is verified. You can now analyze games.</p>
            <a className="btn btn-primary" href="/"
               style={{ display: 'block', textAlign: 'center', textDecoration: 'none' }}>
              Continue
            </a>
          </>
        )}
        {status === 'error' && (
          <>
            <p className="error" style={{ textAlign: 'center' }}>
              This verification link is invalid or has expired.
            </p>
            <p className="auth-footer">
              Log in and use "Resend email" in the banner to get a new link.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
