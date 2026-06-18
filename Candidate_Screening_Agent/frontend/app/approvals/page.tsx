'use client'

import { useEffect, useState } from 'react'
import { getPendingApprovals } from '@/lib/api'
import ApprovalCard from '@/components/ApprovalCard'

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchApprovals = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await getPendingApprovals()
      setApprovals(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load pending approvals')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchApprovals()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="relative w-16 h-16 mx-auto mb-6">
            <div className="absolute inset-0 rounded-full border-2 animate-spin"
                 style={{
                   borderColor: 'var(--cyan-electric)',
                   borderTopColor: 'transparent'
                 }} />
          </div>
          <p className="font-mono text-sm uppercase tracking-wider"
             style={{ color: 'var(--navy-mid)' }}>
            Loading approvals...
          </p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-6 lg:px-12 py-16">
        <div className="border-l-4 p-8"
             style={{
               borderColor: 'var(--coral-warm)',
               background: 'rgba(255, 107, 107, 0.05)'
             }}>
          <h3 className="font-display text-xl mb-2"
              style={{ color: 'var(--navy-deep)' }}>
            Error Loading Approvals
          </h3>
          <p className="mb-4" style={{ color: 'var(--navy-mid)' }}>
            {error}
          </p>
          <button
            onClick={fetchApprovals}
            className="px-6 py-2 font-medium text-sm transition-colors hover:opacity-80"
            style={{
              background: 'var(--coral-warm)',
              color: 'white'
            }}
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-6 lg:px-12 py-16">
      {/* Header */}
      <div className="mb-16">
        <div className="flex items-start justify-between gap-8 mb-8">
          <div className="flex-1">
            <div className="font-mono text-xs uppercase tracking-wider mb-4"
                 style={{ color: 'var(--navy-mid)' }}>
              Review Queue
            </div>
            <h1 className="font-display text-5xl lg:text-6xl leading-tight mb-6"
                style={{ color: 'var(--navy-deep)' }}>
              Pending Approvals
            </h1>
            <p className="text-xl leading-relaxed max-w-2xl"
               style={{ color: 'var(--navy-light)' }}>
              AI has analyzed these candidates. Review recommendations and make
              final hiring decisions.
            </p>
          </div>

          {approvals.length > 0 && (
            <div className="hidden lg:block accent-line pl-6">
              <div className="font-display text-4xl mb-2"
                   style={{ color: 'var(--coral-warm)' }}>
                {approvals.length}
              </div>
              <div className="font-mono text-xs uppercase tracking-wider"
                   style={{ color: 'var(--navy-mid)' }}>
                {approvals.length === 1 ? 'Candidate' : 'Candidates'}
              </div>
            </div>
          )}
        </div>

        {/* Divider */}
        <div className="h-px" style={{ background: 'var(--warm-gray)' }} />
      </div>

      {/* Approvals List */}
      {approvals.length === 0 ? (
        <div className="text-center py-24">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full mb-6"
               style={{ background: 'var(--off-white)' }}>
            <svg className="w-10 h-10"
                 style={{ color: 'var(--sage-green)' }}
                 fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="font-display text-2xl mb-3"
              style={{ color: 'var(--navy-deep)' }}>
            All Caught Up
          </h3>
          <p className="text-lg max-w-md mx-auto"
             style={{ color: 'var(--navy-light)' }}>
            No pending approvals. All candidates have been reviewed.
          </p>
        </div>
      ) : (
        <div className="space-y-8">
          {approvals.map((approval, index) => (
            <div key={approval.id}
                 className="reveal-up"
                 style={{ animationDelay: `${index * 0.1}s` }}>
              <ApprovalCard
                approval={approval}
                onApprovalComplete={fetchApprovals}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
