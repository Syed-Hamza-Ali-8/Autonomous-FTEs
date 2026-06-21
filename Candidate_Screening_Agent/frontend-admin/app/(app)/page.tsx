'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/components/AuthProvider'
import Link from 'next/link'

function handleUnauthorized(r: Response): Promise<any> {
  if (r.status === 401) {
    try { localStorage.removeItem('auth_token') } catch {}
    if (typeof window !== 'undefined') window.location.href = '/login'
    return Promise.resolve(null)
  }
  return r.json()
}

export default function Dashboard() {
  const { user, loading } = useAuth()
  const [companies, setCompanies] = useState<any[]>([])
  const [loadingCompanies, setLoadingCompanies] = useState(true)

  useEffect(() => {
    if (!user) return
    if (user.role === 'super_admin') {
      fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/companies`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
      }).then(handleUnauthorized).then(d => { if (d) setCompanies(Array.isArray(d) ? d : []) }).finally(() => setLoadingCompanies(false))
    }
  }, [user])

  if (loading || !user) return null

  if (user.role === 'super_admin') {
    if (loadingCompanies) return (<div className="flex items-center justify-center min-h-[60vh]" style={{ background: 'var(--off-white)' }}><div className="text-center"><div className="relative w-16 h-16 mx-auto mb-6"><div className="absolute inset-0 rounded-full border-2 animate-spin" style={{ borderColor: 'var(--cyan-electric)', borderTopColor: 'transparent' }} /></div><p className="font-mono text-sm uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>Loading platform data...</p></div></div>)

    const totalCompanies = companies.length
    const totalUsers = companies.reduce((s: number, c: any) => s + c.user_count, 0)
    const totalJobs = companies.reduce((s: number, c: any) => s + c.job_count, 0)
    const totalCandidates = companies.reduce((s: number, c: any) => s + c.candidate_count, 0)
    const activeCompanies = companies.filter((c: any) => c.is_active).length
    const avgCandidatesPerCompany = totalCompanies > 0 ? Math.round(totalCandidates / totalCompanies) : 0

    return (
      <div className="max-w-7xl mx-auto px-6 lg:px-12 py-16">
        <div className="mb-16">
          <div className="font-mono text-xs uppercase tracking-wider mb-4" style={{ color: 'var(--navy-mid)' }}>Platform Overview</div>
          <h1 className="font-display text-5xl lg:text-6xl leading-tight mb-4" style={{ color: 'var(--navy-deep)' }}>Welcome back, {user.name}</h1>
          <p className="text-xl leading-relaxed" style={{ color: 'var(--navy-light)' }}>Monitor all companies and hiring activity across the platform.</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
          {[
            { label: 'Active Companies', value: activeCompanies, icon: '🏢' },
            { label: 'Total Users', value: totalUsers, icon: '👥' },
            { label: 'Jobs Posted', value: totalJobs, icon: '💼' },
            { label: 'Candidates Screened', value: totalCandidates, icon: '📋' },
            { label: 'Avg Candidates/Company', value: avgCandidatesPerCompany, icon: '📊' },
          ].map(s => (
            <div key={s.label} className="p-8 rounded-xl" style={{ background: 'white', border: '1px solid var(--warm-gray)' }}>
              <div className="text-3xl mb-3">{s.icon}</div>
              <div className="font-display text-4xl mb-1" style={{ color: 'var(--cyan-electric)' }}>{s.value}</div>
              <div className="font-mono text-xs uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>{s.label}</div>
            </div>
          ))}
        </div>

        {/* CTA */}
        <Link href="/companies" className="inline-flex items-center gap-3 px-8 py-4 rounded-xl font-medium transition-all hover:opacity-90"
              style={{ background: 'var(--navy-deep)', color: 'var(--off-white)' }}>
          Manage Companies
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" /></svg>
        </Link>
      </div>
    )
  }

  // Company admin dashboard - pipeline view
  const [candidates, setCandidates] = useState<any[]>([])
  const [pendingApprovals, setPendingApprovals] = useState<any[]>([])
  const [jobs, setJobs] = useState<any[]>([])
  const [dataLoading, setDataLoading] = useState(true)

  useEffect(() => {
    if (!user || user.role === 'super_admin') return
    const token = localStorage.getItem('auth_token')
    const headers = { 'Authorization': `Bearer ${token}` }
    Promise.all([
      fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/candidates`, { headers }).then(handleUnauthorized),
      fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/approvals/pending`, { headers }).then(handleUnauthorized),
      fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/jobs`, { headers }).then(handleUnauthorized),
    ]).then(([c, a, j]) => {
      setCandidates(Array.isArray(c) ? c : [])
      setPendingApprovals(Array.isArray(a) ? a : [])
      setJobs(Array.isArray(j) ? j : [])
    }).finally(() => setDataLoading(false))
  }, [user])

  if (dataLoading) return (<div className="flex items-center justify-center min-h-[60vh]" style={{ background: 'var(--off-white)' }}><div className="text-center"><div className="relative w-16 h-16 mx-auto mb-6"><div className="absolute inset-0 rounded-full border-2 animate-spin" style={{ borderColor: 'var(--cyan-electric)', borderTopColor: 'transparent' }} /></div><p className="font-mono text-sm uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>Loading dashboard...</p></div></div>)

  const byStatus: Record<string, number> = {}
  candidates.forEach((c: any) => { byStatus[c.status] = (byStatus[c.status] || 0) + 1 })
  const today = new Date().toDateString()
  const todayApplications = candidates.filter((c: any) => new Date(c.created_at).toDateString() === today).length
  const shortlisted = byStatus['shortlisted'] || 0
  const rejected = byStatus['rejected'] || 0
  const awaitingReply = byStatus['awaiting_reply'] || 0

  return (
    <div className="max-w-7xl mx-auto px-6 lg:px-12 py-16">
      <div className="mb-12">
        <div className="font-mono text-xs uppercase tracking-wider mb-4" style={{ color: 'var(--navy-mid)' }}>{user.company_name} — Dashboard</div>
        <h1 className="font-display text-5xl lg:text-6xl leading-tight mb-4" style={{ color: 'var(--navy-deep)' }}>Welcome back, {user.name}</h1>
        <p className="text-xl" style={{ color: 'var(--navy-light)' }}>Your hiring pipeline overview. Auto-refreshes every 30 seconds.</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
        {[
          { label: 'Today', value: todayApplications, href: '/candidates', icon: '📥' },
          { label: 'Awaiting Reply', value: awaitingReply, href: '/candidates', icon: '⏳' },
          { label: 'Shortlisted', value: shortlisted, href: '/candidates?status=shortlisted', icon: '⭐' },
          { label: 'Pending Approval', value: pendingApprovals.length, href: '/approvals', icon: '🔔' },
        ].map(s => (
          <Link key={s.label} href={s.href} className="p-6 rounded-xl block transition-all hover:opacity-80" style={{ background: 'white', border: '1px solid var(--warm-gray)' }}>
            <div className="text-2xl mb-2">{s.icon}</div>
            <div className="font-display text-3xl mb-1" style={{ color: 'var(--cyan-electric)' }}>{s.value}</div>
            <div className="font-mono text-xs uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>{s.label}</div>
          </Link>
        ))}
      </div>

      {/* Quick Links */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[
          { label: 'Candidates', desc: 'View and manage all candidates', href: '/candidates', icon: '👤', count: candidates.length },
          { label: 'Jobs', desc: 'Manage job postings', href: '/jobs', icon: '💼', count: jobs.length },
          { label: 'Approvals', desc: 'Review pending decisions', href: '/approvals', icon: '✅', count: pendingApprovals.length },
        ].map(card => (
          <Link key={card.label} href={card.href} className="p-8 rounded-xl block transition-all hover:opacity-80" style={{ background: 'white', border: '1px solid var(--warm-gray)' }}>
            <div className="text-3xl mb-4">{card.icon}</div>
            <div className="font-display text-xl mb-2" style={{ color: 'var(--navy-deep)' }}>{card.label}</div>
            <div className="text-sm mb-4" style={{ color: 'var(--navy-light)' }}>{card.desc}</div>
            <div className="font-mono text-sm" style={{ color: 'var(--cyan-electric)' }}>{card.count} {card.label.toLowerCase()}</div>
          </Link>
        ))}
      </div>
    </div>
  )
}
