'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { signInWithEmail } from '@/lib/auth';
import { supabase } from '@/lib/supabase';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [resetSent, setResetSent] = useState(false);
  const [showReset, setShowReset] = useState(false);
  const [resetEmail, setResetEmail] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const { user, error: signInError } = await signInWithEmail(email.trim(), password);
      if (signInError) {
        const msg = signInError.message || String(signInError);
        if (msg.includes('Invalid login') || msg.includes('invalid_credentials')) {
          setError('Wrong email or password. Try again or use "Forgot password?" below.');
        } else if (msg.includes('Email not confirmed')) {
          setError('Please confirm your email first. Check your inbox.');
        } else {
          setError(msg);
        }
        return;
      }
      if (user) router.push('/editor');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    if (!resetEmail.trim()) { setError('Enter your email above'); return; }
    setLoading(true);
    const { error } = await supabase.auth.resetPasswordForEmail(resetEmail.trim(), {
      redirectTo: 'https://tubee.itsthatseason.com/auth/reset-password'
    });
    setLoading(false);
    if (error) { setError(error.message); return; }
    setResetSent(true);
  };

  const inputStyle = {
    width: '100%', padding: '14px 16px', borderRadius: 12,
    background: '#0D1526', border: '1px solid rgba(0,170,255,0.2)',
    color: '#fff', fontSize: 15, outline: 'none', boxSizing: 'border-box' as const,
    marginBottom: 14,
  };

  return (
    <div style={{ minHeight: '100vh', background: '#0A0F1E', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
      <div style={{ width: '100%', maxWidth: 420 }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <Link href="/" style={{ textDecoration: 'none' }}>
            <h1 style={{ fontSize: 28, fontWeight: 900, color: '#00AAFF', margin: 0 }}>TUBEE</h1>
          </Link>
          <p style={{ color: '#8899BB', marginTop: 8 }}>Sign in to your account</p>
        </div>

        <div style={{ background: '#0D1526', borderRadius: 20, padding: 32, border: '1px solid rgba(0,170,255,0.1)' }}>
          {resetSent ? (
            <div style={{ textAlign: 'center', padding: '20px 0' }}>
              <div style={{ fontSize: 48, marginBottom: 16 }}>📧</div>
              <h2 style={{ color: '#00AAFF', marginBottom: 8 }}>Reset Email Sent!</h2>
              <p style={{ color: '#8899BB' }}>Check your inbox (and spam) for a reset link from Supabase.</p>
              <button onClick={() => { setResetSent(false); setShowReset(false); }} style={{ marginTop: 16, color: '#00AAFF', background: 'none', border: 'none', cursor: 'pointer', fontSize: 14 }}>← Back to login</button>
            </div>
          ) : showReset ? (
            <div>
              <h3 style={{ color: '#fff', marginBottom: 16 }}>Reset Password</h3>
              {error && <div style={{ background: 'rgba(255,80,80,0.1)', border: '1px solid rgba(255,80,80,0.3)', borderRadius: 10, padding: '12px 16px', marginBottom: 16, color: '#ff6b6b', fontSize: 14 }}>{error}</div>}
              <input style={inputStyle} type="email" placeholder="Your email address" value={resetEmail} onChange={e => setResetEmail(e.target.value)} />
              <button onClick={handleReset} disabled={loading} style={{ width: '100%', padding: '15px', borderRadius: 12, border: 'none', background: 'linear-gradient(135deg, #00AAFF, #00D4FF)', color: '#fff', fontWeight: 700, fontSize: 16, cursor: 'pointer', marginBottom: 12 }}>
                {loading ? 'Sending...' : 'Send Reset Email'}
              </button>
              <button onClick={() => setShowReset(false)} style={{ width: '100%', background: 'none', border: 'none', color: '#8899BB', cursor: 'pointer', fontSize: 14 }}>← Back to login</button>
            </div>
          ) : (
            <form onSubmit={handleSubmit}>
              {error && <div style={{ background: 'rgba(255,80,80,0.1)', border: '1px solid rgba(255,80,80,0.3)', borderRadius: 10, padding: '12px 16px', marginBottom: 20, color: '#ff6b6b', fontSize: 14 }}>{error}</div>}
              <input style={inputStyle} type="email" placeholder="Email address" value={email} onChange={e => setEmail(e.target.value)} required />
              <input style={inputStyle} type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required />
              <button type="button" onClick={() => { setShowReset(true); setResetEmail(email); setError(''); }} style={{ background: 'none', border: 'none', color: '#00AAFF', cursor: 'pointer', fontSize: 13, marginBottom: 16, padding: 0 }}>
                Forgot password?
              </button>
              <button type="submit" disabled={loading} style={{ width: '100%', padding: '15px', borderRadius: 12, border: 'none', background: loading ? '#1a2540' : 'linear-gradient(135deg, #00AAFF, #00D4FF)', color: loading ? '#666' : '#fff', fontWeight: 700, fontSize: 16, cursor: loading ? 'not-allowed' : 'pointer' }}>
                {loading ? 'Signing in...' : 'Sign In →'}
              </button>
            </form>
          )}

          <div style={{ textAlign: 'center', marginTop: 24, color: '#8899BB', fontSize: 14 }}>
            Don&apos;t have an account?{' '}
            <Link href="/auth/signup" style={{ color: '#00AAFF', textDecoration: 'none', fontWeight: 600 }}>Sign up free</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
