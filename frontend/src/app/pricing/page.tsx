'use client';
import { useEffect, useState } from 'react';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/components/AuthProvider';
import { supabase } from '@/lib/supabase';
import { apiBase, SKIP_NGROK } from '@/lib/api';
import { grantFreeTrial } from '@/lib/auth';

const plans = [
  {
    name: 'Starter',
    plan_key: 'starter' as const,
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
    highlighted: false,
  },
  {
    name: 'Pro',
    plan_key: 'pro' as const,
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
    highlighted: true,
  },
];

export default function PricingPage() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [currentPlan, setCurrentPlan] = useState<string | null>(null);
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null);
  const [portalLoading, setPortalLoading] = useState(false);
  const [error, setError] = useState('');

  // Check existing subscription status
  useEffect(() => {
    if (!user) return;

    const checkSubscription = async () => {
      try {
        const API = await apiBase();
        const res = await fetch(`${API}/subscription-status/${user.id}`, {
          headers: SKIP_NGROK,
        });
        if (res.ok) {
          const data = await res.json();
          if (data.is_paid) {
            setIsSubscribed(true);
            setCurrentPlan(data.plan);
          }
        }
      } catch (err) {
        console.error('Failed to check subscription:', err);
      }
    };
    checkSubscription();
  }, [user]);

  // Handle return from Stripe checkout
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('payment') === 'success') {
      // Payment succeeded — subscription will be activated via webhook
      // Redirect to editor
      window.location.replace('/editor?payment=success');
    }
  }, []);

  const handleCheckout = async (plan: 'starter' | 'pro') => {
    setError('');
    setCheckoutLoading(plan);

    try {
      // Get current user from Supabase
      const { data: { user: currentUser } } = await supabase.auth.getUser();
      if (!currentUser) {
        // Not logged in — send to signup
        router.push('/auth/signup');
        return;
      }

      const API = await apiBase();
      const res = await fetch(`${API}/create-checkout-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...SKIP_NGROK },
        body: JSON.stringify({
          plan,
          user_email: currentUser.email,
          user_id: currentUser.id,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: 'Checkout failed' }));
        throw new Error(errData.detail || 'Failed to create checkout session');
      }

      const { checkout_url } = await res.json();
      // Redirect to Stripe Checkout
      window.location.href = checkout_url;
    } catch (err: any) {
      setError(err.message || 'Something went wrong. Please try again.');
      console.error('Checkout error:', err);
    } finally {
      setCheckoutLoading(null);
    }
  };

  const handleManageSubscription = async () => {
    if (!user) return;
    setPortalLoading(true);
    setError('');

    try {
      const API = await apiBase();
      const res = await fetch(`${API}/create-portal-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...SKIP_NGROK },
        body: JSON.stringify({ user_id: user.id }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: 'Portal creation failed' }));
        throw new Error(errData.detail || 'Failed to open subscription portal');
      }

      const { portal_url } = await res.json();
      window.location.href = portal_url;
    } catch (err: any) {
      setError(err.message || 'Failed to open subscription management.');
      console.error('Portal error:', err);
    } finally {
      setPortalLoading(false);
    }
  };

  const handleFreeTrial = () => {
    grantFreeTrial();
    if (typeof window !== 'undefined') {
      const session = localStorage.getItem('tubee_demo_user');
      if (!session && !user) {
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

        {/* Error Banner */}
        {error && (
          <div style={{
            maxWidth: 700, margin: '0 auto 20px',
            padding: '12px 20px', borderRadius: 12,
            background: 'rgba(255,60,60,0.1)',
            border: '1px solid rgba(255,60,60,0.3)',
            color: '#ff6b6b', fontSize: 14, textAlign: 'center',
          }}>
            {error}
          </div>
        )}

        {/* Plans Grid */}
        <div style={{
          display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: 20, maxWidth: 700, margin: '0 auto 40px',
        }}>
          {plans.map((plan) => {
            const isCurrentPlan = isSubscribed && currentPlan === plan.plan_key;
            const isLoading = checkoutLoading === plan.plan_key;

            return (
              <div
                key={plan.name}
                style={{
                  background: plan.highlighted ? 'rgba(0,170,255,0.05)' : '#0D1526',
                  border: isCurrentPlan
                    ? '2px solid rgba(0,255,100,0.5)'
                    : plan.highlighted
                    ? '2px solid rgba(0,170,255,0.4)'
                    : '1px solid rgba(0,170,255,0.15)',
                  borderRadius: 20, padding: 32,
                  position: 'relative',
                  boxShadow: plan.highlighted ? '0 0 60px rgba(0,170,255,0.08)' : 'none',
                  transform: plan.highlighted ? 'scale(1.02)' : 'none',
                }}
              >
                {isCurrentPlan && (
                  <div style={{
                    position: 'absolute', top: -12, left: '50%', transform: 'translateX(-50%)',
                    background: 'linear-gradient(135deg, #00CC66, #00FF88)',
                    color: '#fff', fontSize: 11, fontWeight: 800, textTransform: 'uppercase',
                    letterSpacing: '0.08em', padding: '6px 16px', borderRadius: 99,
                  }}>
                    Current Plan
                  </div>
                )}
                {!isCurrentPlan && plan.badge && (
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

                {isCurrentPlan ? (
                  <button
                    onClick={handleManageSubscription}
                    disabled={portalLoading}
                    style={{
                      display: 'block', width: '100%', textAlign: 'center',
                      padding: '14px 20px', borderRadius: 14,
                      background: 'transparent',
                      border: '1px solid rgba(0,255,100,0.3)',
                      color: '#00FF88', fontWeight: 700, fontSize: 16,
                      cursor: portalLoading ? 'wait' : 'pointer',
                      opacity: portalLoading ? 0.6 : 1,
                      boxSizing: 'border-box',
                      transition: 'all 0.2s',
                    }}
                  >
                    {portalLoading ? 'Opening...' : 'Manage Subscription'}
                  </button>
                ) : (
                  <button
                    onClick={() => handleCheckout(plan.plan_key)}
                    disabled={isLoading || checkoutLoading !== null}
                    style={{
                      display: 'block', width: '100%', textAlign: 'center',
                      padding: '14px 20px', borderRadius: 14,
                      background: plan.highlighted
                        ? 'linear-gradient(135deg, #00AAFF, #00D4FF)'
                        : 'transparent',
                      border: plan.highlighted ? 'none' : '1px solid rgba(0,170,255,0.3)',
                      color: '#fff', fontWeight: 700, fontSize: 16,
                      cursor: isLoading ? 'wait' : 'pointer',
                      opacity: isLoading ? 0.6 : 1,
                      boxShadow: plan.highlighted ? '0 0 20px rgba(0,170,255,0.3)' : 'none',
                      transition: 'all 0.2s',
                      boxSizing: 'border-box',
                    }}
                  >
                    {isLoading ? 'Redirecting to checkout...' : plan.cta}
                  </button>
                )}
              </div>
            );
          })}
        </div>

        {/* Manage Subscription for subscribers */}
        {isSubscribed && (
          <div style={{
            textAlign: 'center', maxWidth: 700, margin: '0 auto 40px',
            padding: '24px 20px',
            background: 'rgba(0,255,100,0.04)',
            border: '1px solid rgba(0,255,100,0.12)',
            borderRadius: 16,
          }}>
            <p style={{ color: '#88BB99', fontSize: 15, marginBottom: 14 }}>
              You&apos;re on the <strong style={{ color: '#00FF88' }}>{currentPlan?.charAt(0).toUpperCase()}{currentPlan?.slice(1)}</strong> plan ✓
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
        )}

        {/* Return to App for non-subscribers */}
        {!isSubscribed && (
          <div style={{
            textAlign: 'center', maxWidth: 700, margin: '0 auto 40px',
            padding: '24px 20px',
            background: 'rgba(0,170,255,0.04)',
            border: '1px solid rgba(0,170,255,0.12)',
            borderRadius: 16,
          }}>
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
        )}
      </div>
    </div>
  );
}
