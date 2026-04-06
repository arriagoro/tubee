import { createClient } from '@supabase/supabase-js';

// Hardcoded - no env vars needed
const SUPABASE_URL = 'https://jorxyrqhjpffkgkjzrjr.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Impvcnh5cnFoanBmZmtna2p6cmpyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUzMDgyMTksImV4cCI6MjA5MDg4NDIxOX0.0FQUzEPNfFiQnMPfdFDdlBeIb6tm8o10cEAgnMXyUAU';

export const isSupabaseConfigured = true;
export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
