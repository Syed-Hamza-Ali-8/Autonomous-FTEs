'use client'

import { useEffect, useState, useRef } from 'react'
import { getJobs, createJob } from '@/lib/api'
import JobCard from '@/components/JobCard'
import { useSession } from 'next-auth/react'

const STORAGE_KEY = 'jobs_page_data'

export default function JobsPage() {
  const [jobs, setJobs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const { data: session } = useSession()
  const hasLoadedRef = useRef(false)

  // Create Job Modal State
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    rubric_path: '',
    hiring_manager_email: ''
  })

  const fetchJobs = async () => {
    try {
      setError(null)
      const data = await getJobs()
      setJobs(data)
      // Store in localStorage for persistence
      if (typeof window !== 'undefined') {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load jobs')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateJob = async (e: React.FormEvent) => {
    e.preventDefault()
    setCreating(true)
    setCreateError(null)

    try {
      await createJob({
        title: formData.title,
        description: formData.description,
        rubric_path: formData.rubric_path,
        hiring_manager_email: formData.hiring_manager_email || undefined
      })

      setFormData({
        title: '',
        description: '',
        rubric_path: '',
        hiring_manager_email: ''
      })
      setIsCreateModalOpen(false)
      await fetchJobs()
    } catch (err: any) {
      setCreateError(err.response?.data?.detail || err.message || 'Failed to create job')
    } finally {
      setCreating(false)
    }
  }

  useEffect(() => {
    // Load from localStorage first (instant), then fetch fresh data
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        try {
          setJobs(JSON.parse(stored))
          setLoading(false)
        } catch (e) {
          // Invalid JSON, ignore
        }
      }
    }

    // Only fetch if we haven't loaded yet OR if data is empty
    if (!hasLoadedRef.current) {
      hasLoadedRef.current = true
      fetchJobs()
    }
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
            Loading positions...
          </p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto mt-12">
        <div className="border-l-4 p-8"
             style={{
               borderColor: 'var(--coral-warm)',
               background: 'rgba(255, 107, 107, 0.05)'
             }}>
          <div className="flex items-start gap-4">
            <svg className="w-6 h-6 flex-shrink-0 mt-1"
                 style={{ color: 'var(--coral-warm)' }}
                 fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div className="flex-1">
              <h3 className="font-display text-xl mb-2"
                  style={{ color: 'var(--navy-deep)' }}>
                Error Loading Jobs
              </h3>
              <p className="mb-4" style={{ color: 'var(--navy-mid)' }}>
                {error}
              </p>
              <button
                onClick={fetchJobs}
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
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-6 lg:px-12 py-16">
      {/* Header - Different for Admin vs Candidate */}
      <div className="mb-16">
        <div className="flex items-start justify-between gap-8 mb-8">
          <div className="flex-1">
            <div className="font-mono text-xs uppercase tracking-wider mb-4"
                 style={{ color: 'var(--navy-mid)' }}>
              {session ? 'Job Management' : 'Open Positions'}
            </div>
            <h1 className="font-display text-5xl lg:text-6xl leading-tight mb-6"
                style={{ color: 'var(--navy-deep)' }}>
              {session ? 'Manage Positions' : 'Join Our Team'}
            </h1>
            <p className="text-xl leading-relaxed max-w-2xl"
               style={{ color: 'var(--navy-light)' }}>
              {session
                ? 'View and manage all job postings. Monitor candidate pipelines and track hiring progress.'
                : 'We\'re looking for exceptional talent. Our AI-powered screening ensures your application gets the attention it deserves.'
              }
            </p>
          </div>

          {/* Admin: Create Job Button + Stats */}
          {session ? (
            <div className="hidden lg:flex flex-col gap-4">
              <button
                onClick={() => setIsCreateModalOpen(true)}
                className="px-6 py-3 font-medium transition-all hover:opacity-90 whitespace-nowrap"
                style={{
                  background: 'var(--cyan-electric)',
                  color: 'var(--navy-deep)'
                }}
              >
                + Create New Job
              </button>
              {jobs.length > 0 && (
                <div className="accent-line pl-6">
                  <div className="font-display text-4xl mb-2"
                       style={{ color: 'var(--cyan-electric)' }}>
                    {jobs.length}
                  </div>
                  <div className="font-mono text-xs uppercase tracking-wider"
                       style={{ color: 'var(--navy-mid)' }}>
                    {jobs.length === 1 ? 'Position' : 'Positions'}
                  </div>
                </div>
              )}
            </div>
          ) : (
            jobs.length > 0 && (
              <div className="hidden lg:block accent-line pl-6">
                <div className="font-display text-4xl mb-2"
                     style={{ color: 'var(--cyan-electric)' }}>
                  {jobs.length}
                </div>
                <div className="font-mono text-xs uppercase tracking-wider"
                     style={{ color: 'var(--navy-mid)' }}>
                  {jobs.length === 1 ? 'Position' : 'Positions'}
                </div>
              </div>
            )
          )}
        </div>

        {/* Divider */}
        <div className="h-px" style={{ background: 'var(--warm-gray)' }} />
      </div>

      {/* Search Bar */}
      <div className="mb-10">
        <div className="relative max-w-md">
          <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 pointer-events-none"
               style={{ color: 'var(--navy-mid)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
          </svg>
          <input
            type="text"
            placeholder="Search jobs by title, company, description..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-12 pr-4 py-3 border-2 text-sm font-medium transition-all focus:outline-none"
            style={{
              borderColor: 'var(--warm-gray)',
              color: 'var(--navy-deep)',
              background: 'white'
            }}
            onFocus={(e) => e.target.style.borderColor = 'var(--cyan-electric)'}
            onBlur={(e) => e.target.style.borderColor = 'var(--warm-gray)'}
          />
        </div>
      </div>

      {/* Jobs Grid */}
      {(() => {
        const filtered = searchQuery.trim()
          ? jobs.filter(j =>
              j.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
              j.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
              j.company_name?.toLowerCase().includes(searchQuery.toLowerCase())
            )
          : jobs
        return filtered.length === 0 ? (
        <div className="text-center py-24">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-full mb-6"
               style={{ background: 'var(--off-white)' }}>
            <svg className="w-10 h-10"
                 style={{ color: 'var(--navy-mid)' }}
                 fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                    d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <h3 className="font-display text-2xl mb-3"
              style={{ color: 'var(--navy-deep)' }}>
            No {searchQuery ? 'Matching' : 'Open'} Positions
          </h3>
          <p className="text-lg max-w-md mx-auto"
             style={{ color: 'var(--navy-light)' }}>
            {searchQuery
              ? `No positions match "${searchQuery}". Try a different search term.`
              : "We don't have any openings at the moment, but check back soon."}
          </p>
          {searchQuery && (
            <button onClick={() => setSearchQuery('')}
                    className="mt-4 px-5 py-2 text-sm font-medium transition-colors hover:opacity-80"
                    style={{ background: 'var(--cyan-electric)', color: 'var(--navy-deep)' }}>
              Clear Search
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {filtered.map((job, index) => (
            <div key={job.id}
                 className="reveal-up"
                 style={{ animationDelay: `${index * 0.1}s` }}>
              <JobCard job={job} isAdmin={!!session} />
            </div>
          ))}
        </div>
      )
      })()}

      {/* Create Job Modal - Only for Admins */}
      {session && isCreateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
             style={{ background: 'rgba(10, 22, 40, 0.8)' }}
             onClick={() => setIsCreateModalOpen(false)}>
          <div className="max-w-2xl w-full border-l-4 p-8"
               style={{
                 borderColor: 'var(--cyan-electric)',
                 background: 'white',
                 boxShadow: 'var(--shadow-hard)',
                 maxHeight: '90vh',
                 overflowY: 'auto'
               }}
               onClick={(e) => e.stopPropagation()}>
            {/* Modal Header */}
            <div className="flex items-start justify-between mb-8">
              <div>
                <h2 className="font-display text-3xl mb-2"
                    style={{ color: 'var(--navy-deep)' }}>
                  Create New Job
                </h2>
                <p className="text-sm"
                   style={{ color: 'var(--navy-mid)' }}>
                  Add a new position to start screening candidates
                </p>
              </div>
              <button
                onClick={() => setIsCreateModalOpen(false)}
                className="p-2 transition-opacity hover:opacity-70"
                style={{ color: 'var(--navy-mid)' }}>
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Error Message */}
            {createError && (
              <div className="mb-6 p-4 border-l-4"
                   style={{
                     borderColor: 'var(--coral-warm)',
                     background: 'rgba(255, 107, 107, 0.05)'
                   }}>
                <p style={{ color: 'var(--coral-warm)' }}>{createError}</p>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleCreateJob} className="space-y-6">
              {/* Job Title */}
              <div>
                <label htmlFor="title"
                       className="block font-medium mb-3 text-sm uppercase tracking-wider"
                       style={{ color: 'var(--navy-mid)' }}>
                  Job Title *
                </label>
                <input
                  type="text"
                  id="title"
                  required
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full px-4 py-3 border-2 font-medium transition-all focus:outline-none"
                  style={{
                    borderColor: 'var(--warm-gray)',
                    color: 'var(--navy-deep)',
                    background: 'white'
                  }}
                  onFocus={(e) => e.target.style.borderColor = 'var(--cyan-electric)'}
                  onBlur={(e) => e.target.style.borderColor = 'var(--warm-gray)'}
                  placeholder="e.g., Senior Backend Engineer"
                />
              </div>

              {/* Job Description */}
              <div>
                <label htmlFor="description"
                       className="block font-medium mb-3 text-sm uppercase tracking-wider"
                       style={{ color: 'var(--navy-mid)' }}>
                  Job Description *
                </label>
                <textarea
                  id="description"
                  required
                  rows={6}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="w-full px-4 py-3 border-2 font-medium transition-all focus:outline-none resize-none"
                  style={{
                    borderColor: 'var(--warm-gray)',
                    color: 'var(--navy-deep)',
                    background: 'white'
                  }}
                  onFocus={(e) => e.target.style.borderColor = 'var(--cyan-electric)'}
                  onBlur={(e) => e.target.style.borderColor = 'var(--warm-gray)'}
                  placeholder="Describe the role, responsibilities, and requirements..."
                />
              </div>

              {/* Rubric Path */}
              <div>
                <label htmlFor="rubric_path"
                       className="block font-medium mb-3 text-sm uppercase tracking-wider"
                       style={{ color: 'var(--navy-mid)' }}>
                  Rubric Path *
                </label>
                <input
                  type="text"
                  id="rubric_path"
                  required
                  value={formData.rubric_path}
                  onChange={(e) => setFormData({ ...formData, rubric_path: e.target.value })}
                  className="w-full px-4 py-3 border-2 font-medium transition-all focus:outline-none"
                  style={{
                    borderColor: 'var(--warm-gray)',
                    color: 'var(--navy-deep)',
                    background: 'white'
                  }}
                  onFocus={(e) => e.target.style.borderColor = 'var(--cyan-electric)'}
                  onBlur={(e) => e.target.style.borderColor = 'var(--warm-gray)'}
                  placeholder="e.g., rubrics/backend_engineer.md"
                />
                <p className="mt-2 text-xs"
                   style={{ color: 'var(--navy-mid)' }}>
                  Path to the scoring rubric file for AI evaluation
                </p>
              </div>

              {/* Hiring Manager Email */}
              <div>
                <label htmlFor="hiring_manager_email"
                       className="block font-medium mb-3 text-sm uppercase tracking-wider"
                       style={{ color: 'var(--navy-mid)' }}>
                  Hiring Manager Email (Optional)
                </label>
                <input
                  type="email"
                  id="hiring_manager_email"
                  value={formData.hiring_manager_email}
                  onChange={(e) => setFormData({ ...formData, hiring_manager_email: e.target.value })}
                  className="w-full px-4 py-3 border-2 font-medium transition-all focus:outline-none"
                  style={{
                    borderColor: 'var(--warm-gray)',
                    color: 'var(--navy-deep)',
                    background: 'white'
                  }}
                  onFocus={(e) => e.target.style.borderColor = 'var(--cyan-electric)'}
                  onBlur={(e) => e.target.style.borderColor = 'var(--warm-gray)'}
                  placeholder="hiring.manager@company.com"
                />
              </div>

              {/* Action Buttons */}
              <div className="flex gap-4 pt-4">
                <button
                  type="button"
                  onClick={() => setIsCreateModalOpen(false)}
                  className="flex-1 px-6 py-3 font-medium border-2 transition-all hover:opacity-70"
                  style={{
                    borderColor: 'var(--navy-deep)',
                    color: 'var(--navy-deep)',
                    background: 'transparent'
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="flex-1 px-6 py-3 font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90"
                  style={{
                    background: creating ? 'var(--navy-mid)' : 'var(--navy-deep)',
                    color: 'var(--off-white)'
                  }}
                >
                  {creating ? (
                    <span className="flex items-center justify-center gap-3">
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Creating...
                    </span>
                  ) : (
                    'Create Job'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
