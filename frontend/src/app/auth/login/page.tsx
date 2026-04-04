'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { signInWithEmail, signInWithGoogle, isDemoMode } from '@/lib/auth';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const demoMode = isDemoMode();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const { error: authError } = await signInWithEmail(email, password);
      if (authError) {
        setError(authError.message);
        setLoading(false);
        return;
      }
      router.push('/editor');
    } catch {
      setError('Something went wrong. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh', background: '#0A0F1E', color: '#fff',
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
      padding: 20,
    }}>
      {demoMode && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0,
          background: 'linear-gradient(90deg, #FF6B00, #FF9500)',
          color: '#fff', textAlign: 'center', padding: '6px 12px',
          fontSize: 12, fontWeight: 600, zIndex: 100,
        }}>
          🔧 Demo Mode — Click &quot;Sign In&quot; with any email to continue
        </div>
      )}

      <div style={{ width: '100%', maxWidth: 420 }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <Link href="/" style={{ textDecoration: 'none', fontSize: 32, fontWeight: 800, color: '#fff' }}>
            tubee<span style={{ color: '#00AAFF' }}>.</span>
          </Link>
          <p style={{ color: '#8899BB', fontSize: 15, marginTop: 8 }}>
            Welcome back. Sign in to continue.
          </p>
        </div>

        {/* Google Sign In */}
        <button
          onClick={signInWithGoogle}
          style={{
            width: '100%', padding: '14px 20px', borderRadius: 12,
            background: '#fff', color: '#333', fontWeight: 600, fontSize: 15,
            border: 'none', cursor: 'pointer', marginBottom: 20,
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10,
          }}
        >
          <svg width="18" height="18" viewBox="0 0 18 18"><path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 01-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4"/><path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.26c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 009 18z" fill="#34A853"/><path d="M3.964 10.71A5.41 5.41 0 013.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 000 9c0 1.452.348 2.827.957 4.042l3.007-2.332z" fill="#FBBC05"/><path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 00.957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/></svg>
          Continue with Google
        </button>

        {/* Divider */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20,
        }}>
          <div style={{ flex: 1, height: 1, background: 'rgba(0,170,255,0.15)' }} />
          <span style={{ color: '#4a5a7a', fontSize: 13 }}>or</span>
          <div style={{ flex: 1, height: 1, background: 'rgba(0,170,255,0.15)' }} />
        </div>

        {/* Email Form */}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', color: '#8899BB', fontSize: 13, marginBottom: 6, fontWeight: 500 }}>
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              style={{
                width: '100%', padding: '12px 16px', borderRadius: 10,
                background: '#0D1526', border: '1px solid rgba(0,170,255,0.15)',
                color: '#fff', fontSize: 15, outline: 'none', boxSizing: 'border-box',
              }}
            />
          </div>

          <div style={{ marginBottom: 24 }}>
            <label style={{ display: 'block', color: '#8899BB', fontSize: 13, marginBottom: 6, fontWeight: 500 }}>
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              style={{
                width: '100%', padding: '12px 16px', borderRadius: 10,
                background: '#0D1526', border: '1px solid rgba(0,170,255,0.15)',
                color: '#fff', fontSize: 15, outline: 'none', boxSizing: 'border-box',
              }}
            />
          </div>

          {error && (
            <div style={{
              background: 'rgba(255,68,68,0.1)', border: '1px solid rgba(255,68,68,0.3)',
              borderRadius: 10, padding: '10px 14px', marginBottom: 16,
              color: '#ff6b6b', fontSize: 13,
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%', padding: '14px 20px', borderRadius: 12,
              background: loading ? '#1a2540' : 'linear-gradient(135deg, #00AAFF, #00D4FF)',
              color: loading ? '#4a5a7a' : '#fff', fontWeight: 700, fontSize: 16,
              border: 'none', cursor: loading ? 'not-allowed' : 'pointer',
              boxShadow: loading ? 'none' : '0 0 20px rgba(0,170,255,0.3)',
              transition: 'all 0.2s',
            }}
          >
            {loading ? 'Signing in…' : 'Sign In'}
          </button>
        </form>

        {/* Sign up link */}
        <p style={{ textAlign: 'center', marginTop: 24, color: '#8899BB', fontSize: 14 }}>
          Don&apos;t have an account?{' '}
          <Link href="/auth/signup" style={{ color: '#00AAFF', fontWeight: 600, textDecoration: 'none' }}>
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
