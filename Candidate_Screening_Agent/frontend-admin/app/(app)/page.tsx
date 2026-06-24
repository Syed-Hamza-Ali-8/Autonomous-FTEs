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

// Animated counter hook
function useAnimatedCounter(value: number, duration: number = 1000) {
  const [count, setCount] = useState(0)
  useEffect(() => {
    let start = 0
    const end = value
    if (end === 0) { setCount(0); return }
    const increment = end / (duration / 16)
    const timer = setInterval(() => {
      start += increment
      if (start >= end) { setCount(end); clearInterval(timer) }
      else setCount(Math.floor(start))
    }, 16)
    return () => clearInterval(timer)
  }, [value, duration])
  return count
}

// Progress ring component
function ProgressRing({ value, max, color, size = 80, stroke = 8 }: { value: number, max: number, color: string, size?: number, stroke?: number }) {
  const radius = (size - stroke) / 2
  const circumference = radius * 2 * Math.PI
  const offset = circumference - (value / max) * circumference
  return (
    <svg width={size} height={size} className="transform -rotate-90">
      <circle cx={size/2} cy={size/2} r={radius} fill="none" stroke="var(--warm-gray)" strokeWidth={stroke} />
      <circle cx={size/2} cy={size/2} r={radius} fill="none" stroke={color} strokeWidth={stroke}
        strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round"
        style={{ transition: 'stroke-dashoffset 1s ease-out' }} />
    </svg>
  )
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
    const totalCompanies = companies.length
    const totalUsers = companies.reduce((s: number, c: any) => s + c.user_count, 0)
    const totalJobs = companies.reduce((s: number, c: any) => s + c.job_count, 0)
    const totalCandidates = companies.reduce((s: number, c: any) => s + c.candidate_count, 0)
    const activeCompanies = companies.filter((c: any) => c.is_active).length

    return (
      <div className="min-h-screen grid-pattern">
        {/* Hero Section */}
        <div className="relative overflow-hidden" style={{ background: 'linear-gradient(135deg, var(--navy-deep) 0%, var(--navy-mid) 100%)' }}>
          {/* Decorative Elements */}
          <div className="absolute top-0 right-0 w-[600px] h-[600px] opacity-10">
            <div className="absolute top-0 right-0 w-96 h-96 rounded-full" style={{ background: 'var(--cyan-electric)', filter: 'blur(100px)' }} />
          </div>
          <div className="absolute bottom-0 left-0 w-[400px] h-[400px] opacity-10">
            <div className="absolute bottom-0 left-0 w-72 h-72 rounded-full" style={{ background: 'var(--sage-green)', filter: 'blur(80px)' }} />
          </div>

          <div className="max-w-7xl mx-auto px-6 lg:px-12 py-20 relative z-10">
            <div className="reveal-up">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full mb-8"
                   style={{ background: 'rgba(0, 229, 255, 0.1)', border: '1px solid rgba(0, 229, 255, 0.3)' }}>
                <div className="w-2 h-2 rounded-full pulse-live" style={{ background: 'var(--sage-green)' }} />
                <span className="font-mono text-xs uppercase tracking-wider" style={{ color: 'var(--cyan-electric)' }}>Platform Control Center</span>
              </div>
            </div>

            <h1 className="font-display text-5xl lg:text-7xl leading-tight mb-6 reveal-up reveal-delay-1" style={{ color: 'white' }}>
              Welcome back,<br />
              <span className="gradient-text">{user.name}</span>
            </h1>
            <p className="text-xl leading-relaxed max-w-2xl reveal-up reveal-delay-2" style={{ color: 'rgba(255,255,255,0.7)' }}>
              Monitor all companies and hiring activity across the platform in real-time.
            </p>
          </div>
        </div>

        {/* Stats Section */}
        <div className="max-w-7xl mx-auto px-6 lg:px-12 -mt-12 relative z-20">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { label: 'Active Companies', value: activeCompanies, icon: '🏢', color: 'var(--cyan-electric)', gradient: 'linear-gradient(135deg, var(--cyan-electric), var(--sage-green))' },
              { label: 'Total Users', value: totalUsers, icon: '👥', color: 'var(--sage-green)', gradient: 'linear-gradient(135deg, var(--sage-green), var(--cyan-glow))' },
              { label: 'Jobs Posted', value: totalJobs, icon: '💼', color: 'var(--gold-accent)', gradient: 'linear-gradient(135deg, var(--gold-accent), var(--coral-warm))' },
              { label: 'Candidates', value: totalCandidates, icon: '📋', color: 'var(--coral-warm)', gradient: 'linear-gradient(135deg, var(--coral-warm), var(--coral-soft))' },
            ].map((s, i) => (
              <div key={s.label} className="glass-card rounded-2xl p-6 hover-lift reveal-up" style={{ animationDelay: `${0.1 * i}s` }}>
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl"
                       style={{ background: s.gradient }}>
                    {s.icon}
                  </div>
                  <ProgressRing value={s.value} max={Math.max(s.value, 1)} color={s.color} size={48} stroke={4} />
                </div>
                <div className="font-display text-4xl mb-1" style={{ color: 'var(--navy-deep)' }}>{s.value}</div>
                <div className="font-mono text-xs uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>{s.label}</div>
              </div>
            ))}
          </div>

          {/* Quick Actions */}
          <div className="mt-12 mb-12">
            <h2 className="font-display text-2xl mb-6" style={{ color: 'var(--navy-deep)' }}>Quick Actions</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Link href="/companies" className="group p-6 rounded-2xl transition-all hover-lift"
                    style={{ background: 'white', border: '1px solid var(--warm-gray)' }}>
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 rounded-xl flex items-center justify-center text-2xl gradient-border"
                       style={{ background: 'linear-gradient(135deg, rgba(0, 229, 255, 0.1), rgba(78, 205, 196, 0.1))' }}>
                    🏢
                  </div>
                  <div className="flex-1">
                    <div className="font-display text-lg mb-1" style={{ color: 'var(--navy-deep)' }}>Manage Companies</div>
                    <div className="font-mono text-xs" style={{ color: 'var(--navy-mid)' }}>{totalCompanies} companies</div>
                  </div>
                  <svg className="w-5 h-5 transition-transform group-hover:translate-x-1" style={{ color: 'var(--cyan-electric)' }}
                       fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </div>
              </Link>
            </div>
          </div>
        </div>
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

  if (dataLoading) return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--off-white)' }}>
      <div className="text-center">
        <div className="relative w-20 h-20 mx-auto mb-6">
          <div className="absolute inset-0 rounded-full border-4" style={{ borderColor: 'var(--warm-gray)', borderTopColor: 'var(--cyan-electric)', animation: 'spin 1s linear infinite' }} />
        </div>
        <p className="font-mono text-sm uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>Loading dashboard...</p>
      </div>
    </div>
  )

  const byStatus: Record<string, number> = {}
  candidates.forEach((c: any) => { byStatus[c.status] = (byStatus[c.status] || 0) + 1 })
  const today = new Date().toDateString()
  const todayApplications = candidates.filter((c: any) => new Date(c.created_at).toDateString() === today).length
  const shortlisted = byStatus['shortlisted'] || 0
  const rejected = byStatus['rejected'] || 0
  const awaitingReply = byStatus['awaiting_reply'] || 0
  const totalCandidates = candidates.length

  // Pipeline conversion rate
  const conversionRate = totalCandidates > 0 ? Math.round((shortlisted / totalCandidates) * 100) : 0

  return (
    <div className="min-h-screen grid-pattern">
      {/* Hero Section */}
      <div className="relative overflow-hidden" style={{ background: 'linear-gradient(135deg, var(--navy-deep) 0%, var(--navy-mid) 100%)' }}>
        {/* Decorative Elements */}
        <div className="absolute top-0 right-0 w-[600px] h-[600px] opacity-10 float-slow">
          <div className="absolute top-0 right-0 w-96 h-96 rounded-full" style={{ background: 'var(--cyan-electric)', filter: 'blur(100px)' }} />
        </div>
        <div className="absolute bottom-0 left-0 w-[400px] h-[400px] opacity-10 float-medium">
          <div className="absolute bottom-0 left-0 w-72 h-72 rounded-full" style={{ background: 'var(--gold-accent)', filter: 'blur(80px)' }} />
        </div>

        <div className="max-w-7xl mx-auto px-6 lg:px-12 py-20 relative z-10">
          <div className="reveal-up">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full mb-8"
                 style={{ background: 'rgba(0, 229, 255, 0.1)', border: '1px solid rgba(0, 229, 255, 0.3)' }}>
              <div className="w-2 h-2 rounded-full pulse-live" style={{ background: 'var(--sage-green)' }} />
              <span className="font-mono text-xs uppercase tracking-wider" style={{ color: 'var(--cyan-electric)' }}>Live Dashboard</span>
            </div>
          </div>

          <h1 className="font-display text-5xl lg:text-7xl leading-tight mb-6 reveal-up reveal-delay-1" style={{ color: 'white' }}>
            Good {new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 18 ? 'afternoon' : 'evening'},<br />
            <span className="gradient-text">{user.name}</span>
          </h1>
          <p className="text-xl leading-relaxed max-w-2xl reveal-up reveal-delay-2" style={{ color: 'rgba(255,255,255,0.7)' }}>
            {user.company_name} hiring pipeline overview. Auto-refreshes every 30 seconds.
          </p>

          {/* Quick Stats Row */}
          <div className="flex flex-wrap gap-6 mt-10 reveal-up reveal-delay-3">
            <div className="flex items-center gap-3 px-5 py-3 rounded-full" style={{ background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)' }}>
              <span className="text-2xl">📊</span>
              <div>
                <div className="font-mono text-xs uppercase" style={{ color: 'rgba(255,255,255,0.6)' }}>Total Candidates</div>
                <div className="font-display text-xl" style={{ color: 'white' }}>{totalCandidates}</div>
              </div>
            </div>
            <div className="flex items-center gap-3 px-5 py-3 rounded-full" style={{ background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)' }}>
              <span className="text-2xl">💼</span>
              <div>
                <div className="font-mono text-xs uppercase" style={{ color: 'rgba(255,255,255,0.6)' }}>Active Jobs</div>
                <div className="font-display text-xl" style={{ color: 'white' }}>{jobs.length}</div>
              </div>
            </div>
            <div className="flex items-center gap-3 px-5 py-3 rounded-full" style={{ background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)' }}>
              <span className="text-2xl">📈</span>
              <div>
                <div className="font-mono text-xs uppercase" style={{ color: 'rgba(255,255,255,0.6)' }}>Conversion Rate</div>
                <div className="font-display text-xl gradient-text">{conversionRate}%</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="max-w-7xl mx-auto px-6 lg:px-12 -mt-12 relative z-20">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { label: 'Today\'s Applications', value: todayApplications, icon: '📥', color: 'var(--cyan-electric)', gradient: 'linear-gradient(135deg, var(--cyan-electric), var(--cyan-glow))', badge: 'badge-info' },
            { label: 'Awaiting Reply', value: awaitingReply, icon: '⏳', color: 'var(--gold-accent)', gradient: 'linear-gradient(135deg, var(--gold-accent), var(--gold-light))', badge: 'badge-warning' },
            { label: 'Shortlisted', value: shortlisted, icon: '⭐', color: 'var(--sage-green)', gradient: 'linear-gradient(135deg, var(--sage-green), var(--sage-light))', badge: 'badge-success' },
            { label: 'Pending Approval', value: pendingApprovals.length, icon: '🔔', color: 'var(--coral-warm)', gradient: 'linear-gradient(135deg, var(--coral-warm), var(--coral-soft))', badge: 'badge-danger' },
          ].map((s, i) => (
            <Link key={s.label} href={s.label === 'Pending Approval' ? '/approvals' : '/candidates'}
                  className="glass-card rounded-2xl p-6 hover-lift reveal-up group" style={{ animationDelay: `${0.1 * i}s` }}>
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 rounded-xl flex items-center justify-center text-xl" style={{ background: s.gradient }}>
                  {s.icon}
                </div>
                <span className={`px-2 py-1 rounded-full font-mono text-xs ${s.badge}`}>
                  {s.value > 0 ? 'Active' : 'None'}
                </span>
              </div>
              <div className="font-display text-4xl mb-1" style={{ color: 'var(--navy-deep)' }}>{s.value}</div>
              <div className="font-mono text-xs uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>{s.label}</div>
              <div className="mt-3 h-1 rounded-full overflow-hidden" style={{ background: 'var(--warm-gray)' }}>
                <div className="h-full rounded-full" style={{ background: s.gradient, width: `${Math.min((s.value / Math.max(totalCandidates, 1)) * 100, 100)}%`, transition: 'width 1s ease-out' }} />
              </div>
            </Link>
          ))}
        </div>

        {/* Quick Links & Pipeline Overview */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-12 mb-12">
          {[
            { label: 'All Candidates', desc: 'View and manage your talent pipeline', href: '/candidates', icon: '👤', count: candidates.length, gradient: 'linear-gradient(135deg, rgba(0, 229, 255, 0.1), rgba(0, 229, 255, 0.05))' },
            { label: 'Job Postings', desc: 'Manage active job listings', href: '/jobs', icon: '💼', count: jobs.length, gradient: 'linear-gradient(135deg, rgba(244, 185, 66, 0.1), rgba(244, 185, 66, 0.05))' },
            { label: 'Pending Decisions', desc: 'Review and approve candidates', href: '/approvals', icon: '✅', count: pendingApprovals.length, gradient: 'linear-gradient(135deg, rgba(78, 205, 196, 0.1), rgba(78, 205, 196, 0.05))' },
          ].map((card, i) => (
            <Link key={card.label} href={card.href} className="group p-8 rounded-2xl transition-all hover-lift reveal-up"
                  style={{ background: card.gradient, border: '1px solid var(--warm-gray)', animationDelay: `${0.2 + 0.1 * i}s` }}>
              <div className="flex items-center gap-4 mb-4">
                <div className="w-14 h-14 rounded-xl flex items-center justify-center text-2xl bg-white shadow-sm">
                  {card.icon}
                </div>
                <div className="flex-1">
                  <div className="font-display text-xl mb-1" style={{ color: 'var(--navy-deep)' }}>{card.label}</div>
                  <div className="font-mono text-xs" style={{ color: 'var(--navy-mid)' }}>{card.desc}</div>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <div className="px-4 py-2 rounded-lg" style={{ background: 'white' }}>
                  <span className="font-display text-2xl gradient-text">{card.count}</span>
                  <span className="font-mono text-xs ml-2" style={{ color: 'var(--navy-mid)' }}>{card.label.toLowerCase()}</span>
                </div>
                <svg className="w-6 h-6 transition-transform group-hover:translate-x-1" style={{ color: 'var(--navy-mid)' }}
                     fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </div>
            </Link>
          ))}
        </div>

        {/* Pipeline Breakdown */}
        {Object.keys(byStatus).length > 0 && (
          <div className="glass-card rounded-2xl p-8 mb-12 reveal-up">
            <h3 className="font-display text-xl mb-6" style={{ color: 'var(--navy-deep)' }}>Pipeline Breakdown</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
              {Object.entries(byStatus).map(([status, count]) => (
                <div key={status} className="text-center p-4 rounded-xl" style={{ background: 'rgba(10, 22, 40, 0.03)' }}>
                  <div className="font-display text-2xl mb-1" style={{ color: 'var(--navy-deep)' }}>{count}</div>
                  <div className="font-mono text-xs uppercase tracking-wider truncate" style={{ color: 'var(--navy-mid)' }}>
                    {status.replace('_', ' ')}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
