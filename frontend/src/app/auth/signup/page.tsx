'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { signUpWithEmail } from '@/lib/auth';

export default function SignupPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setError('');

    if (!name.trim()) { setError('Please enter your name'); return; }
    if (!email.trim()) { setError('Please enter your email'); return; }
    if (password.length < 6) { setError('Password must be at least 6 characters'); return; }
    if (password !== confirmPassword) { setError('Passwords do not match'); return; }

    setLoading(true);
    try {
      const { user, error: signUpError } = await signUpWithEmail(email.trim(), password, name.trim());
      if (signUpError) {
        const msg = signUpError.message || String(signUpError);
        if (msg.includes('already registered') || msg.includes('already exists')) {
          setError('An account with this email already exists. Try logging in instead.');
        } else if (msg.includes('invalid')) {
          setError('Please enter a valid email address.');
        } else {
          setError(msg);
        }
        return;
      }
      if (user) {
        setSuccess(true);
        setTimeout(() => router.push('/editor'), 1500);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
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
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <Link href="/" style={{ textDecoration: 'none' }}>
            <h1 style={{ fontSize: 28, fontWeight: 900, color: '#00AAFF', margin: 0 }}>TUBEE</h1>
          </Link>
          <p style={{ color: '#8899BB', marginTop: 8 }}>Create your account</p>
        </div>

        <div style={{ background: '#0D1526', borderRadius: 20, padding: 32, border: '1px solid rgba(0,170,255,0.1)' }}>
          {success ? (
            <div style={{ textAlign: 'center', padding: '20px 0' }}>
              <div style={{ fontSize: 48, marginBottom: 16 }}>✅</div>
              <h2 style={{ color: '#00AAFF', marginBottom: 8 }}>Account Created!</h2>
              <p style={{ color: '#8899BB' }}>Taking you to the editor...</p>
            </div>
          ) : (
            <div>
              {error && (
                <div style={{ background: 'rgba(255,80,80,0.1)', border: '1px solid rgba(255,80,80,0.3)', borderRadius: 10, padding: '12px 16px', marginBottom: 20, color: '#ff6b6b', fontSize: 14 }}>
                  {error}
                </div>
              )}

              <input style={inputStyle} type="text" placeholder="Full name" value={name} onChange={e => setName(e.target.value)} />
              <input style={inputStyle} type="email" placeholder="Email address" value={email} onChange={e => setEmail(e.target.value)} />
              <input style={inputStyle} type="password" placeholder="Password (min 6 characters)" value={password} onChange={e => setPassword(e.target.value)} />
              <input style={inputStyle} type="password" placeholder="Confirm password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} />

              <button type="button" onClick={() => handleSubmit()} disabled={loading} style={{
                width: '100%', padding: '15px', borderRadius: 12, border: 'none',
                background: loading ? '#1a2540' : 'linear-gradient(135deg, #00AAFF, #00D4FF)',
                color: loading ? '#666' : '#fff', fontWeight: 700, fontSize: 16,
                cursor: loading ? 'not-allowed' : 'pointer', marginTop: 4,
              }}>
                {loading ? 'Creating account...' : 'Create Account →'}
              </button>
            </div>
          )}

          <div style={{ textAlign: 'center', marginTop: 24, color: '#8899BB', fontSize: 14 }}>
            Already have an account?{' '}
            <Link href="/auth/login" style={{ color: '#00AAFF', textDecoration: 'none', fontWeight: 600 }}>Sign in</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
