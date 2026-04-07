'use client';
import { useEffect } from 'react';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { grantFreeTrial } from '@/lib/auth';

const plans = [
  {
    name: 'Starter',
    
    price: 29,
    badge: null,
    features: [
      '10 AI edits per month',
      '1080p HD export',
      'All style presets & transitions',
      'Instagram Reel format',
      'Beat sync to music',
    ],
    cta: 'Get Started',
    href: 'https://www.fanbasis.com/agency-checkout/Dicipline/3wg3n?redirect=https://tubee.itsthatseason.com/editor',
    highlighted: false,
  },
  {
    name: 'Pro',
    price: 79,
    badge: 'Most Popular',
    features: [
      'Unlimited AI edits',
      '4K ultra export',
      'AI video generation (Veo 3.1)',
      'AI music generation (Lyria)',
      'Thumbnail generation',
      'Vibe Edit (Remotion)',
      'DaVinci Resolve export',
      'Priority processing',
      
    ],
    cta: 'Get Started',
    href: 'https://www.fanbasis.com/agency-checkout/Dicipline/4Lj20?redirect=https://tubee.itsthatseason.com/editor',
    highlighted: true,
  },
];

export default function PricingPage() {
  // Detect return from FanBasis payment
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('payment') === 'success' || document.referrer.includes('fanbasis.com')) {
      localStorage.setItem('tubee_paid', 'true');
      window.location.replace('https://tubee.itsthatseason.com/editor');
    }
  }, []);


  const router = useRouter();

  const handleFreeTrial = () => {
    grantFreeTrial();
    // Check if user is logged in, if not send to signup first
    if (typeof window !== 'undefined') {
      const session = localStorage.getItem('tubee_demo_user');
      if (!session) {
        router.push('/auth/signup');
        return;
      }
    }
    router.push('/editor');
  };

  return (
    <div style={{
      minHeight: '100vh', background: '#0A0F1E', color: '#fff',
      padding: '20px', paddingBottom: 80,
    }}>
      {/* Header */}
      <div style={{ maxWidth: 800, margin: '0 auto', paddingTop: 60 }}>
        <div style={{ textAlign: 'center', marginBottom: 48 }}>
          <Link href="/" style={{ textDecoration: 'none', fontSize: 24, fontWeight: 800, color: '#fff' }}>
            tubee<span style={{ color: '#00AAFF' }}>.</span>
          </Link>
          <h1 style={{
            fontSize: 40, fontWeight: 900, marginTop: 24, marginBottom: 12,
            letterSpacing: '-0.02em', lineHeight: 1.1,
          }}>
            Choose your plan
          </h1>
          <p style={{ color: '#8899BB', fontSize: 17, maxWidth: 500, margin: '0 auto', lineHeight: 1.6 }}>
            Start creating AI-powered video edits today. Cancel anytime.
          </p>
        </div>

        {/* Plans Grid */}
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: 20, maxWidth: 700, margin: '0 auto 40px',
        }}>
          {plans.map((plan) => (
            <div
              key={plan.name}
              style={{
                background: plan.highlighted ? 'rgba(0,170,255,0.05)' : '#0D1526',
                border: plan.highlighted ? '2px solid rgba(0,170,255,0.4)' : '1px solid rgba(0,170,255,0.15)',
                borderRadius: 20, padding: 32,
                position: 'relative',
                boxShadow: plan.highlighted ? '0 0 60px rgba(0,170,255,0.08)' : 'none',
                transform: plan.highlighted ? 'scale(1.02)' : 'none',
              }}
            >
              {plan.badge && (
                <div style={{
                  position: 'absolute', top: -12, left: '50%', transform: 'translateX(-50%)',
                  background: 'linear-gradient(135deg, #00AAFF, #00D4FF)',
                  color: '#fff', fontSize: 11, fontWeight: 800, textTransform: 'uppercase',
                  letterSpacing: '0.08em', padding: '6px 16px', borderRadius: 99,
                }}>
                  {plan.badge}
                </div>
              )}

              <h3 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>{plan.name}</h3>
              <div style={{ marginBottom: 24 }}>
                <span style={{ fontSize: 48, fontWeight: 900, letterSpacing: '-0.02em' }}>
                  ${plan.price}
                </span>
                <span style={{ color: '#8899BB', fontSize: 15 }}>/month</span>
              </div>

              <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 28px' }}>
                {plan.features.map((f) => (
                  <li key={f} style={{
                    display: 'flex', alignItems: 'flex-start', gap: 10,
                    marginBottom: 12, fontSize: 14, color: '#ccc', lineHeight: 1.5,
                  }}>
                    <span style={{ color: '#00AAFF', fontWeight: 700, flexShrink: 0, marginTop: 1 }}>✓</span>
                    {f}
                  </li>
                ))}
              </ul>

              <a
                href={plan.href}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: 'block', width: '100%', textAlign: 'center',
                  padding: '14px 20px', borderRadius: 14,
                  background: plan.highlighted
                    ? 'linear-gradient(135deg, #00AAFF, #00D4FF)'
                    : 'transparent',
                  border: plan.highlighted ? 'none' : '1px solid rgba(0,170,255,0.3)',
                  color: '#fff', fontWeight: 700, fontSize: 16,
                  textDecoration: 'none', cursor: 'pointer',
                  boxShadow: plan.highlighted ? '0 0 20px rgba(0,170,255,0.3)' : 'none',
                  transition: 'all 0.2s',
                  boxSizing: 'border-box',
                }}
              >
                {plan.cta}
              </a>
            </div>
          ))}
        </div>

        {/* Return to App */}
        <div style={{
          textAlign: 'center', maxWidth: 700, margin: '0 auto 40px',
          padding: '24px 20px',
          background: 'rgba(0,170,255,0.04)',
          border: '1px solid rgba(0,170,255,0.12)',
          borderRadius: 16,
        }}>
          <p style={{ color: '#8899BB', fontSize: 15, marginBottom: 14 }}>
            Already paid? Click here to access the app →
          </p>
          <Link
            href="/editor"
            style={{
              display: 'inline-block', padding: '12px 32px', borderRadius: 12,
              background: 'linear-gradient(135deg, #00AAFF, #00D4FF)',
              color: '#fff', fontWeight: 700, fontSize: 15,
              textDecoration: 'none',
              boxShadow: '0 0 15px rgba(0,170,255,0.2)',
              transition: 'all 0.2s',
            }}
          >
            Go to Editor →
          </Link>
        </div>

      </div>
    </div>
  );
}
