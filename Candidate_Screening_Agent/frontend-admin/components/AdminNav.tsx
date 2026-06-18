'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'

export default function AdminNav() {
  const pathname = usePathname()
  const [pendingCount, setPendingCount] = useState(0)
  const [mobileOpen, setMobileOpen] = useState(false)

  const navigation = [
    { name: 'Dashboard', href: '/' },
    { name: 'Candidates', href: '/candidates' },
    { name: 'Approvals', href: '/approvals' },
    { name: 'Jobs', href: '/jobs' },
  ]

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/'
    return pathname.startsWith(href)
  }

  // Fetch pending approval count
  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/approvals/pending`)
      .then(r => r.json())
      .then(data => setPendingCount(data.length))
      .catch(() => {})
  }, [])

  return (
    <nav className="relative border-b"
         style={{ background: 'var(--off-white)', borderColor: 'var(--warm-gray)' }}>
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
                  Admin Panel
                </div>
                <div className="font-mono text-xs uppercase tracking-wider"
                     style={{ color: 'var(--navy-mid)' }}>
                  Candidate Screening
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
                  style={{ color: isActive(item.href) ? 'var(--navy-deep)' : 'var(--navy-mid)' }}
                >
                  {item.name}
                  {isActive(item.href) && (
                    <div className="absolute bottom-0 left-4 right-4 h-0.5"
                         style={{ background: 'var(--cyan-electric)' }} />
                  )}
                  {item.href === '/approvals' && pendingCount > 0 && (
                    <span className="ml-2 inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-white rounded-full"
                          style={{ background: 'var(--coral-warm)' }}>
                      {pendingCount}
                    </span>
                  )}
                </Link>
              ))}
            </div>
          </div>

          {/* Status indicator + Mobile hamburger */}
          <div className="flex items-center gap-3">
            <div className="hidden md:flex items-center gap-3 px-4 py-2 rounded-full"
                 style={{ background: 'rgba(10, 22, 40, 0.05)', border: '1px solid var(--warm-gray)' }}>
              <div className="w-2 h-2 rounded-full" style={{ background: 'var(--sage-green)' }} />
              <span className="font-mono text-xs" style={{ color: 'var(--navy-mid)' }}>
                Admin Mode
              </span>
            </div>

            {/* Mobile hamburger */}
            <button
              className="md:hidden flex items-center justify-center w-10 h-10 rounded-lg transition-colors"
              style={{ color: 'var(--navy-deep)' }}
              onClick={() => setMobileOpen(!mobileOpen)}
              aria-label="Toggle menu"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
        <div className="md:hidden border-t" style={{ borderColor: 'var(--warm-gray)', background: 'var(--off-white)' }}>
          <div className="px-6 py-4 space-y-1">
            {navigation.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className="block px-4 py-3 rounded-lg font-medium text-base transition-colors"
                style={{
                  color: isActive(item.href) ? 'var(--navy-deep)' : 'var(--navy-mid)',
                  background: isActive(item.href) ? 'rgba(10, 22, 40, 0.05)' : 'transparent',
                }}
                onClick={() => setMobileOpen(false)}
              >
                {item.name}
                {item.href === '/approvals' && pendingCount > 0 && (
                  <span className="ml-2 inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-white rounded-full"
                        style={{ background: 'var(--coral-warm)' }}>
                    {pendingCount}
                  </span>
                )}
              </Link>
            ))}
          </div>
        </div>
      )}
    </nav>
  )
}
