import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Protected routes — must be logged in
const PROTECTED = ['/editor', '/generate', '/vibe', '/captions', '/upscale'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isProtected = PROTECTED.some(p => pathname.startsWith(p));
  
  if (isProtected) {
    // Check for Supabase auth cookie
    const token = request.cookies.get('sb-jorxyrqhjpffkgkjzrjr-auth-token') || 
                  request.cookies.get('sb-access-token') ||
                  request.cookies.get('supabase-auth-token');
    
    if (!token) {
      return NextResponse.redirect(new URL('/auth/login', request.url));
    }
  }
  
  return NextResponse.next();
}

export const config = {
  matcher: ['/editor/:path*', '/generate/:path*', '/vibe/:path*', '/captions/:path*', '/upscale/:path*'],
};
