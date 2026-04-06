'use client';
import { useState } from 'react';
import Link from 'next/link';
import { supabase, isSupabaseConfigured } from '@/lib/supabase';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showReset, setShowReset] = useState(false);
  const [resetSent, setResetSent] = useState(false);

  const doLogin = async () => {
    if (!email || !password) { setError('Please enter email and password'); return; }
    setError('');
    setLoading(true);
    try {
      const { data, error: err } = await supabase.auth.signInWithPassword({ email: email.trim(), password });
      if (err) {
        setError('Wrong email or password. Try again.');
        setLoading(false);
        return;
      }
      if (data?.user) {
        // Small delay to ensure cookie is set before redirect
        setTimeout(() => {
          window.location.replace('https://tubee.itsthatseason.com/editor');
        }, 500);
      }
    } catch {
      setError('Something went wrong. Please try again.');
      setLoading(false);
    }
  };

  const doReset = async () => {
    if (!email) { setError('Enter your email first'); return; }
    setError('');
    setLoading(true);
    const { error: err } = await supabase.auth.resetPasswordForEmail(email.trim(), {
      redirectTo: 'https://tubee.itsthatseason.com/auth/reset-password'
    });
    setLoading(false);
    if (err) { setError(err.message); return; }
    setResetSent(true);
  };

  const inp: React.CSSProperties = {
    width: '100%', padding: '16px', borderRadius: 12, marginBottom: 14,
    background: '#0D1526', border: '1px solid rgba(0,170,255,0.3)',
    color: '#fff', fontSize: 16, outline: 'none', boxSizing: 'border-box',
    WebkitAppearance: 'none',
  };

  const btn: React.CSSProperties = {
    width: '100%', padding: '16px', borderRadius: 12, border: 'none',
    background: 'linear-gradient(135deg, #00AAFF, #00D4FF)',
    color: '#fff', fontWeight: 800, fontSize: 17,
    cursor: 'pointer', marginTop: 4, WebkitAppearance: 'none',
    touchAction: 'manipulation',
  };

  if (!isSupabaseConfigured) {
    return (
      <div style={{ minHeight: '100vh', background: '#0A0F1E', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
        <div style={{ color: '#ff6b6b', textAlign: 'center' }}>
          <p>Auth not configured. Contact support.</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', background: '#0A0F1E', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
      <div style={{ width: '100%', maxWidth: 400 }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <Link href="/" style={{ textDecoration: 'none' }}>
            <h1 style={{ fontSize: 32, fontWeight: 900, color: '#00AAFF', margin: 0, letterSpacing: -1 }}>TUBEE</h1>
          </Link>
          <p style={{ color: '#8899BB', marginTop: 8, fontSize: 16 }}>Sign in to your account</p>
        </div>

        <div style={{ background: '#0D1526', borderRadius: 20, padding: 28, border: '1px solid rgba(0,170,255,0.15)' }}>
          {error && (
            <div style={{ background: 'rgba(255,80,80,0.15)', border: '1px solid #ff6b6b', borderRadius: 10, padding: '14px 16px', marginBottom: 18, color: '#ff8888', fontSize: 15 }}>
              {error}
            </div>
          )}

          {resetSent ? (
            <div style={{ textAlign: 'center', padding: '20px 0' }}>
              <div style={{ fontSize: 48, marginBottom: 12 }}>📧</div>
              <h3 style={{ color: '#00AAFF', marginBottom: 8 }}>Reset Email Sent!</h3>
              <p style={{ color: '#8899BB', fontSize: 14 }}>Check your inbox and spam folder.</p>
              <button onClick={() => { setResetSent(false); setShowReset(false); }} style={{ ...btn, marginTop: 20, background: 'rgba(0,170,255,0.2)' }}>
                ← Back to Login
              </button>
            </div>
          ) : showReset ? (
            <div>
              <p style={{ color: '#fff', fontWeight: 700, marginBottom: 16, fontSize: 18 }}>Reset Password</p>
              <input style={inp} type="email" placeholder="Your email" value={email} onChange={e => setEmail(e.target.value)} />
              <button onClick={doReset} disabled={loading} style={{ ...btn, marginBottom: 12 }}>
                {loading ? 'Sending...' : 'Send Reset Email'}
              </button>
              <button onClick={() => setShowReset(false)} style={{ ...btn, background: 'rgba(255,255,255,0.05)', color: '#8899BB' }}>
                ← Back to Login
              </button>
            </div>
          ) : (
            <div>
              <input style={inp} type="email" placeholder="Email address" value={email} onChange={e => setEmail(e.target.value)} autoCapitalize="none" autoCorrect="off" />
              <input style={inp} type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} />
              <button onClick={() => { setShowReset(true); setError(''); }} style={{ background: 'none', border: 'none', color: '#00AAFF', cursor: 'pointer', fontSize: 14, marginBottom: 16, padding: 0, display: 'block' }}>
                Forgot password?
              </button>
              <button onClick={doLogin} disabled={loading} style={{ ...btn, opacity: loading ? 0.7 : 1 }}>
                {loading ? 'Signing in...' : 'Sign In →'}
              </button>
            </div>
          )}

          <div style={{ textAlign: 'center', marginTop: 24, color: '#8899BB', fontSize: 15 }}>
            No account?{' '}
            <Link href="/auth/signup" style={{ color: '#00AAFF', fontWeight: 700, textDecoration: 'none' }}>Sign up free</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
