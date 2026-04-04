import { NextRequest, NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

const PROTECTED_ROUTES = ['/editor', '/generate', '/vibe', '/captions', '/upscale'];

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Only protect specific routes
  const isProtected = PROTECTED_ROUTES.some((route) => pathname.startsWith(route));
  if (!isProtected) return NextResponse.next();

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  // If Supabase isn't configured, allow access (demo mode)
  if (
    !supabaseUrl ||
    !supabaseAnonKey ||
    supabaseUrl === 'your-supabase-url' ||
    supabaseAnonKey === 'your-anon-key'
  ) {
    return NextResponse.next();
  }

  // Check for Supabase auth cookie
  const supabase = createClient(supabaseUrl, supabaseAnonKey, {
    global: {
      headers: {
        cookie: request.headers.get('cookie') || '',
      },
    },
  });

  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    // Not logged in → redirect to login
    const loginUrl = new URL('/auth/login', request.url);
    loginUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(loginUrl);
  }

  // User is logged in — allow access
  // Plan gating is handled client-side with the UpgradeModal
  return NextResponse.next();
}

export const config = {
  matcher: ['/editor/:path*', '/generate/:path*', '/vibe/:path*', '/captions/:path*', '/upscale/:path*'],
};
