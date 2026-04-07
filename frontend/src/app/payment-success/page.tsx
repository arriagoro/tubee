'use client';
import { useEffect } from 'react';

export default function PaymentSuccess() {
  useEffect(() => {
    // Mark as paid and redirect to editor
    localStorage.setItem('tubee_paid', 'true');
    setTimeout(() => {
      window.location.replace('https://tubee.itsthatseason.com/editor');
    }, 1500);
  }, []);

  return (
    <div style={{ minHeight: '100vh', background: '#0A0F1E', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ textAlign: 'center', color: '#fff' }}>
        <div style={{ fontSize: 64, marginBottom: 16 }}>✅</div>
        <h1 style={{ color: '#00AAFF', marginBottom: 8 }}>Payment Successful!</h1>
        <p style={{ color: '#8899BB' }}>Taking you to the editor...</p>
      </div>
    </div>
  );
}
