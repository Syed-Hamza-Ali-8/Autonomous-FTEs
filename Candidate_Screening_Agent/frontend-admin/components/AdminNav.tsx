'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'
import { useAuth } from '@/components/AuthProvider'

export default function AdminNav({ onLogout }: { onLogout?: () => void }) {
  const { user } = useAuth()
  const pathname = usePathname()
  const [pendingCount, setPendingCount] = useState(0)
  const [mobileOpen, setMobileOpen] = useState(false)

  const role = user?.role || ''
  const isSuperAdmin = role.includes('super_admin')

  // Super admin sees: Dashboard + Companies
  // Company admin sees: Dashboard + Candidates + Approvals + Jobs
  const navigation = isSuperAdmin
    ? [
        { name: 'Dashboard', href: '/' },
        { name: 'Companies', href: '/companies' },
      ]
    : [
        { name: 'Dashboard', href: '/' },
        { name: 'Candidates', href: '/candidates' },
        { name: 'Approvals', href: '/approvals' },
        { name: 'Jobs', href: '/jobs' },
      ]

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/'
    return pathname.startsWith(href)
  }

  useEffect(() => {
    const token = localStorage.getItem('auth_token')
    if (!token) return
    fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/approvals/pending`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(r => {
        if (r.status === 401) { try { localStorage.removeItem('auth_token') } catch {}; if (typeof window !== 'undefined') window.location.href = '/login'; return { length: 0 } }
        return r.json()
      })
      .then(data => setPendingCount(Array.isArray(data) ? data.length : 0))
      .catch(() => {})
  }, [])

  return (
    <nav className="relative glass-card border-b-0 rounded-b-2xl"
         style={{ borderColor: 'var(--warm-gray)' }}>
      <div className="max-w-7xl mx-auto px-6 lg:px-12">
        <div className="flex justify-between h-20">
          {/* Logo & Nav */}
          <div className="flex items-center gap-12">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-3 group">
              <div className="relative w-12 h-12 flex items-center justify-center rounded-xl overflow-hidden"
                   style={{ background: 'linear-gradient(135deg, var(--navy-deep), var(--navy-mid))' }}>
                {/* Animated gradient overlay */}
                <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                     style={{ background: 'linear-gradient(135deg, var(--cyan-electric), var(--sage-green))' }} />
                <span className="relative z-10 font-display text-2xl font-bold"
                      style={{ color: 'var(--off-white)' }}>
                  H
                </span>
              </div>
              <div className="hidden sm:block">
                <div className="font-display text-xl leading-none"
                     style={{ color: 'var(--navy-deep)' }}>
                  {isSuperAdmin ? 'Super Admin' : 'HireAI'}
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <div className="w-2 h-2 rounded-full" style={{ background: 'var(--sage-green)' }} />
                  <span className="font-mono text-xs" style={{ color: 'var(--navy-mid)' }}>
                    {isSuperAdmin ? 'Platform' : user?.company_name || 'Dashboard'}
                  </span>
                </div>
              </div>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden lg:flex items-center gap-1">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  href={item.href}
                  className="relative px-5 py-2.5 rounded-xl font-medium text-sm transition-all duration-200"
                  style={{
                    color: isActive(item.href) ? 'white' : 'var(--navy-mid)',
                    background: isActive(item.href) ? 'var(--navy-deep)' : 'transparent',
                  }}
                >
                  {item.name}
                  {item.href === '/approvals' && pendingCount > 0 && (
                    <span className="ml-2 inline-flex items-center justify-center w-5 h-5 text-xs font-bold rounded-full animate-pulse"
                          style={{ background: 'var(--coral-warm)', color: 'white' }}>
                      {pendingCount}
                    </span>
                  )}
                </Link>
              ))}
            </div>
          </div>

          {/* Right Side Actions */}
          <div className="flex items-center gap-4">
            {/* Live Indicator */}
            <div className="hidden md:flex items-center gap-2 px-4 py-2 rounded-full"
                 style={{ background: 'rgba(78, 205, 196, 0.1)', border: '1px solid rgba(78, 205, 196, 0.3)' }}>
              <div className="w-2 h-2 rounded-full animate-pulse" style={{ background: 'var(--sage-green)' }} />
              <span className="font-mono text-xs uppercase tracking-wider" style={{ color: 'var(--sage-green)' }}>
                Live
              </span>
            </div>

            {/* User Avatar */}
            <div className="hidden md:flex items-center gap-3 px-4 py-2 rounded-full"
                 style={{ background: 'var(--warm-gray)' }}>
              <div className="w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm"
                   style={{ background: 'var(--navy-deep)', color: 'var(--off-white)' }}>
                {user?.name?.charAt(0).toUpperCase() || 'U'}
              </div>
              <div className="text-sm">
                <div className="font-medium" style={{ color: 'var(--navy-deep)' }}>
                  {user?.name || 'User'}
                </div>
                <div className="font-mono text-xs" style={{ color: 'var(--navy-mid)' }}>
                  {user?.email || ''}
                </div>
              </div>
            </div>

            {/* Logout Button */}
            {onLogout && (
              <button
                className="hidden md:flex items-center gap-2 px-4 py-2 rounded-xl font-mono text-xs uppercase tracking-wider transition-all hover:opacity-80"
                style={{ color: 'var(--coral-warm)', border: '1px solid var(--coral-warm)' }}
                onClick={onLogout}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                Logout
              </button>
            )}

            {/* Mobile hamburger */}
            <button
              className="lg:hidden flex items-center justify-center w-12 h-12 rounded-xl transition-colors"
              style={{ color: 'var(--navy-deep)', background: 'var(--warm-gray)' }}
              onClick={() => setMobileOpen(!mobileOpen)}
              aria-label="Toggle menu"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {mobileOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="lg:hidden border-t" style={{ borderColor: 'var(--warm-gray)', background: 'white' }}>
          <div className="px-6 py-4 space-y-2">
            {navigation.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className="flex items-center justify-between px-4 py-3 rounded-xl font-medium transition-colors"
                style={{
                  color: isActive(item.href) ? 'white' : 'var(--navy-mid)',
                  background: isActive(item.href) ? 'var(--navy-deep)' : 'var(--warm-gray)',
                }}
                onClick={() => setMobileOpen(false)}
              >
                {item.name}
                {item.href === '/approvals' && pendingCount > 0 && (
                  <span className="inline-flex items-center justify-center w-5 h-5 text-xs font-bold rounded-full"
                        style={{ background: 'var(--coral-warm)', color: 'white' }}>
                    {pendingCount}
                  </span>
                )}
              </Link>
            ))}
            {onLogout && (
              <button
                className="flex items-center justify-center gap-2 w-full px-4 py-3 rounded-xl font-mono text-xs uppercase tracking-wider"
                style={{ color: 'var(--coral-warm)', border: '1px solid var(--coral-warm)' }}
                onClick={onLogout}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                Logout
              </button>
            )}
          </div>
        </div>
      )}
    </nav>
  )
}
