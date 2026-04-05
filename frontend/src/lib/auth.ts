'use client';

import { supabase, isSupabaseConfigured } from './supabase';
import { User } from '@supabase/supabase-js';

// Demo mode user for when Supabase isn't configured
const DEMO_USER: User = {
  id: 'demo-user',
  email: 'demo@tubee.app',
  app_metadata: {},
  user_metadata: { full_name: 'Demo User' },
  aud: 'authenticated',
  created_at: new Date().toISOString(),
};

export function isDemoMode(): boolean {
  return !isSupabaseConfigured;
}

export async function getUser(): Promise<User | null> {
  if (isDemoMode()) {
    // In demo mode, check if user "signed in" via localStorage
    if (typeof window !== 'undefined' && localStorage.getItem('tubee_demo_auth')) {
      return DEMO_USER;
    }
    return null;
  }

  try {
    const { data: { user } } = await supabase.auth.getUser();
    return user;
  } catch {
    return null;
  }
}

export async function signInWithEmail(email: string, password: string) {
  if (isDemoMode()) {
    localStorage.setItem('tubee_demo_auth', 'true');
    return { user: DEMO_USER, error: null };
  }

  const { data, error } = await supabase.auth.signInWithPassword({ email, password });
  return { user: data.user, error };
}

export async function signUpWithEmail(email: string, password: string, name: string) {
  if (isDemoMode()) {
    localStorage.setItem('tubee_demo_auth', 'true');
    return { user: DEMO_USER, error: null };
  }

  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: { data: { full_name: name } },
  });
  
  // If signup succeeded but needs email confirmation, auto-sign them in
  if (data.user && !error) {
    const { data: signInData } = await supabase.auth.signInWithPassword({ email, password });
    if (signInData.user) return { user: signInData.user, error: null };
  }
  
  return { user: data.user, error };
}

export async function signInWithGoogle() {
  if (isDemoMode()) {
    localStorage.setItem('tubee_demo_auth', 'true');
    window.location.href = '/pricing';
    return;
  }

  await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: { redirectTo: 'https://tubee.itsthatseason.com/auth/callback' },
  });
}

export async function signOut() {
  if (isDemoMode()) {
    localStorage.removeItem('tubee_demo_auth');
    window.location.href = '/';
    return;
  }

  await supabase.auth.signOut();
  window.location.href = '/';
}

export function getUserInitials(user: User | null): string {
  if (!user) return '?';
  const name = user.user_metadata?.full_name || user.email || '';
  const parts = name.split(/[\s@]+/);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return name.slice(0, 2).toUpperCase();
}

export function getUserDisplayName(user: User | null): string {
  if (!user) return 'Guest';
  return user.user_metadata?.full_name || user.email?.split('@')[0] || 'User';
}

// Trial logic (localStorage-based for now)
export function hasUsedFreeTrial(): boolean {
  if (typeof window === 'undefined') return false;
  return localStorage.getItem('tubee_trial_used') === 'true';
}

export function markTrialUsed(): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem('tubee_trial_used', 'true');
  }
}

export function grantFreeTrial(): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem('tubee_free_trial_granted', 'true');
    localStorage.removeItem('tubee_trial_used');
  }
}

export function hasFreeTrialGranted(): boolean {
  if (typeof window === 'undefined') return false;
  return localStorage.getItem('tubee_free_trial_granted') === 'true';
}

// Plan status (localStorage-based for now, Supabase DB later)
export function getUserPlan(): 'none' | 'starter' | 'pro' | 'free_trial' {
  if (typeof window === 'undefined') return 'none';
  const plan = localStorage.getItem('tubee_plan');
  if (plan === 'starter' || plan === 'pro') return plan;
  if (hasFreeTrialGranted() && !hasUsedFreeTrial()) return 'free_trial';
  return 'none';
}

export function hasPaidPlan(): boolean {
  const plan = getUserPlan();
  return plan === 'starter' || plan === 'pro';
}

export function canUseEditor(): boolean {
  const plan = getUserPlan();
  return plan === 'starter' || plan === 'pro' || plan === 'free_trial';
}
