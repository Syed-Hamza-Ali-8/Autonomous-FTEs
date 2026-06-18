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
  const [rejectReason, setRejectReason] = useState('')
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const handleApprove = async () => {
    if (!confirm(`Approve ${approval.candidate_name} and send interview invite?`)) return

    setLoading(true)
    setMessage(null)
    try {
      await approveCandidate(approval.id)
      setMessage({ type: 'success', text: 'Candidate approved. Interview scheduling initiated.' })
      onComplete?.()
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to approve candidate' })
    } finally {
      setLoading(false)
    }
  }

  const handleReject = async () => {
    if (!confirm(`Reject ${approval.candidate_name}?`)) return

    setLoading(true)
    setMessage(null)
    try {
      await rejectCandidate(approval.id)
      setMessage({ type: 'success', text: 'Candidate rejected. Rejection email sent.' })
      onComplete?.()
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to reject candidate' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white shadow rounded-lg p-6 border-2 border-purple-200">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Pending Approval</h2>

      <div className="mb-4 p-4 bg-purple-50 rounded-lg">
        <p className="text-sm font-medium text-gray-700">AI Recommendation</p>
        <p className="text-lg font-semibold text-gray-900 capitalize mt-1">
          {approval.recommendation}
          {approval.confidence && (
            <span className="ml-2 text-sm font-normal text-gray-500">
              ({approval.confidence} confidence)
            </span>
          )}
        </p>
        <p className="text-sm text-gray-600 mt-2">Score: {approval.score?.toFixed?.(1) ?? approval.score}/100</p>
      </div>

      <p className="text-sm text-gray-700 mb-6">{approval.brief_summary}</p>

      {message && (
        <div
          className={`mb-4 p-3 rounded-lg text-sm ${
            message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
          }`}
        >
          {message.text}
        </div>
      )}

      {!showRejectForm ? (
        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={handleApprove}
            disabled={loading}
            className="flex-1 px-4 py-3 bg-green-600 text-white font-medium rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Processing...' : 'Approve — Send Interview Invite'}
          </button>
          <button
            onClick={() => setShowRejectForm(true)}
            disabled={loading}
            className="flex-1 px-4 py-3 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
          >
            Reject
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          <textarea
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            placeholder="Optional rejection reason (for your records)"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            rows={3}
          />
          <div className="flex gap-3">
            <button
              onClick={handleReject}
              disabled={loading}
              className="flex-1 px-4 py-2 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 disabled:opacity-50"
            >
              Confirm Reject
            </button>
            <button
              onClick={() => setShowRejectForm(false)}
              disabled={loading}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
