'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState } from 'react'
import { useSession, signOut } from 'next-auth/react'

export default function Navigation() {
  const pathname = usePathname()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const { data: session, status } = useSession()

  const publicNavigation = [
    { name: 'Home', href: '/' },
    { name: 'Jobs', href: '/jobs' },
  ]

  const adminNavigation = [
    { name: 'Dashboard', href: '/dashboard' },
    { name: 'Pending Approvals', href: '/approvals' },
    { name: 'All Candidates', href: '/candidates' },
    { name: 'Jobs', href: '/jobs' },
  ]

  // Determine if we're on an admin route
  const isAdminRoute = pathname.startsWith('/dashboard') ||
                       pathname.startsWith('/approvals') ||
                       pathname.startsWith('/candidates')

  // Show admin navigation only on admin routes when logged in
  // Show public navigation on public routes (even if logged in)
  const navigation = (session && isAdminRoute) ? adminNavigation : publicNavigation

  const isActive = (href: string) => {
    if (href === '/') {
      return pathname === '/'
    }
    return pathname.startsWith(href)
  }

  return (
    <nav className="relative border-b"
         style={{
           background: 'var(--off-white)',
           borderColor: 'var(--warm-gray)'
         }}>
      <div className="max-w-7xl mx-auto px-6 lg:px-12">
        <div className="flex justify-between h-20">
          {/* Logo & Nav */}
          <div className="flex items-center gap-12">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-3 group">
              <div className="relative w-10 h-10 flex items-center justify-center"
                   style={{ background: 'var(--navy-deep)' }}>
                <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity"
                     style={{ background: 'var(--cyan-electric)' }} />
                <span className="relative z-10 font-display text-xl"
                      style={{ color: 'var(--off-white)' }}>
                  C
                </span>
              </div>
              <div className="hidden sm:block">
                <div className="font-display text-lg leading-none"
                     style={{ color: 'var(--navy-deep)' }}>
                  HireAI
                </div>
                <div className="font-mono text-xs uppercase tracking-wider"
                     style={{ color: 'var(--navy-mid)' }}>
                  Jobs Portal
                </div>
              </div>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center gap-1">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  href={item.href}
                  className="relative px-4 py-2 font-medium text-sm transition-colors"
                  style={{
                    color: isActive(item.href) ? 'var(--navy-deep)' : 'var(--navy-mid)'
                  }}
                >
                  {item.name}
                  {isActive(item.href) && (
                    <div className="absolute bottom-0 left-4 right-4 h-0.5"
                         style={{ background: 'var(--cyan-electric)' }} />
                  )}
                </Link>
              ))}
            </div>
          </div>

          {/* Right side - Auth (only when authenticated) */}
          <div className="hidden md:flex items-center gap-4">
            {session && (
              <>
                {/* Show Admin Panel link when on public pages */}
                {!isAdminRoute && (
                  <Link
                    href="/dashboard"
                    className="px-4 py-2 font-medium text-sm transition-all hover:opacity-80"
                    style={{
                      background: 'var(--navy-deep)',
                      color: 'var(--off-white)'
                    }}
                  >
                    Admin Panel
                  </Link>
                )}
                <div className="flex items-center gap-3 px-4 py-2 rounded-full"
                     style={{
                       background: 'rgba(10, 22, 40, 0.05)',
                       border: '1px solid var(--warm-gray)'
                     }}>
                  <div className="w-2 h-2 rounded-full"
                       style={{ background: 'var(--sage-green)' }} />
                  <span className="font-mono text-xs"
                        style={{ color: 'var(--navy-mid)' }}>
                    {session.user?.email}
                  </span>
                </div>
                <button
                  onClick={() => signOut({ callbackUrl: '/' })}
                  className="px-4 py-2 font-medium text-sm transition-colors hover:opacity-70"
                  style={{ color: 'var(--navy-mid)' }}
                >
                  Logout
                </button>
              </>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="flex items-center md:hidden">
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 transition-colors"
              style={{ color: 'var(--navy-mid)' }}
            >
              <span className="sr-only">Open menu</span>
              {!mobileMenuOpen ? (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              ) : (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t"
             style={{
               background: 'white',
               borderColor: 'var(--warm-gray)'
             }}>
          <div className="px-6 py-4 space-y-1">
            {navigation.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                onClick={() => setMobileMenuOpen(false)}
                className="block px-4 py-3 font-medium transition-colors"
                style={{
                  color: isActive(item.href) ? 'var(--navy-deep)' : 'var(--navy-mid)',
                  background: isActive(item.href) ? 'var(--off-white)' : 'transparent'
                }}
              >
                {item.name}
              </Link>
            ))}
          </div>
          {session && (
            <div className="px-6 py-4 border-t space-y-3"
                 style={{ borderColor: 'var(--warm-gray)' }}>
              {/* Show Admin Panel link when on public pages */}
              {!isAdminRoute && (
                <Link
                  href="/dashboard"
                  onClick={() => setMobileMenuOpen(false)}
                  className="block px-4 py-3 font-medium text-center transition-all"
                  style={{
                    background: 'var(--navy-deep)',
                    color: 'var(--off-white)'
                  }}
                >
                  Admin Panel
                </Link>
              )}
              <p className="font-mono text-xs px-4"
                 style={{ color: 'var(--navy-mid)' }}>
                {session.user?.email}
              </p>
              <button
                onClick={() => signOut({ callbackUrl: '/' })}
                className="w-full text-left px-4 py-3 font-medium transition-colors"
                style={{ color: 'var(--navy-mid)' }}
              >
                Logout
              </button>
            </div>
          )}
        </div>
      )}
    </nav>
  )
}
