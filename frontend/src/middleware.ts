import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Temporarily allow all routes - auth is handled client-side
export function middleware(request: NextRequest) {
  return NextResponse.next();
}
