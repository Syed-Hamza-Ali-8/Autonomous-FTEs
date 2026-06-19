'use client'

import { usePathname } from 'next/navigation'
import { useAuth } from '@/components/AuthProvider'
import AdminNav from '@/components/AdminNav'
import { ReactNode, useEffect } from 'react'

const PUBLIC_PATHS = ['/login', '/register']

export default function AppLayout({ children }: { children: ReactNode }) {
  const { user, loading, logout } = useAuth()
  const pathname = usePathname()
  const isPublic = PUBLIC_PATHS.some(p => pathname === p || pathname.startsWith(p + '/'))

  useEffect(() => { if (!loading && !user && !isPublic) { window.location.href = '/login' } }, [loading, user, isPublic])

  if (loading) return (<div className="flex items-center justify-center min-h-screen" style={{ background: 'var(--off-white)' }}><div className="text-center"><div className="relative w-16 h-16 mx-auto mb-6"><div className="absolute inset-0 rounded-full border-2 animate-spin" style={{ borderColor: 'var(--cyan-electric)', borderTopColor: 'transparent' }} /></div><p className="font-mono text-xs uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>Loading...</p></div></div>)
  if (isPublic) return <>{children}</>
  if (!user) return null
  return (<><AdminNav onLogout={logout} />{children}</>)
}
