'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/components/AuthProvider'

interface Company { id: number; name: string; slug: string; description: string | null; services: string | null; plan: string; is_active: boolean; user_count: number; job_count: number; candidate_count: number; created_at: string }

export default function CompaniesPage() {
  const { user } = useAuth()
  const [companies, setCompanies] = useState<Company[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState('')

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/companies`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('auth_token')}` }
    })
      .then(r => { if (!r.ok) throw new Error('Failed to load'); return r.json() })
      .then(data => setCompanies(data))
      .catch(err => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return (<div className="flex items-center justify-center min-h-[60vh]"><div className="text-center"><div className="relative w-16 h-16 mx-auto mb-6"><div className="absolute inset-0 rounded-full border-2 animate-spin" style={{ borderColor: 'var(--cyan-electric)', borderTopColor: 'transparent' }} /></div><p className="font-mono text-sm uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>Loading companies...</p></div></div>)
  if (error) return (<div className="max-w-7xl mx-auto px-6 lg:px-12 py-16"><div className="border-l-4 p-8" style={{ borderColor: 'var(--coral-warm)', background: 'rgba(255, 107, 107, 0.05)' }}><h3 className="font-display text-xl mb-2" style={{ color: 'var(--navy-deep)' }}>Error</h3><p style={{ color: 'var(--navy-mid)' }}>{error}</p></div></div>)

  const filtered = companies.filter(c => c.name.toLowerCase().includes(filter.toLowerCase()) || (c.services || '').toLowerCase().includes(filter.toLowerCase()))
  const totalUsers = companies.reduce((s, c) => s + c.user_count, 0)
  const totalJobs = companies.reduce((s, c) => s + c.job_count, 0)
  const totalCandidates = companies.reduce((s, c) => s + c.candidate_count, 0)

  return (
    <div className="max-w-7xl mx-auto px-6 lg:px-12 py-16">
      <div className="mb-12">
        <div className="font-mono text-xs uppercase tracking-wider mb-4" style={{ color: 'var(--navy-mid)' }}>Super Admin</div>
        <h1 className="font-display text-5xl lg:text-6xl leading-tight mb-4" style={{ color: 'var(--navy-deep)' }}>Registered Companies</h1>
        <p className="text-xl" style={{ color: 'var(--navy-light)' }}>Manage all companies registered on the platform.</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
        {[
          { label: 'Companies', value: companies.length },
          { label: 'Total Users', value: totalUsers },
          { label: 'Total Jobs', value: totalJobs },
          { label: 'Total Candidates', value: totalCandidates },
        ].map(s => (
          <div key={s.label} className="p-6 rounded-xl" style={{ background: 'white', border: '1px solid var(--warm-gray)' }}>
            <div className="font-display text-4xl mb-1" style={{ color: 'var(--cyan-electric)' }}>{s.value}</div>
            <div className="font-mono text-xs uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Filter */}
      <div className="mb-8">
        <input type="text" value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="Search companies..." className="w-full max-w-md px-4 py-3 rounded-lg text-sm" style={{ background: 'white', border: '1px solid var(--warm-gray)', color: 'var(--navy-deep)' }} />
      </div>

      {/* Companies Table */}
      <div className="rounded-xl overflow-hidden" style={{ background: 'white', border: '1px solid var(--warm-gray)' }}>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead><tr style={{ background: 'var(--off-white)', borderBottom: '1px solid var(--warm-gray)' }}>
              <th className="text-left px-6 py-4 font-mono text-xs uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>Company</th>
              <th className="text-left px-6 py-4 font-mono text-xs uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>Services</th>
              <th className="text-left px-6 py-4 font-mono text-xs uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>Plan</th>
              <th className="text-center px-4 py-4 font-mono text-xs uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>Users</th>
              <th className="text-center px-4 py-4 font-mono text-xs uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>Jobs</th>
              <th className="text-center px-4 py-4 font-mono text-xs uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>Candidates</th>
              <th className="text-left px-6 py-4 font-mono text-xs uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>Status</th>
            </tr></thead>
            <tbody>
              {filtered.map(c => (
                <tr key={c.id} className="border-b" style={{ borderColor: 'var(--warm-gray)' }}>
                  <td className="px-6 py-4">
                    <div className="font-medium" style={{ color: 'var(--navy-deep)' }}>{c.name}</div>
                    <div className="text-xs mt-1" style={{ color: 'var(--navy-light)' }}>{c.description?.substring(0, 60) || 'No description'}</div>
                  </td>
                  <td className="px-6 py-4 text-sm" style={{ color: 'var(--navy-mid)' }}>{c.services || '—'}</td>
                  <td className="px-6 py-4"><span className="px-3 py-1 rounded-full text-xs font-medium" style={{ background: c.plan === 'enterprise' ? 'var(--cyan-electric)' : c.plan === 'pro' ? 'rgba(0, 229, 255, 0.1)' : 'var(--off-white)', color: c.plan === 'free' ? 'var(--navy-mid)' : 'var(--navy-deep)' }}>{c.plan}</span></td>
                  <td className="px-4 py-4 text-center font-mono text-sm" style={{ color: 'var(--navy-deep)' }}>{c.user_count}</td>
                  <td className="px-4 py-4 text-center font-mono text-sm" style={{ color: 'var(--navy-deep)' }}>{c.job_count}</td>
                  <td className="px-4 py-4 text-center font-mono text-sm" style={{ color: 'var(--navy-deep)' }}>{c.candidate_count}</td>
                  <td className="px-6 py-4"><span className="inline-flex items-center gap-2"><span className="w-2 h-2 rounded-full" style={{ background: c.is_active ? 'var(--sage-green)' : 'var(--coral-warm)' }} /><span className="text-sm" style={{ color: 'var(--navy-mid)' }}>{c.is_active ? 'Active' : 'Inactive'}</span></span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {filtered.length === 0 && (<div className="text-center py-16" style={{ color: 'var(--navy-light)' }}><p className="text-lg">No companies found</p></div>)}
      </div>
    </div>
  )
}
