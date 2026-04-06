import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const token_hash = searchParams.get('token_hash');
  const type = searchParams.get('type');
  const next = searchParams.get('next') ?? '/editor';

  if (token_hash && type === 'recovery') {
    return NextResponse.redirect(
      new URL(`/auth/reset-password?token_hash=${token_hash}&type=${type}`, request.url)
    );
  }

  if (token_hash && type === 'signup') {
    return NextResponse.redirect(new URL('/editor', request.url));
  }

  return NextResponse.redirect(new URL(next, request.url));
}
