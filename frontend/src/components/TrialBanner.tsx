'use client';

import { useAuth } from './AuthProvider';
import { hasUsedFreeTrial, hasPaidPlan, hasFreeTrialGranted } from '@/lib/auth';
import { useEffect, useState } from 'react';

export function TrialBanner() {
  const { user } = useAuth();
  const [show, setShow] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (!user) return;
    const paid = hasPaidPlan();
    if (paid) { setShow(false); return; }

    const granted = hasFreeTrialGranted();
    const used = hasUsedFreeTrial();

    if (granted && !used) {
      setShow(true);
      setMessage('🎁 You have 1 free edit remaining. Make it count!');
    } else if (!granted) {
      setShow(true);
      setMessage('🎁 You have 1 free edit remaining. Make it count!');
    } else {
      setShow(false);
    }
  }, [user]);

  if (!show) return null;

  return (
    <div style={{
      background: 'linear-gradient(90deg, rgba(0,170,255,0.15), rgba(0,212,255,0.1))',
      border: '1px solid rgba(0,170,255,0.3)',
      borderRadius: 12, padding: '12px 16px', marginBottom: 16,
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      fontSize: 14,
    }}>
      <span style={{ color: '#00D4FF', fontWeight: 600 }}>{message}</span>
      <a
        href="/pricing"
        style={{
          color: '#00AAFF', fontWeight: 700, fontSize: 13,
          textDecoration: 'none', whiteSpace: 'nowrap',
        }}
      >
        Upgrade →
      </a>
    </div>
  );
}
