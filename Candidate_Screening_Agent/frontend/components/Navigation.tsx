'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState } from 'react'

export default function Navigation() {
  const pathname = usePathname()
  const [open, setOpen] = useState(false)

  const isHome = pathname === '/'
  const dark = isHome

  const links = [
    { name: 'Find Jobs', href: '/jobs' },
  ]

  const active = (href: string) =>
    href === '/' ? pathname === '/' : pathname.startsWith(href)

  return (
    <nav
      className="sticky top-0 z-50 border-b backdrop-blur-md"
      style={{
        background: dark ? 'rgba(10,22,40,0.92)' : 'rgba(255,255,255,0.92)',
        borderColor: dark ? 'rgba(255,255,255,0.06)' : '#E5E7EB',
      }}
    >
      <div className="max-w-6xl mx-auto px-6 flex items-center justify-between h-14">
        {/* Left: Logo + nav */}
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-2.5 group">
            <span
              className="w-7 h-7 flex items-center justify-center text-xs font-bold rounded transition-transform group-hover:scale-105"
              style={{
                background: dark ? '#00E5FF' : '#0F172A',
                color: dark ? '#0A1628' : '#FFFFFF',
              }}
            >
              H
            </span>
            <span className="text-sm font-semibold tracking-tight"
                  style={{ color: dark ? '#FFFFFF' : '#0F172A' }}>
              HireAI
            </span>
          </Link>
          <div className="hidden sm:flex items-center gap-1">
            {links.map(l => (
              <Link
                key={l.href}
                href={l.href}
                className="px-3 py-1.5 text-sm font-medium rounded-md transition-colors"
                style={{
                  color: active(l.href)
                    ? (dark ? '#FFFFFF' : '#0F172A')
                    : (dark ? 'rgba(255,255,255,0.55)' : '#64748B'),
                  background: active(l.href)
                    ? (dark ? 'rgba(255,255,255,0.08)' : '#F1F5F9')
                    : 'transparent',
                }}
              >
                {l.name}
              </Link>
            ))}
          </div>
        </div>

        {/* Right: placeholder for future auth */}
        <div className="hidden sm:block" />

        {/* Mobile toggle */}
        <button onClick={() => setOpen(!open)} className="sm:hidden p-1.5"
                style={{ color: dark ? 'rgba(255,255,255,0.6)' : '#64748B' }}>
          {open ? (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            </svg>
          )}
        </button>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="sm:hidden border-t px-6 py-3 space-y-1"
             style={{
               background: dark ? 'rgba(10,22,40,0.97)' : '#FFFFFF',
               borderColor: dark ? 'rgba(255,255,255,0.06)' : '#E5E7EB'
             }}>
          <Link href="/jobs" onClick={() => setOpen(false)}
                className="block py-2.5 text-sm font-medium"
                style={{ color: dark ? 'rgba(255,255,255,0.7)' : '#64748B' }}>
            Find Jobs
          </Link>
        </div>
      )}
    </nav>
  )
}
