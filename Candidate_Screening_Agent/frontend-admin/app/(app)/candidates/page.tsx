'use client'

import { useEffect, useState, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { getCandidates, getCandidatesByStatus } from '@/lib/api'
import CandidateCard from '@/components/CandidateCard'

function CandidatesContent() {
  const searchParams = useSearchParams()
  const jobId = searchParams.get('job_id')

  const [candidates, setCandidates] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('all')

  const fetchCandidates = async () => {
    try {
      setLoading(true)
      setError(null)

      const jobIdNum = jobId ? parseInt(jobId) : undefined

      const data = statusFilter === 'all'
        ? await getCandidates(jobIdNum)
        : await getCandidatesByStatus(statusFilter)

      const filteredData = jobIdNum && statusFilter !== 'all'
        ? data.filter((c: any) => c.job_id === jobIdNum)
        : data

      setCandidates(filteredData)
    } catch (err: any) {
      setError(err.message || 'Failed to load candidates')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCandidates()
  }, [statusFilter, jobId])

  const statuses = [
    { value: 'all', label: 'All Candidates' },
    { value: 'queued', label: 'Queued' },
    { value: 'scoring', label: 'Scoring' },
    { value: 'scored', label: 'Scored' },
    { value: 'questions_sent', label: 'Questions Sent' },
    { value: 'awaiting_reply', label: 'Awaiting Reply' },
    { value: 'replied', label: 'Replied' },
    { value: 'shortlisted', label: 'Shortlisted' },
    { value: 'rejected', label: 'Rejected' },
    { value: 'hired', label: 'Hired' },
    { value: 'manual_review', label: 'Manual Review' },
  ]

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
            Loading candidates...
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
            Error Loading Candidates
          </h3>
          <p className="mb-4" style={{ color: 'var(--navy-mid)' }}>{error}</p>
          <button
            onClick={fetchCandidates}
            className="px-6 py-2 font-medium text-sm transition-colors hover:opacity-80"
            style={{ background: 'var(--coral-warm)', color: 'white' }}
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
              {jobId ? `Job #${jobId}` : 'Candidate Pipeline'}
            </div>
            <h1 className="font-display text-5xl lg:text-6xl leading-tight mb-6"
                style={{ color: 'var(--navy-deep)' }}>
              {jobId ? 'Job Candidates' : 'All Candidates'}
            </h1>
            <p className="text-xl leading-relaxed max-w-2xl"
               style={{ color: 'var(--navy-light)' }}>
              {jobId
                ? `Viewing candidates for job ID: ${jobId}`
                : 'View and manage all candidate applications'
              }
            </p>
          </div>

          {candidates.length > 0 && (
            <div className="hidden lg:block accent-line pl-6">
              <div className="font-display text-4xl mb-2"
                   style={{ color: 'var(--cyan-electric)' }}>
                {candidates.length}
              </div>
              <div className="font-mono text-xs uppercase tracking-wider"
                   style={{ color: 'var(--navy-mid)' }}>
                {candidates.length === 1 ? 'Candidate' : 'Candidates'}
              </div>
            </div>
          )}
        </div>

        {/* Divider */}
        <div className="h-px" style={{ background: 'var(--warm-gray)' }} />
      </div>

      {/* Status Filter */}
      <div className="mb-10">
        <label htmlFor="status-filter"
               className="block font-mono text-xs uppercase tracking-wider mb-3"
               style={{ color: 'var(--navy-mid)' }}>
          Filter by Status
        </label>
        <select
          id="status-filter"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="block w-full max-w-xs px-4 py-3 rounded-lg text-sm font-medium transition-colors"
          style={{
            background: 'var(--off-white)',
            border: '1px solid var(--warm-gray)',
            color: 'var(--navy-deep)',
          }}
        >
          {statuses.map((status) => (
            <option key={status.value} value={status.value}>
              {status.label}
            </option>
          ))}
        </select>
      </div>

      {/* Candidates Grid */}
      {candidates.length === 0 ? (
        <div className="text-center py-24">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full mb-6"
               style={{ background: 'var(--off-white)' }}>
            <svg className="w-10 h-10"
                 style={{ color: 'var(--navy-mid)' }}
                 fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <h3 className="font-display text-2xl mb-3"
              style={{ color: 'var(--navy-deep)' }}>
            No candidates found
          </h3>
          <p className="text-lg max-w-md mx-auto"
             style={{ color: 'var(--navy-light)' }}>
            {statusFilter === 'all'
              ? 'No candidates have applied yet.'
              : `No candidates with status "${statusFilter.replace('_', ' ')}".`}
          </p>
        </div>
      ) : (
        <>
          <div className="mb-6 font-mono text-xs uppercase tracking-wider"
               style={{ color: 'var(--navy-mid)' }}>
            Showing {candidates.length} candidate{candidates.length !== 1 ? 's' : ''}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {candidates.map((candidate, index) => (
              <div key={candidate.id}
                   className="reveal-up"
                   style={{ animationDelay: `${index * 0.05}s` }}>
                <CandidateCard candidate={candidate} />
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

export default function CandidatesPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="relative w-16 h-16 mx-auto mb-6">
            <div className="absolute inset-0 rounded-full border-2 animate-spin"
                 style={{ borderColor: 'var(--cyan-electric)', borderTopColor: 'transparent' }} />
          </div>
          <p className="font-mono text-sm uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>
            Loading candidates...
          </p>
        </div>
      </div>
    }>
      <CandidatesContent />
    </Suspense>
  )
}
