'use client'

import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { getCandidate, getCandidateBrief, getPendingApprovals, getCandidateInterview } from '@/lib/api'
import { formatDistanceToNow } from 'date-fns'

// Format date - show "Today" for same day, otherwise show date
function formatAppliedDate(dateStr: string): string {
  const date = new Date(dateStr)
  const today = new Date()
  if (date.toDateString() === today.toDateString()) {
    return 'Today'
  }
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

// Short timezone label (e.g. "PKT", "GMT+5") for an IANA zone at a given instant
function tzShortLabel(timeZone: string, atIso: string): string {
  try {
    const parts = new Intl.DateTimeFormat('en-US', {
      timeZone, timeZoneName: 'short',
    }).formatToParts(new Date(atIso))
    return parts.find((p) => p.type === 'timeZoneName')?.value ?? timeZone
  } catch {
    return timeZone
  }
}

// Format a UTC ISO time in a specific timezone, e.g. "Tue, Jul 28 · 08:00 PM – 08:45 PM"
function formatSlotInTz(startIso: string, endIso: string, timeZone: string): string {
  try {
    const dateOpts: Intl.DateTimeFormatOptions = {
      weekday: 'short', month: 'short', day: 'numeric', timeZone,
    }
    const timeOpts: Intl.DateTimeFormatOptions = {
      hour: '2-digit', minute: '2-digit', timeZone,
    }
    const day = new Date(startIso).toLocaleDateString('en-US', dateOpts)
    const start = new Date(startIso).toLocaleTimeString('en-US', timeOpts)
    const end = new Date(endIso).toLocaleTimeString('en-US', timeOpts)
    return `${day} · ${start} – ${end}`
  } catch {
    return ''
  }
}
import Link from 'next/link'
import ScoreBar from '@/components/ScoreBar'
import ApprovalPanel from '@/components/ApprovalPanel'

export default function CandidateDetailPage() {
  const params = useParams()
  const candidateId = parseInt(params.id as string)

  const [candidate, setCandidate] = useState<any>(null)
  const [brief, setBrief] = useState<any>(null)
  const [pendingApproval, setPendingApproval] = useState<any>(null)
  const [interview, setInterview] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const [candidateData, briefData, approvalsData, interviewData] = await Promise.all([
        getCandidate(candidateId),
        getCandidateBrief(candidateId).catch(() => null),
        getPendingApprovals(),
        getCandidateInterview(candidateId).catch(() => null),
      ])
      setCandidate(candidateData)
      setBrief(briefData)
      setPendingApproval(approvalsData.find((a: any) => a.candidate_id === candidateId) ?? null)
      setInterview(interviewData)
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
            Loading candidate details...
          </p>
        </div>
      </div>
    )
  }

  if (error || !candidate) {
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
            Candidate Not Found
          </h3>
          <p className="mb-4" style={{ color: 'var(--navy-mid)' }}>{error || 'This candidate does not exist.'}</p>
          <Link href="/candidates"
                className="px-6 py-2 font-medium text-sm transition-colors hover:opacity-80"
                style={{ background: 'var(--navy-deep)', color: 'var(--off-white)' }}>
            ← Back to Candidates
          </Link>
        </div>
      </div>
    )
  }

  const statusColors: Record<string, string> = {
    queued: 'bg-gray-100 text-gray-800',
    scoring: 'bg-blue-100 text-blue-800',
    scored: 'bg-blue-100 text-blue-800',
    screening: 'bg-blue-100 text-blue-800',
    questions_sent: 'bg-yellow-100 text-yellow-800',
    awaiting_reply: 'bg-yellow-100 text-yellow-800',
    replied: 'bg-yellow-100 text-yellow-800',
    pending_approval: 'bg-purple-100 text-purple-800',
    approved: 'bg-green-100 text-green-800',
    rejected: 'bg-red-100 text-red-800',
    manual_review: 'bg-orange-100 text-orange-800',
    shortlisted: 'bg-purple-100 text-purple-800',
    hired: 'bg-green-100 text-green-800',
  }

  const statusColor = statusColors[candidate.status] || 'bg-gray-100 text-gray-800'
  const strengths = brief?.strengths ?? candidate.strengths ?? []
  const weaknesses = brief?.weaknesses ?? candidate.weaknesses ?? []
  const redFlags = brief?.red_flags ?? candidate.red_flags ?? []

  return (
    <div className="max-w-7xl mx-auto px-6 lg:px-12 py-16">
      {/* Breadcrumb */}
      <Link href="/candidates"
            className="inline-flex items-center font-mono text-xs uppercase tracking-wider mb-8 transition-colors hover:opacity-70"
            style={{ color: 'var(--navy-mid)' }}>
        ← Back to Candidates
      </Link>

      {/* Candidate Header */}
      <div className="mb-10">
        <div className="flex items-start justify-between gap-8">
          <div className="flex-1">
            <div className="font-mono text-xs uppercase tracking-wider mb-4"
                 style={{ color: 'var(--navy-mid)' }}>
              Candidate Profile
            </div>
            <h1 className="font-display text-5xl lg:text-6xl leading-tight mb-4"
                style={{ color: 'var(--navy-deep)' }}>
              {candidate.name || candidate.email}
            </h1>
            {candidate.email && (
              <p className="text-xl" style={{ color: 'var(--navy-light)' }}>
                {candidate.email}
              </p>
            )}
            {brief?.job_title && (
              <p className="mt-2 font-mono text-sm" style={{ color: 'var(--navy-mid)' }}>
                Role: {brief.job_title}
              </p>
            )}
            <p className="mt-3 font-mono text-xs uppercase tracking-wider"
               style={{ color: 'var(--navy-mid)' }}>
              Applied {formatAppliedDate(candidate.created_at)}
            </p>
          </div>

          <div className="flex flex-col items-end gap-4">
            <span className={`inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium ${statusColor}`}>
              {candidate.status.replace(/_/g, ' ')}
            </span>
          </div>
        </div>

        {/* Divider */}
        <div className="h-px mt-8" style={{ background: 'var(--warm-gray)' }} />
      </div>

      {/* Confirmed Interview Slot */}
      {interview && interview.slot_id && (
        <div className="mb-10">
          <h2 className="font-display text-2xl mb-6" style={{ color: 'var(--navy-deep)' }}>
            Confirmed Interview
          </h2>
          <div
            className="p-8 rounded-2xl"
            style={{ background: 'rgba(78, 205, 196, 0.05)', border: '1px solid rgba(78, 205, 196, 0.25)' }}
          >
            <div className="flex flex-wrap items-start justify-between gap-6">
              <div className="space-y-4">
                <div>
                  <p className="font-mono text-xs uppercase tracking-wider mb-2" style={{ color: 'var(--navy-mid)' }}>
                    Date &amp; Time
                  </p>
                  {/* Company standard time (UTC) */}
                  <div className="mb-3">
                    <p className="font-mono text-[11px] uppercase tracking-wider mb-1" style={{ color: 'var(--navy-light)' }}>
                      Company standard · UTC
                    </p>
                    <p className="font-display text-xl leading-snug" style={{ color: 'var(--navy-deep)' }}>
                      {formatSlotInTz(interview.start_time, interview.end_time, 'UTC')} UTC
                    </p>
                  </div>
                  {/* Candidate's local time, if we captured one */}
                  {interview.candidate_timezone && (
                    <div>
                      <p className="font-mono text-[11px] uppercase tracking-wider mb-1" style={{ color: 'var(--navy-light)' }}>
                        Candidate local · {tzShortLabel(interview.candidate_timezone, interview.start_time)}
                      </p>
                      <p className="font-display text-xl leading-snug" style={{ color: 'var(--navy-deep)' }}>
                        {formatSlotInTz(interview.start_time, interview.end_time, interview.candidate_timezone)}
                        {' '}
                        {tzShortLabel(interview.candidate_timezone, interview.start_time)}
                      </p>
                    </div>
                  )}
                </div>
                <div>
                  <p className="font-mono text-xs uppercase tracking-wider mb-1" style={{ color: 'var(--navy-mid)' }}>
                    Status
                  </p>
                  <span
                    className="inline-flex items-center px-3 py-1 rounded-full text-xs font-mono uppercase tracking-wider"
                    style={{
                      background: interview.status === 'booked'
                        ? 'rgba(78, 205, 196, 0.15)' : 'rgba(255, 191, 0, 0.15)',
                      color: interview.status === 'booked'
                        ? 'var(--sage-green)' : '#B8860B',
                    }}
                  >
                    {interview.status}
                  </span>
                </div>
              </div>
              {interview.meeting_link && (
                <a
                  href={interview.meeting_link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-6 py-3 rounded-lg font-mono text-sm uppercase tracking-wider transition-opacity hover:opacity-80"
                  style={{ background: 'var(--sage-green)', color: 'var(--navy-deep)' }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M15 10l4.553-2.069A1 1 0 0121 8.87v6.26a1 1 0 01-1.447.9L15 14M3 8a2 2 0 012-2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z"/>
                  </svg>
                  Join Meet
                </a>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Pending Approval */}
      {pendingApproval && (
        <div className="mb-10">
          <ApprovalPanel
            approval={{
              ...pendingApproval,
              confidence: candidate.confidence,
            }}
            onComplete={fetchData}
          />
        </div>
      )}

      {/* Score */}
      {candidate.total_score !== null && candidate.total_score !== undefined && (
        <div className="mb-10">
          <h2 className="font-display text-2xl mb-6" style={{ color: 'var(--navy-deep)' }}>
            Screening Score
          </h2>
          <div className="p-8 rounded-2xl"
               style={{ background: 'var(--off-white)', border: '1px solid var(--warm-gray)' }}>
            <ScoreBar
              totalScore={candidate.total_score}
              scoreBreakdown={candidate.score_breakdown}
            />
            {candidate.recommendation && (
              <div className="mt-6 p-6 rounded-lg"
                   style={{ background: 'rgba(0, 229, 255, 0.05)', border: '1px solid rgba(0, 229, 255, 0.15)' }}>
                <p className="font-mono text-xs uppercase tracking-wider mb-2"
                   style={{ color: 'var(--navy-mid)' }}>
                  AI Recommendation
                </p>
                <p className="font-display text-lg" style={{ color: 'var(--navy-deep)' }}>
                  {candidate.recommendation}
                  {candidate.confidence && (
                    <span className="ml-2 font-mono text-sm" style={{ color: 'var(--navy-light)' }}>
                      ({candidate.confidence} confidence)
                    </span>
                  )}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Strengths / Weaknesses / Red Flags */}
      {(strengths.length > 0 || weaknesses.length > 0 || redFlags.length > 0) && (
        <div className="mb-10">
          <h2 className="font-display text-2xl mb-6" style={{ color: 'var(--navy-deep)' }}>
            Analysis
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {strengths.length > 0 && (
              <div className="p-6 rounded-2xl"
                   style={{ background: 'rgba(78, 205, 196, 0.05)', border: '1px solid rgba(78, 205, 196, 0.2)' }}>
                <h3 className="font-mono text-xs uppercase tracking-wider mb-4"
                    style={{ color: 'var(--sage-green)' }}>
                  Strengths
                </h3>
                <ul className="space-y-3">
                  {strengths.map((item: string, i: number) => (
                    <li key={i} className="text-sm leading-relaxed"
                        style={{ color: 'var(--navy-deep)' }}>
                      <span className="mr-2" style={{ color: 'var(--sage-green)' }}>+</span>{item}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {weaknesses.length > 0 && (
              <div className="p-6 rounded-2xl"
                   style={{ background: 'rgba(255, 191, 0, 0.05)', border: '1px solid rgba(255, 191, 0, 0.2)' }}>
                <h3 className="font-mono text-xs uppercase tracking-wider mb-4"
                    style={{ color: '#B8860B' }}>
                  Weaknesses
                </h3>
                <ul className="space-y-3">
                  {weaknesses.map((item: string, i: number) => (
                    <li key={i} className="text-sm leading-relaxed"
                        style={{ color: 'var(--navy-deep)' }}>
                      <span className="mr-2" style={{ color: '#B8860B' }}>−</span>{item}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {redFlags.length > 0 && (
              <div className="p-6 rounded-2xl"
                   style={{ background: 'rgba(255, 107, 107, 0.05)', border: '1px solid rgba(255, 107, 107, 0.2)' }}>
                <h3 className="font-mono text-xs uppercase tracking-wider mb-4"
                    style={{ color: 'var(--coral-warm)' }}>
                  Red Flags
                </h3>
                <ul className="space-y-3">
                  {redFlags.map((item: string, i: number) => (
                    <li key={i} className="text-sm leading-relaxed"
                        style={{ color: 'var(--navy-deep)' }}>
                      <span className="mr-2" style={{ color: 'var(--coral-warm)' }}>!</span>{item}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Screening Q&A */}
      {candidate.screening_questions && candidate.screening_questions.length > 0 && (
        <div className="mb-10">
          <h2 className="font-display text-2xl mb-6" style={{ color: 'var(--navy-deep)' }}>
            Screening Q&A
          </h2>
          <div className="space-y-6">
            {candidate.screening_questions.map((question: string, index: number) => (
              <div key={index}
                   className="p-6 rounded-2xl"
                   style={{ background: 'var(--off-white)', border: '1px solid var(--warm-gray)' }}>
                <p className="font-mono text-xs uppercase tracking-wider mb-3"
                   style={{ color: 'var(--navy-mid)' }}>
                  Question {index + 1}
                </p>
                <p className="text-base leading-relaxed" style={{ color: 'var(--navy-deep)' }}>
                  {question}
                </p>
              </div>
            ))}
            {candidate.candidate_reply && (
              <div className="p-6 rounded-2xl"
                   style={{ background: 'rgba(0, 229, 255, 0.03)', border: '1px solid rgba(0, 229, 255, 0.12)' }}>
                <p className="font-mono text-xs uppercase tracking-wider mb-3"
                   style={{ color: 'var(--navy-mid)' }}>
                  Candidate Reply
                </p>
                <p className="text-base leading-relaxed whitespace-pre-wrap"
                   style={{ color: 'var(--navy-deep)' }}>
                  {candidate.candidate_reply}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Reply Analysis */}
      {candidate.reply_analysis && (
        <div className="mb-10">
          <h2 className="font-display text-2xl mb-6" style={{ color: 'var(--navy-deep)' }}>
            Reply Analysis
          </h2>
          <div className="p-8 rounded-2xl"
               style={{ background: 'var(--off-white)', border: '1px solid var(--warm-gray)' }}>
            {candidate.reply_analysis.brief_summary && (
              <p className="text-base leading-relaxed mb-6" style={{ color: 'var(--navy-deep)' }}>
                {candidate.reply_analysis.brief_summary?.replace(/^JSON\s*/i, '')}
              </p>
            )}
            {candidate.reply_analysis.notable_answers?.length > 0 && (
              <ul className="space-y-3">
                {candidate.reply_analysis.notable_answers.map((note: string, i: number) => (
                  <li key={i} className="text-sm leading-relaxed"
                      style={{ color: 'var(--navy-deep)' }}>
                    <span className="mr-2" style={{ color: 'var(--cyan-electric)' }}>•</span>{note}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}

      {/* CV / Resume */}
      {candidate.cv_text && (
        <div className="mb-10">
          <h2 className="font-display text-2xl mb-6" style={{ color: 'var(--navy-deep)' }}>
            CV / Resume
          </h2>
          <div className="p-8 rounded-2xl max-h-[600px] overflow-y-auto"
               style={{ background: 'var(--off-white)', border: '1px solid var(--warm-gray)' }}>
            <div
              className="leading-relaxed whitespace-pre-wrap"
              style={{ fontFamily: 'Georgia, "Times New Roman", serif', fontSize: '15px', lineHeight: '1.8', color: 'var(--navy-deep)' }}
            >
              {candidate.cv_text}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
