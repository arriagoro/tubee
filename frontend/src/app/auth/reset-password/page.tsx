'use client';
import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { supabase } from '@/lib/supabase';

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    const token_hash = searchParams.get('token_hash');
    const type = searchParams.get('type');
    if (token_hash && type === 'recovery') {
      supabase.auth.verifyOtp({ token_hash, type: 'recovery' });
    }
  }, [searchParams]);

  const handleReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (password.length < 6) { setError('Password must be at least 6 characters'); return; }
    if (password !== confirmPassword) { setError('Passwords do not match'); return; }
    setLoading(true);
    const { error } = await supabase.auth.updateUser({ password });
    setLoading(false);
    if (error) { setError(error.message); return; }
    setSuccess(true);
    setTimeout(() => router.push('/editor'), 2000);
  };

  const inputStyle = {
    width: '100%', padding: '14px 16px', borderRadius: 12,
    background: '#0D1526', border: '1px solid rgba(0,170,255,0.2)',
    color: '#fff', fontSize: 15, outline: 'none', boxSizing: 'border-box' as const, marginBottom: 14,
  };

  return (
    <div style={{ minHeight: '100vh', background: '#0A0F1E', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
      <div style={{ width: '100%', maxWidth: 420 }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <Link href="/" style={{ textDecoration: 'none' }}>
            <h1 style={{ fontSize: 28, fontWeight: 900, color: '#00AAFF', margin: 0 }}>TUBEE</h1>
          </Link>
          <p style={{ color: '#8899BB', marginTop: 8 }}>Set your new password</p>
        </div>
        <div style={{ background: '#0D1526', borderRadius: 20, padding: 32, border: '1px solid rgba(0,170,255,0.1)' }}>
          {success ? (
            <div style={{ textAlign: 'center', padding: '20px 0' }}>
              <div style={{ fontSize: 48, marginBottom: 16 }}>✅</div>
              <h2 style={{ color: '#00AAFF' }}>Password Updated!</h2>
              <p style={{ color: '#8899BB' }}>Taking you to the editor...</p>
            </div>
          ) : (
            <form onSubmit={handleReset}>
              {error && <div style={{ background: 'rgba(255,80,80,0.1)', border: '1px solid rgba(255,80,80,0.3)', borderRadius: 10, padding: '12px 16px', marginBottom: 16, color: '#ff6b6b', fontSize: 14 }}>{error}</div>}
              <input style={inputStyle} type="password" placeholder="New password (min 6 characters)" value={password} onChange={e => setPassword(e.target.value)} required />
              <input style={inputStyle} type="password" placeholder="Confirm new password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} required />
              <button type="submit" disabled={loading} style={{ width: '100%', padding: '15px', borderRadius: 12, border: 'none', background: loading ? '#1a2540' : 'linear-gradient(135deg, #00AAFF, #00D4FF)', color: loading ? '#666' : '#fff', fontWeight: 700, fontSize: 16, cursor: loading ? 'not-allowed' : 'pointer' }}>
                {loading ? 'Updating...' : 'Set New Password →'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return <Suspense><ResetPasswordForm /></Suspense>;
}
