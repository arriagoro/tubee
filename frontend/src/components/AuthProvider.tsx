'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { User } from '@supabase/supabase-js';
import { supabase, isSupabaseConfigured } from '@/lib/supabase';
import { getUser, isDemoMode } from '@/lib/auth';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  demoMode: boolean;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  demoMode: false,
});

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const demoMode = isDemoMode();

  useEffect(() => {
    // Initial load
    getUser().then((u) => {
      setUser(u);
      setLoading(false);
    });

    // Listen for auth changes (only if Supabase is configured)
    if (isSupabaseConfigured) {
      const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
        setUser(session?.user ?? null);
        setLoading(false);
      });
      return () => subscription.unsubscribe();
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, demoMode }}>
      {children}
    </AuthContext.Provider>
  );
}
