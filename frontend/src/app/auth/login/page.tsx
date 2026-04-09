'use client';
import { useState } from 'react';
import Link from 'next/link';
import { supabase } from '@/lib/supabase';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(false);
  const [showReset, setShowReset] = useState(false);

  async function handleLogin() {
    if (!email || !password) { setStatus('Enter email and password'); return; }
    setLoading(true);
    setStatus('Signing in...');
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email: email.trim(),
        password,
      });

      if (error || !data.session) {
        setStatus(error?.message || 'Wrong email or password. Try again.');
        setLoading(false);
        return;
      }

      setStatus('Success! Redirecting...');
      setTimeout(() => { window.location.href = '/editor'; }, 500);
    } catch {
      setStatus('Connection error. Try again.');
      setLoading(false);
    }
  }

  async function handleReset() {
    if (!email) { setStatus('Enter your email first'); return; }
    setLoading(true);
    const { error } = await supabase.auth.resetPasswordForEmail(email.trim(), {
      redirectTo: 'https://tubee.itsthatseason.com/auth/reset-password',
    });
    setLoading(false);
    if (!error) {
      setStatus('Reset email sent! Check your inbox.');
      setShowReset(false);
    } else {
      setStatus(error.message || 'Could not send reset email. Try again.');
    }
  }

  const s: React.CSSProperties = {
    width: '100%', padding: '16px', borderRadius: 12, marginBottom: 14,
    background: '#0D1526', border: '1px solid rgba(0,170,255,0.3)',
    color: '#fff', fontSize: 16, outline: 'none', boxSizing: 'border-box',
  };

  const b: React.CSSProperties = {
    width: '100%', padding: '16px', borderRadius: 12, border: 'none',
    background: 'linear-gradient(135deg, #00AAFF, #00D4FF)',
    color: '#fff', fontWeight: 800, fontSize: 17, cursor: 'pointer',
    touchAction: 'manipulation', userSelect: 'none',
  };

  return (
    <div style={{ minHeight: '100vh', background: '#0A0F1E', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
      <div style={{ width: '100%', maxWidth: 400 }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <Link href="/" style={{ textDecoration: 'none' }}>
            <h1 style={{ fontSize: 32, fontWeight: 900, color: '#00AAFF', margin: 0 }}>TUBEE</h1>
          </Link>
          <p style={{ color: '#8899BB', marginTop: 8 }}>Sign in to your account</p>
        </div>
        <div style={{ background: '#0D1526', borderRadius: 20, padding: 28, border: '1px solid rgba(0,170,255,0.15)' }}>
          {status && (
            <div style={{ background: status.includes('Success') || status.includes('sent') ? 'rgba(0,170,255,0.1)' : 'rgba(255,80,80,0.1)',
              border: `1px solid ${status.includes('Success') || status.includes('sent') ? '#00AAFF' : '#ff6b6b'}`,
              borderRadius: 10, padding: '12px 16px', marginBottom: 16,
              color: status.includes('Success') || status.includes('sent') ? '#00AAFF' : '#ff8888', fontSize: 15 }}>
              {status}
            </div>
          )}
          {!showReset ? (
            <>
              <input style={s} type="email" placeholder="Email address" value={email}
                onChange={e => setEmail(e.target.value)} autoCapitalize="none" autoCorrect="off" />
              <input style={s} type="password" placeholder="Password" value={password}
                onChange={e => setPassword(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleLogin()} />
              <button onClick={handleLogin} disabled={loading} style={{ ...b, opacity: loading ? 0.7 : 1, marginBottom: 12 }}>
                {loading ? 'Signing in...' : 'Sign In →'}
              </button>
              <button onClick={() => setShowReset(true)} style={{ background: 'none', border: 'none', color: '#00AAFF', cursor: 'pointer', fontSize: 14, width: '100%', padding: '8px 0' }}>
                Forgot password?
              </button>
            </>
          ) : (
            <>
              <p style={{ color: '#fff', marginBottom: 12 }}>Enter your email to reset password:</p>
              <input style={s} type="email" placeholder="Email address" value={email} onChange={e => setEmail(e.target.value)} />
              <button onClick={handleReset} disabled={loading} style={{ ...b, marginBottom: 12 }}>
                {loading ? 'Sending...' : 'Send Reset Email'}
              </button>
              <button onClick={() => setShowReset(false)} style={{ background: 'none', border: 'none', color: '#8899BB', cursor: 'pointer', fontSize: 14, width: '100%', padding: '8px 0' }}>
                ← Back to login
              </button>
            </>
          )}
          <div style={{ textAlign: 'center', marginTop: 20, color: '#8899BB', fontSize: 15 }}>
            No account? <Link href="/auth/signup" style={{ color: '#00AAFF', fontWeight: 700, textDecoration: 'none' }}>Sign up</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
