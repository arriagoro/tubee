'use client';

import Link from 'next/link';
import { useAuth } from './AuthProvider';
import { signOut, getUserInitials, getUserDisplayName } from '@/lib/auth';
import { useState } from 'react';

export function Navbar() {
  const { user, loading, demoMode } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <>
      {demoMode && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100,
          background: 'linear-gradient(90deg, #FF6B00, #FF9500)',
          color: '#fff', textAlign: 'center', padding: '6px 12px',
          fontSize: 12, fontWeight: 600,
        }}>
          🔧 Demo Mode — Supabase not configured. Auth is simulated.
        </div>
      )}
      <nav style={{
        position: 'fixed', top: demoMode ? 28 : 0, left: 0, right: 0, zIndex: 50,
        background: 'rgba(10, 15, 30, 0.8)', backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(0, 170, 255, 0.15)',
      }}>
        <div style={{
          maxWidth: 1152, margin: '0 auto', padding: '0 24px',
          height: 64, display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          {/* Logo */}
          <Link href="/" style={{ textDecoration: 'none', fontSize: 20, fontWeight: 700, letterSpacing: '-0.02em', color: '#fff' }}>
            tubee<span style={{ color: '#00AAFF' }}>.</span>
          </Link>

          {/* Right side */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {loading ? (
              <div style={{ width: 80, height: 36, background: '#0D1526', borderRadius: 8 }} />
            ) : user ? (
              /* Logged in */
              <div style={{ position: 'relative' }}>
                <button
                  onClick={() => setMenuOpen(!menuOpen)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 8,
                    background: 'rgba(0, 170, 255, 0.1)', border: '1px solid rgba(0, 170, 255, 0.2)',
                    borderRadius: 12, padding: '6px 12px 6px 6px', cursor: 'pointer', color: '#fff',
                  }}
                >
                  <div style={{
                    width: 32, height: 32, borderRadius: 8,
                    background: 'linear-gradient(135deg, #00AAFF, #00D4FF)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 13, fontWeight: 700, color: '#fff',
                  }}>
                    {getUserInitials(user)}
                  </div>
                  <span style={{ fontSize: 14, fontWeight: 500, color: '#ccc' }}>
                    {getUserDisplayName(user)}
                  </span>
                </button>

                {menuOpen && (
                  <>
                    <div
                      onClick={() => setMenuOpen(false)}
                      style={{ position: 'fixed', inset: 0, zIndex: 40 }}
                    />
                    <div style={{
                      position: 'absolute', top: '110%', right: 0, zIndex: 50,
                      background: '#0D1526', border: '1px solid rgba(0, 170, 255, 0.2)',
                      borderRadius: 12, padding: 4, minWidth: 180,
                      boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
                    }}>
                      <Link
                        href="/pricing"
                        onClick={() => setMenuOpen(false)}
                        style={{
                          display: 'block', padding: '10px 14px', borderRadius: 8,
                          color: '#8899BB', fontSize: 14, textDecoration: 'none',
                        }}
                      >
                        💎 Plans & Pricing
                      </Link>
                      <button
                        onClick={() => { setMenuOpen(false); signOut(); }}
                        style={{
                          display: 'block', width: '100%', padding: '10px 14px', borderRadius: 8,
                          color: '#ff6b6b', fontSize: 14, border: 'none', background: 'transparent',
                          cursor: 'pointer', textAlign: 'left',
                        }}
                      >
                        🚪 Sign Out
                      </button>
                    </div>
                  </>
                )}
              </div>
            ) : (
              /* Logged out */
              <>
                <Link
                  href="/auth/login"
                  style={{
                    color: '#8899BB', fontSize: 14, fontWeight: 500,
                    textDecoration: 'none', padding: '8px 16px',
                  }}
                >
                  Sign In
                </Link>
                <Link
                  href="/auth/signup"
                  style={{
                    background: '#00AAFF', color: '#fff', fontWeight: 600,
                    padding: '8px 20px', borderRadius: 10, fontSize: 14,
                    textDecoration: 'none',
                    boxShadow: '0 0 20px rgba(0, 170, 255, 0.3)',
                  }}
                >
                  Get Started
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>
    </>
  );
}
