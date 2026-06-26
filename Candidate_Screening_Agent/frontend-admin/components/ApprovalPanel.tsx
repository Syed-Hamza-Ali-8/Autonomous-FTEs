'use client'

import { useState } from 'react'
import { approveCandidate, rejectCandidate } from '@/lib/api'

interface ApprovalPanelProps {
  approval: {
    id: number
    candidate_id: number
    candidate_name: string
    job_title: string
    score: number
    recommendation: string
    brief_summary: string
    confidence?: string
  }
  onComplete?: () => void
}

export default function ApprovalPanel({ approval, onComplete }: ApprovalPanelProps) {
  const [loading, setLoading] = useState(false)
  const [showRejectForm, setShowRejectForm] = useState(false)
  const [showApproveConfirm, setShowApproveConfirm] = useState(false)
  const [rejectReason, setRejectReason] = useState('')
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const handleApprove = async () => {
    setShowApproveConfirm(false)
    setLoading(true)
    setMessage(null)
    try {
      await approveCandidate(approval.id)
      setMessage({ type: 'success', text: 'Candidate approved. Interview scheduling email has been sent.' })
      onComplete?.()
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to approve candidate' })
    } finally {
      setLoading(false)
    }
  }

  const handleReject = async () => {
    setLoading(true)
    setMessage(null)
    try {
      await rejectCandidate(approval.id)
      setMessage({ type: 'success', text: 'Candidate rejected. Rejection email has been sent.' })
      setShowRejectForm(false)
      onComplete?.()
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to reject candidate' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white shadow-lg rounded-2xl p-8 border-2"
         style={{ borderColor: 'var(--sage-green)', background: 'var(--off-white)' }}>
      <div className="flex items-center gap-3 mb-6">
        <div className="w-12 h-12 rounded-full flex items-center justify-center"
             style={{ background: 'rgba(78, 205, 196, 0.1)' }}>
          <svg className="w-6 h-6" style={{ color: 'var(--sage-green)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div>
          <h2 className="font-display text-2xl" style={{ color: 'var(--navy-deep)' }}>
            Pending Approval
          </h2>
          <p className="font-mono text-xs uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>
            {approval.candidate_name} for {approval.job_title}
          </p>
        </div>
      </div>

      <div className="p-6 rounded-xl mb-6" style={{ background: 'rgba(0, 229, 255, 0.05)', border: '1px solid rgba(0, 229, 255, 0.15)' }}>
        <p className="font-mono text-xs uppercase tracking-wider mb-2" style={{ color: 'var(--navy-mid)' }}>
          AI Recommendation
        </p>
        <p className="font-display text-xl capitalize" style={{ color: 'var(--navy-deep)' }}>
          {approval.recommendation}
          {approval.confidence && (
            <span className="ml-2 font-mono text-sm" style={{ color: 'var(--navy-light)' }}>
              ({approval.confidence} confidence)
            </span>
          )}
        </p>
        <p className="font-mono text-sm mt-2" style={{ color: 'var(--navy-mid)' }}>
          Score: <span className="font-semibold" style={{ color: 'var(--sage-green)' }}>{approval.score?.toFixed?.(1) ?? approval.score}/100</span>
        </p>
      </div>

      <p className="text-sm leading-relaxed mb-6" style={{ color: 'var(--navy-deep)' }}>
        {approval.brief_summary?.replace(/^JSON\s*/i, '')}
      </p>

      {message && (
        <div
          className="mb-6 p-4 rounded-xl text-sm"
          style={{
            background: message.type === 'success' ? 'rgba(78, 205, 196, 0.1)' : 'rgba(255, 107, 107, 0.1)',
            color: message.type === 'success' ? 'var(--sage-green)' : 'var(--coral-warm)',
            border: `1px solid ${message.type === 'success' ? 'rgba(78, 205, 196, 0.3)' : 'rgba(255, 107, 107, 0.3)'}`
          }}
        >
          {message.text}
        </div>
      )}

      {/* Approve Confirmation Modal */}
      {showApproveConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl">
            <div className="text-center mb-6">
              <div className="w-16 h-16 rounded-full mx-auto mb-4 flex items-center justify-center"
                   style={{ background: 'rgba(78, 205, 196, 0.1)' }}>
                <svg className="w-8 h-8" style={{ color: 'var(--sage-green)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="font-display text-xl mb-2" style={{ color: 'var(--navy-deep)' }}>
                Approve & Send Interview Invite?
              </h3>
              <p className="text-sm" style={{ color: 'var(--navy-mid)' }}>
                An email with interview time slots and screening questions will be sent to <strong>{approval.candidate_name}</strong>.
              </p>
            </div>
            <div className="flex gap-4">
              <button
                onClick={() => setShowApproveConfirm(false)}
                className="flex-1 px-6 py-3 font-medium border-2 transition-all hover:opacity-70"
                style={{ borderColor: 'var(--navy-mid)', color: 'var(--navy-deep)' }}
              >
                Cancel
              </button>
              <button
                onClick={handleApprove}
                disabled={loading}
                className="flex-1 px-6 py-3 font-medium transition-all hover:opacity-90 disabled:opacity-50"
                style={{ background: 'var(--sage-green)', color: 'white' }}
              >
                {loading ? 'Sending...' : 'Confirm'}
              </button>
            </div>
          </div>
        </div>
      )}

      {!showRejectForm ? (
        <div className="flex flex-col sm:flex-row gap-4">
          <button
            onClick={() => setShowApproveConfirm(true)}
            disabled={loading}
            className="flex-1 px-6 py-4 font-medium rounded-xl transition-all hover:opacity-90 disabled:opacity-50"
            style={{ background: 'var(--sage-green)', color: 'white' }}
          >
            ✓ Approve & Send Interview Invite
          </button>
          <button
            onClick={() => setShowRejectForm(true)}
            disabled={loading}
            className="flex-1 px-6 py-4 font-medium rounded-xl transition-all hover:opacity-90 disabled:opacity-50"
            style={{ background: 'var(--coral-warm)', color: 'white' }}
          >
            ✗ Reject Application
          </button>
        </div>
      ) : (
        <div className="space-y-4 p-6 rounded-xl" style={{ background: 'rgba(255, 107, 107, 0.05)', border: '1px solid rgba(255, 107, 107, 0.2)' }}>
          <h4 className="font-medium" style={{ color: 'var(--coral-warm)' }}>
            Rejection Reason (Optional)
          </h4>
          <textarea
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            placeholder="Add a note for your records..."
            className="w-full px-4 py-3 rounded-lg text-sm border-2"
            style={{ borderColor: 'var(--warm-gray)' }}
            rows={3}
          />
          <div className="flex gap-4">
            <button
              onClick={handleReject}
              disabled={loading}
              className="flex-1 px-6 py-3 font-medium rounded-xl transition-all hover:opacity-90 disabled:opacity-50"
              style={{ background: 'var(--coral-warm)', color: 'white' }}
            >
              {loading ? 'Sending...' : 'Confirm Rejection'}
            </button>
            <button
              onClick={() => setShowRejectForm(false)}
              disabled={loading}
              className="px-6 py-3 font-medium border-2 rounded-xl transition-all hover:opacity-70"
              style={{ borderColor: 'var(--navy-mid)', color: 'var(--navy-deep)' }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
