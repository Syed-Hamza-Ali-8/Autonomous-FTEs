'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import { getJobs } from '@/lib/api'

function timeSince(dateStr: string) {
  const seconds = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000)
  if (seconds < 3600) return 'Just now'
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`
  return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export default function HomePage() {
  const [jobs, setJobs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    getJobs()
      .then((data) => { setJobs(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const filtered = searchQuery.trim()
    ? jobs.filter(j =>
        j.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        j.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        j.company_name?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : jobs

  const departments = [...new Set(jobs.map(j => j.department || j.rubric_path?.split('/').pop()?.replace('.md', '').replace(/_/g, ' ')).filter(Boolean))]

  return (
    <div className="min-h-screen flex flex-col" style={{ background: '#F8F9FB' }}>

      {/* ─── Hero ─── */}
      <section className="relative overflow-hidden" style={{ background: 'linear-gradient(135deg, #0A1628 0%, #142240 50%, #1A2B47 100%)' }}>
        {/* Subtle grid pattern */}
        <div className="absolute inset-0 opacity-[0.04]" style={{
          backgroundImage: 'linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px)',
          backgroundSize: '60px 60px'
        }} />
        {/* Glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] opacity-20 blur-[120px] pointer-events-none"
             style={{ background: 'radial-gradient(ellipse, #00E5FF 0%, transparent 70%)' }} />

        <div className="relative max-w-6xl mx-auto px-6 pt-20 pb-24 sm:pt-28 sm:pb-32">
          <div className="max-w-2xl">
            <h1 className="text-4xl sm:text-5xl lg:text-[56px] font-bold leading-[1.1] tracking-tight mb-5" style={{ color: '#FFFFFF' }}>
              Opportunities that match your ambition
            </h1>
            <p className="text-base sm:text-lg leading-relaxed mb-10" style={{ color: 'rgba(255,255,255,0.55)' }}>
              Apply to roles at growing companies. Our screening process is fast, fair, and transparent — you'll hear back within 48 hours.
            </p>

            {/* Search bar */}
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="relative flex-1">
                <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 pointer-events-none" style={{ color: '#94A3B8' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
                </svg>
                <input
                  type="text"
                  placeholder="Search job titles, companies..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-12 pr-4 py-4 text-[15px] rounded-xl focus:outline-none focus:ring-2 focus:ring-cyan-400/40 transition-shadow"
                  style={{ background: 'rgba(255,255,255,0.95)', color: '#0A1628' }}
                />
              </div>
              <Link
                href="/jobs"
                className="flex items-center justify-center gap-2 px-7 py-4 text-sm font-semibold rounded-xl transition-all hover:brightness-110"
                style={{ background: '#00E5FF', color: '#0A1628' }}
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
                </svg>
                Find Jobs
              </Link>
            </div>

            {/* Stats row */}
            <div className="flex flex-wrap gap-6 mt-8">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full" style={{ background: '#4ECDC4' }} />
                <span className="text-xs font-medium" style={{ color: 'rgba(255,255,255,0.5)' }}>
                  {loading ? '...' : `${jobs.filter((j: any) => j.status !== 'paused').length} open positions`}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full" style={{ background: '#00E5FF' }} />
                <span className="text-xs font-medium" style={{ color: 'rgba(255,255,255,0.5)' }}>
                  48h average response
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full" style={{ background: '#FF6B6B' }} />
                <span className="text-xs font-medium" style={{ color: 'rgba(255,255,255,0.5)' }}>
                  100% applications reviewed
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Featured Jobs ─── */}
      <section className="max-w-6xl w-full mx-auto px-6 -mt-8 relative z-10">
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {(loading ? [1, 2, 3] : filtered.slice(0, 3)).map((job: any, i: number) =>
            loading ? (
              <div key={i} className="h-44 rounded-xl animate-pulse" style={{ background: '#E2E8F0' }} />
            ) : (
              <Link key={job.id} href={job.status === 'paused' ? '#' : `/jobs/${job.id}`}
                    className={`group flex flex-col justify-between p-5 rounded-xl border transition-all ${job.status === 'paused' ? 'opacity-60 cursor-default' : 'hover:shadow-lg hover:-translate-y-0.5'}`}
                    style={{ background: '#FFFFFF', borderColor: '#E5E7EB' }}
                    onClick={job.status === 'paused' ? (e: React.MouseEvent) => e.preventDefault() : undefined}>
                <div>
                  <div className="flex items-start gap-3 mb-3">
                    <div className="shrink-0 w-10 h-10 rounded-lg flex items-center justify-center text-sm font-bold"
                         style={{ background: ['#EFF6FF','#ECFDF5','#FFF7ED'][i % 3], color: ['#2563EB','#059669','#EA580C'][i % 3] }}>
                      {(job.company_name || job.title || '?')[0].toUpperCase()}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-semibold truncate group-hover:text-cyan-700 transition-colors" style={{ color: '#0F172A' }}>
                          {job.title}
                        </h3>
                        {job.status === 'paused' && (
                          <span className="shrink-0 text-[10px] font-semibold px-1.5 py-0.5 rounded" style={{ background: '#FEF2F2', color: '#DC2626' }}>PAUSED</span>
                        )}
                      </div>
                      {job.company_name && (
                        <p className="text-xs mt-0.5 truncate" style={{ color: '#64748B' }}>{job.company_name}</p>
                      )}
                    </div>
                  </div>
                  <p className="text-xs leading-relaxed line-clamp-2" style={{ color: '#64748B' }}>
                    {job.description?.slice(0, 120)}{job.description?.length > 120 ? '...' : ''}
                  </p>
                </div>
                <div className="flex items-center justify-between mt-4 pt-3 border-t" style={{ borderColor: '#F1F5F9' }}>
                  <div className="flex items-center gap-3">
                    {job.status === 'paused' ? (
                      <span className="inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full"
                            style={{ background: '#FEF2F2', color: '#DC2626' }}>
                        Not accepting applications
                      </span>
                    ) : (
                      <>
                        <span className="inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full"
                              style={{ background: '#F0FDFA', color: '#0D9488' }}>
                          <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          Full-time
                        </span>
                        {job.created_at && (
                          <span className="text-[11px]" style={{ color: '#94A3B8' }}>{timeSince(job.created_at)}</span>
                        )}
                      </>
                    )}
                  </div>
                  <svg className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-all group-hover:translate-x-0.5" style={{ color: '#0D9488' }}
                       fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12h15m0 0l-6.75-6.75M19.5 12l-6.75 6.75" />
                  </svg>
                </div>
              </Link>
            )
          )}
        </div>
      </section>

      {/* ─── All Jobs List ─── */}
      <section className="max-w-6xl w-full mx-auto px-6 mt-12 mb-4">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-xl font-bold" style={{ color: '#0F172A' }}>
            {searchQuery ? `Results for "${searchQuery}"` : 'All open positions'}
          </h2>
          <span className="text-xs font-medium px-2.5 py-1 rounded-full" style={{ background: '#E0F2FE', color: '#0369A1' }}>
            {filtered.length} {filtered.length === 1 ? 'job' : 'jobs'}
          </span>
        </div>

        <div className="rounded-xl border overflow-hidden" style={{ background: '#FFFFFF', borderColor: '#E5E7EB' }}>
          {loading ? (
            <div className="divide-y" style={{ borderColor: '#F1F5F9' }}>
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="flex items-center gap-4 px-5 py-4">
                  <div className="w-10 h-10 rounded-lg animate-pulse" style={{ background: '#E2E8F0' }} />
                  <div className="flex-1 space-y-2">
                    <div className="h-4 w-48 rounded animate-pulse" style={{ background: '#E2E8F0' }} />
                    <div className="h-3 w-32 rounded animate-pulse" style={{ background: '#F1F5F9' }} />
                  </div>
                </div>
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-14">
              <svg className="w-12 h-12 mx-auto mb-3" style={{ color: '#CBD5E1' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
              </svg>
              <p className="text-sm font-medium" style={{ color: '#64748B' }}>
                {searchQuery ? `No positions match "${searchQuery}"` : 'No open positions right now'}
              </p>
              {searchQuery && (
                <button onClick={() => setSearchQuery('')} className="text-xs mt-2 underline" style={{ color: '#0EA5E9' }}>
                  Clear search
                </button>
              )}
            </div>
          ) : (
            <div className="divide-y" style={{ borderColor: '#F1F5F9' }}>
              {filtered.map((job: any, i: number) => (
                <Link key={job.id} href={job.status === 'paused' ? '#' : `/jobs/${job.id}`}
                      className={`group flex items-center gap-4 px-5 py-4 transition-colors ${job.status === 'paused' ? 'opacity-60 cursor-default' : 'hover:bg-slate-50/80'}`}
                      onClick={job.status === 'paused' ? (e: React.MouseEvent) => e.preventDefault() : undefined}>
                  {/* Company avatar */}
                  <div className="shrink-0 w-10 h-10 rounded-lg flex items-center justify-center text-sm font-bold"
                       style={{
                         background: ['#EFF6FF','#ECFDF5','#FFF7ED','#FDF2F8','#F5F3FF'][i % 5],
                         color: ['#2563EB','#059669','#EA580C','#DB2777','#7C3AED'][i % 5]
                       }}>
                    {(job.company_name || job.title || '?')[0].toUpperCase()}
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-semibold truncate group-hover:text-cyan-700 transition-colors" style={{ color: '#0F172A' }}>
                        {job.title}
                      </h3>
                      {job.status === 'paused' && (
                        <span className="shrink-0 text-[10px] font-semibold px-1.5 py-0.5 rounded" style={{ background: '#FEF2F2', color: '#DC2626' }}>PAUSED</span>
                      )}
                      {job.status !== 'paused' && job.created_at && (new Date().getTime() - new Date(job.created_at).getTime()) < 259200000 && (
                        <span className="shrink-0 text-[10px] font-semibold px-1.5 py-0.5 rounded" style={{ background: '#DCFCE7', color: '#16A34A' }}>NEW</span>
                      )}
                    </div>
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 mt-1">
                      {job.company_name && (
                        <span className="text-xs" style={{ color: '#64748B' }}>{job.company_name}</span>
                      )}
                      {job.status === 'paused' ? (
                        <span className="text-xs" style={{ color: '#DC2626' }}>Not accepting applications</span>
                      ) : (
                        <>
                          <span className="hidden sm:inline text-xs" style={{ color: '#94A3B8' }}>Full-time</span>
                          {job.created_at && (
                            <span className="text-xs" style={{ color: '#94A3B8' }}>{timeSince(job.created_at)}</span>
                          )}
                        </>
                      )}
                    </div>
                  </div>

                  {/* Apply button — hidden for paused */}
                  {job.status !== 'paused' && (
                    <div className="shrink-0 hidden sm:block">
                      <span className="inline-flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg transition-all opacity-0 group-hover:opacity-100 translate-x-1 group-hover:translate-x-0"
                            style={{ background: '#0F172A', color: '#FFFFFF' }}>
                        Apply
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12h15m0 0l-6.75-6.75M19.5 12l-6.75 6.75" />
                        </svg>
                      </span>
                    </div>
                  )}
                </Link>
              ))}
            </div>
          )}
        </div>

        {filtered.length > 6 && (
          <div className="text-center mt-6">
            <Link href="/jobs"
                  className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-semibold rounded-lg border transition-colors hover:bg-slate-50"
                  style={{ borderColor: '#CBD5E1', color: '#334155' }}>
              View all {filtered.length} positions
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12h15m0 0l-6.75-6.75M19.5 12l-6.75 6.75" />
              </svg>
            </Link>
          </div>
        )}
      </section>

      {/* ─── Browse by Category ─── */}
      {departments.length > 1 && (
        <section className="max-w-6xl w-full mx-auto px-6 mt-10 mb-4">
          <h2 className="text-xl font-bold mb-5" style={{ color: '#0F172A' }}>Browse by category</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
            {departments.slice(0, 8).map((dept, i) => {
              const count = jobs.filter(j => (j.department || j.rubric_path?.split('/').pop()?.replace('.md', '').replace(/_/g, ' ')) === dept).length
              const icons = ['M20.25 14.15v4.25c0 1.094-.787 2.036-1.872 2.18-2.087.277-4.216.42-6.378.42s-4.291-.143-6.378-.42c-1.085-.144-1.872-1.086-1.872-2.18v-4.25m16.5 0a2.18 2.18 0 00.75-1.661V8.706c0-1.081-.768-2.015-1.837-2.175a48.114 48.114 0 00-3.413-.387m4.5 8.006c-.194.165-.42.295-.673.38A23.978 23.978 0 0112 15.75c-2.648 0-5.195-.429-7.577-1.22a2.016 2.016 0 01-.673-.38m0 0A2.18 2.18 0 013 12.489V8.706c0-1.081.768-2.015 1.837-2.175a48.111 48.111 0 013.413-.387m7.5 0V5.25A2.25 2.25 0 0013.5 3h-3a2.25 2.25 0 00-2.25 2.25v.894m7.5 0a48.667 48.667 0 00-7.5 0M12 12.75h.008v.008H12v-.008z',
                'M9 17.25v1.007a3 3 0 01-.879 2.122L7.5 21h9l-.621-.621A3 3 0 0115 18.257V17.25m6-12V15a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 15V5.25m18 0A2.25 2.25 0 0018.75 3H5.25A2.25 2.25 0 003 5.25m18 0V12a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 12V5.25',
                'M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5M9 11.25v1.5M12 9v3.75m3-6v6',
                'M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.06 12.06 0 01-4.5 0m3.75 2.383a14.406 14.406 0 01-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 10-7.517 0c.85.493 1.509 1.333 1.509 2.316V18']
              return (
                <Link key={dept} href="/jobs"
                      className="group flex items-center gap-3 p-4 rounded-xl border transition-all hover:shadow-md hover:-translate-y-0.5"
                      style={{ background: '#FFFFFF', borderColor: '#E5E7EB' }}>
                  <div className="shrink-0 w-9 h-9 rounded-lg flex items-center justify-center"
                       style={{ background: ['#EFF6FF','#ECFDF5','#FFF7ED','#F5F3FF'][i % 4] }}>
                    <svg className="w-4 h-4" style={{ color: ['#2563EB','#059669','#EA580C','#7C3AED'][i % 4] }}
                         fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d={icons[i % 4]} />
                    </svg>
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium truncate group-hover:text-cyan-700 transition-colors" style={{ color: '#0F172A' }}>
                      {String(dept).replace(/\b\w/g, c => c.toUpperCase())}
                    </p>
                    <p className="text-[11px]" style={{ color: '#94A3B8' }}>
                      {count} {count === 1 ? 'position' : 'positions'}
                    </p>
                  </div>
                </Link>
              )
            })}
          </div>
        </section>
      )}

      {/* ─── How it works ─── */}
      <section className="max-w-6xl w-full mx-auto px-6 mt-14 mb-16">
        <div className="rounded-2xl border overflow-hidden" style={{ background: '#FFFFFF', borderColor: '#E5E7EB' }}>
          <div className="px-6 py-5 border-b" style={{ borderColor: '#F1F5F9' }}>
            <h2 className="text-lg font-bold" style={{ color: '#0F172A' }}>How the application process works</h2>
          </div>
          <div className="grid sm:grid-cols-3 divide-y sm:divide-y-0 sm:divide-x" style={{ borderColor: '#F1F5F9' }}>
            {[
              { step: 'Apply', desc: 'Upload your resume to any open role. Takes less than 2 minutes.', icon: 'M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z', color: '#2563EB', bg: '#EFF6FF' },
              { step: 'Review', desc: 'Your application is evaluated against role-specific criteria by AI + humans.', icon: 'M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z', color: '#059669', bg: '#ECFDF5' },
              { step: 'Interview', desc: 'Shortlisted candidates get an interview invite within 48 hours.', icon: 'M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5', color: '#EA580C', bg: '#FFF7ED' },
            ].map((item, i) => (
              <div key={i} className="flex items-start gap-4 p-6">
                <div className="shrink-0 w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: item.bg }}>
                  <svg className="w-5 h-5" style={{ color: item.color }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d={item.icon} />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-semibold mb-1" style={{ color: '#0F172A' }}>{item.step}</p>
                  <p className="text-xs leading-relaxed" style={{ color: '#64748B' }}>{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Footer ─── */}
      <footer className="mt-auto border-t" style={{ background: '#FFFFFF', borderColor: '#E5E7EB' }}>
        <div className="max-w-6xl mx-auto px-6 py-8">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <span className="w-7 h-7 flex items-center justify-center text-xs font-bold rounded"
                    style={{ background: '#0F172A', color: '#FFFFFF' }}>H</span>
              <span className="text-sm font-semibold" style={{ color: '#0F172A' }}>HireAI</span>
              <span className="text-xs ml-2" style={{ color: '#94A3B8' }}>
                AI-powered hiring, human decisions
              </span>
            </div>
            <div className="flex items-center gap-5">
              <Link href="/jobs" className="text-xs font-medium hover:underline" style={{ color: '#64748B' }}>All Jobs</Link>
              <span className="text-xs" style={{ color: '#E2E8F0' }}>|</span>
              <span className="text-xs" style={{ color: '#94A3B8' }}>&copy; {new Date().getFullYear()} HireAI</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
