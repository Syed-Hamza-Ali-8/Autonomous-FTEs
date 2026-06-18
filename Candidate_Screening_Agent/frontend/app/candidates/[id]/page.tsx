'use client'

import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { getCandidate, getCandidateBrief, getPendingApprovals } from '@/lib/api'
import { formatDistanceToNow } from 'date-fns'
import Link from 'next/link'
import ScoreBar from '@/components/ScoreBar'
import ApprovalPanel from '@/components/ApprovalPanel'

export default function CandidateDetailPage() {
  const params = useParams()
  const candidateId = parseInt(params.id as string)

  const [candidate, setCandidate] = useState<any>(null)
  const [brief, setBrief] = useState<any>(null)
  const [pendingApproval, setPendingApproval] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const [candidateData, briefData, approvalsData] = await Promise.all([
        getCandidate(candidateId),
        getCandidateBrief(candidateId).catch(() => null),
        getPendingApprovals(),
      ])
      setCandidate(candidateData)
      setBrief(briefData)
      setPendingApproval(approvalsData.find((a: any) => a.candidate_id === candidateId) ?? null)
    } catch (err: any) {
      setError(err.message || 'Failed to load candidate details')
    } finally {
      setLoading(false)
    }
  }, [candidateId])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto" />
          <p className="mt-4 text-gray-600">Loading candidate details...</p>
        </div>
      </div>
    )
  }

  if (error || !candidate) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error: {error || 'Candidate not found'}</p>
        <Link href="/candidates" className="mt-2 inline-block text-sm text-red-600 hover:text-red-500 font-medium">
          ← Back to Candidates
        </Link>
      </div>
    )
  }

  const statusColors: Record<string, string> = {
    queued: 'bg-gray-100 text-gray-800',
    screening: 'bg-blue-100 text-blue-800',
    awaiting_reply: 'bg-yellow-100 text-yellow-800',
    pending_approval: 'bg-purple-100 text-purple-800',
    approved: 'bg-green-100 text-green-800',
    rejected: 'bg-red-100 text-red-800',
    manual_review: 'bg-orange-100 text-orange-800',
    shortlisted: 'bg-purple-100 text-purple-800',
  }

  const statusColor = statusColors[candidate.status] || 'bg-gray-100 text-gray-800'
  const strengths = brief?.strengths ?? candidate.strengths ?? []
  const weaknesses = brief?.weaknesses ?? candidate.weaknesses ?? []
  const redFlags = brief?.red_flags ?? candidate.red_flags ?? []

  return (
    <div className="px-4 sm:px-0 max-w-5xl mx-auto">
      <Link href="/candidates" className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 mb-4">
        ← Back to Candidates
      </Link>

      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{candidate.name || candidate.email}</h1>
            <p className="text-lg text-gray-500 mt-1">{candidate.email}</p>
            {brief?.job_title && (
              <p className="text-sm text-gray-600 mt-1">Role: {brief.job_title}</p>
            )}
            <p className="text-sm text-gray-500 mt-2">
              Applied {formatDistanceToNow(new Date(candidate.created_at), { addSuffix: true })}
            </p>
          </div>
          <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${statusColor}`}>
            {candidate.status.replace(/_/g, ' ')}
          </span>
        </div>
      </div>

      {pendingApproval && (
        <div className="mb-6">
          <ApprovalPanel
            approval={{
              ...pendingApproval,
              confidence: candidate.confidence,
            }}
            onComplete={fetchData}
          />
        </div>
      )}

      {candidate.total_score !== null && candidate.total_score !== undefined && (
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Screening Score</h2>
          <ScoreBar
            totalScore={candidate.total_score}
            scoreBreakdown={candidate.score_breakdown}
          />
          {candidate.recommendation && (
            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <p className="text-sm font-medium text-gray-700">AI Recommendation</p>
              <p className="text-sm text-gray-900 mt-1 capitalize">
                {candidate.recommendation}
                {candidate.confidence && ` (${candidate.confidence} confidence)`}
              </p>
            </div>
          )}
        </div>
      )}

      {(strengths.length > 0 || weaknesses.length > 0 || redFlags.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          {strengths.length > 0 && (
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-sm font-semibold text-green-700 uppercase tracking-wide mb-3">Strengths</h3>
              <ul className="space-y-2">
                {strengths.map((item: string, i: number) => (
                  <li key={i} className="text-sm text-gray-700 flex gap-2">
                    <span className="text-green-500">+</span> {item}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {weaknesses.length > 0 && (
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-sm font-semibold text-yellow-700 uppercase tracking-wide mb-3">Weaknesses</h3>
              <ul className="space-y-2">
                {weaknesses.map((item: string, i: number) => (
                  <li key={i} className="text-sm text-gray-700 flex gap-2">
                    <span className="text-yellow-500">−</span> {item}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {redFlags.length > 0 && (
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-sm font-semibold text-red-700 uppercase tracking-wide mb-3">Red Flags</h3>
              <ul className="space-y-2">
                {redFlags.map((item: string, i: number) => (
                  <li key={i} className="text-sm text-gray-700 flex gap-2">
                    <span className="text-red-500">!</span> {item}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {candidate.screening_questions && candidate.screening_questions.length > 0 && (
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Screening Q&amp;A</h2>
          <div className="space-y-4">
            {candidate.screening_questions.map((question: string, index: number) => (
              <div key={index} className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm font-medium text-gray-700">Question {index + 1}</p>
                <p className="text-sm text-gray-900 mt-1">{question}</p>
                {candidate.candidate_reply && (
                  <p className="text-sm text-gray-600 mt-2 italic">
                    See full reply below for answer details.
                  </p>
                )}
              </div>
            ))}
          </div>
          {candidate.candidate_reply && (
            <div className="mt-4 p-4 border border-gray-200 rounded-lg">
              <p className="text-sm font-medium text-gray-700 mb-2">Candidate Reply</p>
              <p className="text-sm text-gray-900 whitespace-pre-wrap">{candidate.candidate_reply}</p>
            </div>
          )}
        </div>
      )}

      {candidate.reply_analysis && (
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Reply Analysis</h2>
          {candidate.reply_analysis.brief_summary && (
            <p className="text-sm text-gray-700 mb-4">{candidate.reply_analysis.brief_summary}</p>
          )}
          {candidate.reply_analysis.notable_answers?.length > 0 && (
            <ul className="space-y-2">
              {candidate.reply_analysis.notable_answers.map((note: string, i: number) => (
                <li key={i} className="text-sm text-gray-700">• {note}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {candidate.cv_text && (
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">CV / Resume</h2>
          <div className="bg-white border-2 border-gray-200 rounded-lg p-8 max-h-[600px] overflow-y-auto">
            <div
              className="font-serif text-gray-900 leading-relaxed whitespace-pre-wrap"
              style={{ fontFamily: 'Georgia, "Times New Roman", serif', fontSize: '15px', lineHeight: '1.8' }}
            >
              {candidate.cv_text}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
