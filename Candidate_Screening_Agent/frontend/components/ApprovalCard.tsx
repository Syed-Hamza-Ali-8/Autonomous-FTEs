'use client'

import { useState } from 'react'
import { approveCandidate, rejectCandidate } from '@/lib/api'

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

  const handleApprove = async () => {
    if (!confirm(`Approve ${approval.candidate_name} for ${approval.job_title}?`)) {
      return
    }

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
    if (!confirm(`Reject ${approval.candidate_name} for ${approval.job_title}?`)) {
      return
    }

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

  const actionColor = approval.action === 'approve' ? 'text-green-600' : 'text-red-600'
  const actionBg = approval.action === 'approve' ? 'bg-green-50' : 'bg-red-50'

  return (
    <div className={`bg-white shadow rounded-lg p-6 border-l-4 ${approval.action === 'approve' ? 'border-green-500' : 'border-red-500'}`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            {approval.candidate_name}
          </h3>
          <p className="text-sm text-gray-500">{approval.candidate_email}</p>
          <p className="text-sm text-gray-600 mt-1">
            Position: <span className="font-medium">{approval.job_title}</span>
          </p>
        </div>
        <div className={`px-3 py-1 rounded-full ${actionBg}`}>
          <span className={`text-sm font-semibold ${actionColor} capitalize`}>
            AI Recommends: {approval.action}
          </span>
        </div>
      </div>

      {/* Score */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Overall Score</span>
          <span className="text-2xl font-bold text-gray-900">{approval.score.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full ${approval.score >= 70 ? 'bg-green-500' : approval.score >= 50 ? 'bg-yellow-500' : 'bg-red-500'}`}
            style={{ width: `${approval.score}%` }}
          />
        </div>
      </div>

      {/* AI Recommendation */}
      <div className="mb-4 p-4 bg-gray-50 rounded-lg">
        <p className="text-sm font-medium text-gray-700 mb-2">AI Recommendation:</p>
        <p className="text-sm text-gray-900 capitalize">{approval.recommendation}</p>
      </div>

      {/* Brief Summary */}
      <div className="mb-6 p-4 bg-blue-50 rounded-lg">
        <p className="text-sm font-medium text-gray-700 mb-2">Summary:</p>
        <p className="text-sm text-gray-900">{approval.brief_summary}</p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3">
        <button
          onClick={handleApprove}
          disabled={loading}
          className="flex-1 bg-green-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Processing...' : '✓ Approve & Send Interview Invite'}
        </button>
        <button
          onClick={handleReject}
          disabled={loading}
          className="flex-1 bg-red-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Processing...' : '✗ Reject & Send Rejection Email'}
        </button>
      </div>

      {/* View Full Details Link */}
      <div className="mt-4 text-center">
        <a
          href={`/candidates/${approval.candidate_id}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-primary-600 hover:text-primary-500 font-medium"
        >
          View Full Candidate Profile →
        </a>
      </div>
    </div>
  )
}
