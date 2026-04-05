'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { signInWithEmail, isDemoMode } from '@/lib/auth';

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
