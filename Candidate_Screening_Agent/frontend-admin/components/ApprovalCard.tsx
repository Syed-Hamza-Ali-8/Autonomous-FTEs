'use client'

import { useState } from 'react'
import { approveCandidate, rejectCandidate } from '@/lib/api'
import Link from 'next/link'

interface ApprovalCardProps {
  approval: {
    id: number
    candidate_id: number
    candidate_name: string
    candidate_email: string
    job_id: number
    job_title: string
    action: string
    score: number
    recommendation: string
    brief_summary: string
    created_at: string
  }
  onApprovalComplete: () => void
}

export default function ApprovalCard({ approval, onApprovalComplete }: ApprovalCardProps) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showConfirm, setShowConfirm] = useState<'approve' | 'reject' | null>(null)

  const handleApprove = async () => {
    setShowConfirm(null)
    setLoading(true)
    setError(null)

    try {
      await approveCandidate(approval.id)
      onApprovalComplete()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to approve candidate')
      setLoading(false)
    }
  }

  const handleReject = async () => {
    setShowConfirm(null)
    setLoading(true)
    setError(null)

    try {
      await rejectCandidate(approval.id)
      onApprovalComplete()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to reject candidate')
      setLoading(false)
    }
  }

  const borderColor = approval.action === 'approve' ? 'var(--sage-green)' : 'var(--coral-warm)'
  const bgTint = approval.action === 'approve'
    ? 'rgba(78, 205, 196, 0.05)'
    : 'rgba(255, 107, 107, 0.05)'

  return (
    <>
      {/* Confirmation Modal */}
      {showConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl">
            <div className="text-center mb-6">
              <div className="w-16 h-16 rounded-full mx-auto mb-4 flex items-center justify-center"
                   style={{ background: showConfirm === 'approve' ? 'rgba(78, 205, 196, 0.1)' : 'rgba(255, 107, 107, 0.1)' }}>
                {showConfirm === 'approve' ? (
                  <svg className="w-8 h-8" style={{ color: 'var(--sage-green)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                ) : (
                  <svg className="w-8 h-8" style={{ color: 'var(--coral-warm)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                )}
              </div>
              <h3 className="font-display text-xl mb-2" style={{ color: 'var(--navy-deep)' }}>
                {showConfirm === 'approve' ? 'Approve & Send Interview Invite?' : 'Reject Application?'}
              </h3>
              <p className="text-sm" style={{ color: 'var(--navy-mid)' }}>
                {showConfirm === 'approve'
                  ? `Send interview invitation with time slots and screening questions to ${approval.candidate_name}?`
                  : `This will reject ${approval.candidate_name}'s application and send a rejection email.`
                }
              </p>
            </div>
            <div className="flex gap-4">
              <button
                onClick={() => setShowConfirm(null)}
                className="flex-1 px-6 py-3 font-medium border-2 rounded-xl transition-all hover:opacity-70"
                style={{ borderColor: 'var(--navy-mid)', color: 'var(--navy-deep)' }}
              >
                Cancel
              </button>
              <button
                onClick={showConfirm === 'approve' ? handleApprove : handleReject}
                disabled={loading}
                className="flex-1 px-6 py-3 font-medium rounded-xl transition-all hover:opacity-90 disabled:opacity-50"
                style={{ background: showConfirm === 'approve' ? 'var(--sage-green)' : 'var(--coral-warm)', color: 'white' }}
              >
                {loading ? 'Processing...' : 'Confirm'}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="rounded-2xl p-8"
           style={{
             background: 'var(--off-white)',
             border: `1px solid var(--warm-gray)`,
             borderLeft: `4px solid ${borderColor}`,
           }}>
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h3 className="font-display text-2xl" style={{ color: 'var(--navy-deep)' }}>
            {approval.candidate_name}
          </h3>
          <p className="font-mono text-sm mt-1" style={{ color: 'var(--navy-mid)' }}>
            {approval.candidate_email}
          </p>
          <p className="mt-2 font-mono text-xs uppercase tracking-wider"
             style={{ color: 'var(--navy-light)' }}>
            {approval.job_title}
          </p>
        </div>
        <div className="px-4 py-2 rounded-lg" style={{ background: bgTint }}>
          <span className="font-mono text-xs uppercase tracking-wider capitalize"
                style={{ color: borderColor }}>
            AI: {approval.action}
          </span>
        </div>
      </div>

      {/* Score */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <span className="font-mono text-xs uppercase tracking-wider"
                style={{ color: 'var(--navy-mid)' }}>
            Overall Score
          </span>
          <span className="font-display text-3xl" style={{ color: 'var(--navy-deep)' }}>
            {approval.score.toFixed(1)}%
          </span>
        </div>
        <div className="w-full rounded-full h-2" style={{ background: 'var(--warm-gray)' }}>
          <div
            className="h-2 rounded-full transition-all"
            style={{
              width: `${approval.score}%`,
              background: approval.score >= 70 ? 'var(--sage-green)' : approval.score >= 50 ? '#B8860B' : 'var(--coral-warm)',
            }}
          />
        </div>
      </div>

      {/* AI Recommendation */}
      <div className="mb-6 p-6 rounded-lg"
           style={{ background: 'var(--off-white)', border: '1px solid var(--warm-gray)' }}>
        <p className="font-mono text-xs uppercase tracking-wider mb-2"
           style={{ color: 'var(--navy-mid)' }}>
          AI Recommendation
        </p>
        <p className="font-display text-lg capitalize" style={{ color: 'var(--navy-deep)' }}>
          {approval.recommendation}
        </p>
      </div>

      {/* Brief Summary */}
      <div className="mb-8 p-6 rounded-lg"
           style={{ background: 'rgba(0, 229, 255, 0.03)', border: '1px solid rgba(0, 229, 255, 0.12)' }}>
        <p className="font-mono text-xs uppercase tracking-wider mb-2"
           style={{ color: 'var(--navy-mid)' }}>
          Summary
        </p>
        <p className="text-sm leading-relaxed" style={{ color: 'var(--navy-deep)' }}>
          {approval.brief_summary?.replace(/^JSON\s*/i, '')}
        </p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 rounded-lg border-l-4"
             style={{
               borderColor: 'var(--coral-warm)',
               background: 'rgba(255, 107, 107, 0.05)',
             }}>
          <p className="text-sm" style={{ color: 'var(--coral-warm)' }}>{error}</p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-4">
        <button
          onClick={() => setShowConfirm('approve')}
          disabled={loading}
          className="flex-1 px-6 py-3 font-medium rounded-xl transition-all hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
          style={{ background: 'var(--sage-green)', color: 'white' }}
        >
          ✓ Approve & Send Interview Invite
        </button>
        <button
          onClick={() => setShowConfirm('reject')}
          disabled={loading}
          className="flex-1 px-6 py-3 font-medium rounded-xl transition-all hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
          style={{ background: 'var(--coral-warm)', color: 'white' }}
        >
          ✗ Reject Application
        </button>
      </div>

      {/* View Full Details Link */}
      <div className="mt-6 text-center">
        <Link
          href={`/candidates/${approval.candidate_id}`}
          className="font-mono text-xs uppercase tracking-wider transition-colors hover:opacity-70"
          style={{ color: 'var(--navy-mid)' }}
        >
          View Full Candidate Profile →
        </Link>
      </div>
      </div>
    </>
  )
}
