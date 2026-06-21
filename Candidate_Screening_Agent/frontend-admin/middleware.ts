import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Auth is handled client-side by AuthProvider + (app)/layout.tsx
// Middleware only allows all requests through
export function middleware(request: NextRequest) {
  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
