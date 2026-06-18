'use client'

import { useCallback, useEffect, useState } from 'react'
import { getCandidates, getPendingApprovals } from '@/lib/api'
import DigestBanner from '@/components/DigestBanner'
import PipelineBoard from '@/components/PipelineBoard'
import ApprovalCard from '@/components/ApprovalCard'
import Link from 'next/link'

export default function Dashboard() {
  const [candidates, setCandidates] = useState<any[]>([])
  const [pendingApprovals, setPendingApprovals] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    try {
      setError(null)
      const [candidatesData, approvalsData] = await Promise.all([
        getCandidates(),
        getPendingApprovals(),
      ])
      setCandidates(candidatesData)
      setPendingApprovals(approvalsData)
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [fetchData])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="relative w-16 h-16 mx-auto mb-6">
            <div
              className="absolute inset-0 rounded-full border-2 animate-spin"
              style={{
                borderColor: 'var(--cyan-electric)',
                borderTopColor: 'transparent',
              }}
            />
          </div>
          <p className="font-mono text-sm uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>
            Loading dashboard...
          </p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-6 lg:px-12 py-16">
        <div
          className="border-l-4 p-8"
          style={{
            borderColor: 'var(--coral-warm)',
            background: 'rgba(255, 107, 107, 0.05)',
          }}
        >
          <h3 className="font-display text-xl mb-2" style={{ color: 'var(--navy-deep)' }}>
            Error Loading Dashboard
          </h3>
          <p className="mb-4" style={{ color: 'var(--navy-mid)' }}>
            {error}
          </p>
          <button
            onClick={fetchData}
            className="px-6 py-2 font-medium text-sm transition-colors hover:opacity-80"
            style={{ background: 'var(--coral-warm)', color: 'white' }}
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  const today = new Date().toDateString()
  const newApplications = candidates.filter(
    (c) => new Date(c.created_at).toDateString() === today
  ).length
  const shortlistedToday = candidates.filter(
    (c) => c.status === 'shortlisted' && new Date(c.updated_at || c.created_at).toDateString() === today
  ).length
  const pendingApprovalIds = pendingApprovals.map((a) => a.candidate_id)

  return (
    <div className="max-w-7xl mx-auto px-6 lg:px-12 py-16">
      <div className="mb-8">
        <div className="font-mono text-xs uppercase tracking-wider mb-4" style={{ color: 'var(--navy-mid)' }}>
          Admin Dashboard
        </div>
        <h1 className="font-display text-5xl lg:text-6xl leading-tight mb-4" style={{ color: 'var(--navy-deep)' }}>
          Pipeline
        </h1>
        <p className="text-xl leading-relaxed max-w-2xl" style={{ color: 'var(--navy-light)' }}>
          AI-powered screening with human oversight. Auto-refreshes every 30 seconds.
        </p>
      </div>

      <DigestBanner
        newApplications={newApplications}
        pendingApprovals={pendingApprovals.length}
        shortlistedToday={shortlistedToday}
      />

      <div className="mb-16">
        <h2 className="font-display text-2xl mb-6" style={{ color: 'var(--navy-deep)' }}>
          Candidate Pipeline
        </h2>
        <PipelineBoard
          candidates={candidates}
          pendingApprovalCandidateIds={pendingApprovalIds}
        />
      </div>

      {pendingApprovals.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-6">
            <h2 className="font-display text-2xl" style={{ color: 'var(--navy-deep)' }}>
              Pending Approvals
            </h2>
            <Link
              href="/approvals"
              className="px-6 py-3 font-medium transition-all hover:opacity-90"
              style={{ background: 'var(--navy-deep)', color: 'var(--off-white)' }}
            >
              View All ({pendingApprovals.length})
            </Link>
          </div>
          <div className="space-y-6">
            {pendingApprovals.slice(0, 3).map((approval) => (
              <ApprovalCard key={approval.id} approval={approval} onApprovalComplete={fetchData} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
