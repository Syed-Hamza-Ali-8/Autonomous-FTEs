'use client'

import { useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { getCandidates, getCandidatesByStatus } from '@/lib/api'
import CandidateCard from '@/components/CandidateCard'

export default function CandidatesPage() {
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

      // Parse job_id if present
      const jobIdNum = jobId ? parseInt(jobId) : undefined

      const data = statusFilter === 'all'
        ? await getCandidates(jobIdNum)
        : await getCandidatesByStatus(statusFilter)

      // If job_id is specified and we're filtering by status,
      // we need to filter the results by job_id on the client side
      // (since getCandidatesByStatus doesn't support job_id filtering yet)
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
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading candidates...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error: {error}</p>
        <button
          onClick={fetchCandidates}
          className="mt-2 text-sm text-red-600 hover:text-red-500 font-medium"
        >
          Try Again
        </button>
      </div>
    )
  }

  return (
    <div className="px-4 sm:px-0">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">
          {jobId ? 'Job Candidates' : 'All Candidates'}
        </h1>
        <p className="mt-2 text-gray-600">
          {jobId
            ? `Viewing candidates for job ID: ${jobId}`
            : 'View and manage all candidate applications'
          }
        </p>
      </div>

      {/* Status Filter */}
      <div className="mb-6">
        <label htmlFor="status-filter" className="block text-sm font-medium text-gray-700 mb-2">
          Filter by Status
        </label>
        <select
          id="status-filter"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="block w-full max-w-xs px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500"
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
        <div className="bg-white shadow rounded-lg p-12 text-center">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No candidates found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {statusFilter === 'all'
              ? 'No candidates have applied yet.'
              : `No candidates with status "${statusFilter.replace('_', ' ')}".`}
          </p>
        </div>
      ) : (
        <>
          <div className="mb-4 text-sm text-gray-600">
            Showing {candidates.length} candidate{candidates.length !== 1 ? 's' : ''}
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {candidates.map((candidate) => (
              <CandidateCard key={candidate.id} candidate={candidate} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}
