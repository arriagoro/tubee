'use client';
import { useState, useEffect, Suspense } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { supabase } from '@/lib/supabase';

function ResetPasswordForm() {
  const router = useRouter();
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // Supabase puts the access_token in the URL hash after redirect
    // e.g. /auth/reset-password#access_token=xxx&type=recovery
    const hash = window.location.hash;
    if (hash) {
      const params = new URLSearchParams(hash.substring(1));
      const access_token = params.get('access_token');
      const refresh_token = params.get('refresh_token');
      const type = params.get('type');
      
      if (access_token && type === 'recovery') {
        supabase.auth.setSession({ access_token, refresh_token: refresh_token || '' })
          .then(({ error }) => {
            if (error) {
              setError('Reset link expired. Please request a new one.');
            } else {
              setReady(true);
            }
          });
        return;
      }
    }
    
    // Also check query params
    const params = new URLSearchParams(window.location.search);
    const token_hash = params.get('token_hash');
    const type = params.get('type');
    
    if (token_hash && type === 'recovery') {
      supabase.auth.verifyOtp({ token_hash, type: 'recovery' })
        .then(({ error }) => {
          if (error) setError('Reset link expired. Please request a new one.');
          else setReady(true);
        });
    } else {
      // Check for existing session
      supabase.auth.getSession().then(({ data }) => {
        if (data.session) setReady(true);
        else setError('Invalid or expired reset link. Please request a new one.');
      });
    }
  }, []);

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
    setTimeout(async () => {
      await supabase.auth.signOut();
      router.push('/auth/login?reset=success');
    }, 2000);
  };

  const inputStyle = {
    width: '100%', padding: '14px 16px', borderRadius: 12,
    background: '#0D1526', border: '1px solid rgba(0,170,255,0.2)',
    color: '#fff', fontSize: 15, outline: 'none', boxSizing: 'border-box' as const, marginBottom: 14,
  };

  if (success) return (
    <div style={{ minHeight: '100vh', background: '#0A0F1E', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}>
      <div style={{ textAlign: 'center' }}>
        <div style={{ fontSize: 64, marginBottom: 16 }}>✅</div>
        <h2 style={{ color: '#00AAFF', marginBottom: 8 }}>Password Updated!</h2>
        <p style={{ color: '#8899BB' }}>Taking you to login...</p>
      </div>
    </div>
  );

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
          {!ready && !error && (
            <p style={{ color: '#8899BB', textAlign: 'center' }}>Verifying reset link...</p>
          )}
          {error && (
            <div style={{ textAlign: 'center' }}>
              <div style={{ background: 'rgba(255,80,80,0.1)', border: '1px solid rgba(255,80,80,0.3)', borderRadius: 10, padding: '16px', marginBottom: 20, color: '#ff6b6b', fontSize: 14 }}>{error}</div>
              <Link href="/auth/login" style={{ color: '#00AAFF', textDecoration: 'none', fontWeight: 600 }}>← Request new reset link</Link>
            </div>
          )}
          {ready && (
            <form onSubmit={handleReset}>
              <p style={{ color: '#8899BB', marginBottom: 20, fontSize: 14 }}>Enter your new password below.</p>
              <input style={inputStyle} type="password" placeholder="New password (min 6 characters)" value={password} onChange={e => setPassword(e.target.value)} required autoFocus />
              <input style={inputStyle} type="password" placeholder="Confirm new password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} required />
              {error && <div style={{ background: 'rgba(255,80,80,0.1)', border: '1px solid rgba(255,80,80,0.3)', borderRadius: 10, padding: '12px', marginBottom: 12, color: '#ff6b6b', fontSize: 14 }}>{error}</div>}
              <button type="submit" disabled={loading} style={{ width: '100%', padding: '15px', borderRadius: 12, border: 'none', background: loading ? '#1a2540' : 'linear-gradient(135deg, #00AAFF, #00D4FF)', color: loading ? '#666' : '#fff', fontWeight: 700, fontSize: 16, cursor: loading ? 'not-allowed' : 'pointer' }}>
                {loading ? 'Saving...' : 'Set New Password →'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return <Suspense fallback={<div style={{minHeight:'100vh',background:'#0A0F1E'}}/>}><ResetPasswordForm /></Suspense>;
}
