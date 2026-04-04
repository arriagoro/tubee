'use client';

import Link from 'next/link';

interface UpgradeModalProps {
  show: boolean;
  onClose: () => void;
}

export function UpgradeModal({ show, onClose }: UpgradeModalProps) {
  if (!show) return null;

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 200,
        background: 'rgba(0, 0, 0, 0.7)', backdropFilter: 'blur(8px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 20,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: '#0D1526', border: '1px solid rgba(0, 170, 255, 0.3)',
          borderRadius: 24, padding: 40, maxWidth: 440, width: '100%',
          textAlign: 'center',
          boxShadow: '0 0 60px rgba(0, 170, 255, 0.1)',
        }}
      >
        <div style={{ fontSize: 56, marginBottom: 16 }}>🔒</div>
        <h2 style={{ fontSize: 24, fontWeight: 800, marginBottom: 8, color: '#fff' }}>
          Free Trial Used
        </h2>
        <p style={{ color: '#8899BB', fontSize: 15, marginBottom: 28, lineHeight: 1.6 }}>
          You&apos;ve used your free edit. Upgrade to a paid plan to keep creating with Tubee.
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <Link
            href="/pricing"
            style={{
              display: 'block', padding: '16px 24px', borderRadius: 14,
              background: 'linear-gradient(135deg, #00AAFF, #00D4FF)',
              color: '#fff', fontWeight: 700, fontSize: 16, textDecoration: 'none',
              boxShadow: '0 0 20px rgba(0, 170, 255, 0.3)',
            }}
          >
            View Plans →
          </Link>
          <button
            onClick={onClose}
            style={{
              padding: '12px 24px', borderRadius: 14,
              border: '1px solid rgba(0, 170, 255, 0.15)',
              background: 'transparent', color: '#8899BB',
              fontSize: 14, cursor: 'pointer',
            }}
          >
            Maybe Later
          </button>
        </div>
      </div>
    </div>
  );
}
