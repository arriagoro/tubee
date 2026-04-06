import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export async function GET(request: NextRequest) {
  const url = new URL(request.url);
  const token_hash = url.searchParams.get('token_hash');
  const type = url.searchParams.get('type');
  const code = url.searchParams.get('code');
  const error = url.searchParams.get('error');
  const error_description = url.searchParams.get('error_description');

  // Handle errors
  if (error) {
    return NextResponse.redirect(
      new URL(`/auth/login?error=${encodeURIComponent(error_description || error)}`, request.url)
    );
  }

  // Handle password recovery
  if (type === 'recovery' && token_hash) {
    return NextResponse.redirect(
      new URL(`/auth/reset-password?token_hash=${token_hash}&type=recovery`, request.url)
    );
  }

  // Handle email confirmation or OAuth
  if (code || (type === 'signup' && token_hash)) {
    return NextResponse.redirect(new URL('/editor', request.url));
  }

  // Default
  return NextResponse.redirect(new URL('/editor', request.url));
}
