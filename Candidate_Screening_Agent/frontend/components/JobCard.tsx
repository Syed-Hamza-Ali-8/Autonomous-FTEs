import Link from 'next/link'
import { format } from 'date-fns'

interface JobCardProps {
  job: {
    id: number
    title: string
    description: string
    rubric_path: string
    hiring_manager_email?: string
    company_name?: string
    status?: string
    total_candidates: number
    candidate_count?: number
    status_counts: Record<string, number>
    created_at: string
  }
  isAdmin?: boolean
}

export default function JobCard({ job, isAdmin = false }: JobCardProps) {
  const statusCounts = job.status_counts || {}
  const pendingApprovals = statusCounts['pending_approval'] || 0
  const approved = statusCounts['approved'] || 0
  const rejected = statusCounts['rejected'] || 0
  const totalCandidates = job.total_candidates || job.candidate_count || 0
  const inProgress = totalCandidates - approved - rejected

  return (
    <div className="group relative hover-lift border-l-4 p-8"
         style={{
           borderColor: 'var(--cyan-electric)',
           background: 'white',
           boxShadow: 'var(--shadow-soft)'
         }}>
      {/* Header */}
      <div className="mb-6">
        <h3 className="font-display text-2xl mb-2 transition-colors group-hover:opacity-80"
            style={{ color: 'var(--navy-deep)' }}>
          {job.title}
        </h3>
        {!isAdmin && job.company_name && (
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full mb-3"
               style={{ background: 'var(--off-white)', border: '1px solid var(--warm-gray)' }}>
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"
                 style={{ color: 'var(--navy-mid)' }}>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            <span className="font-mono text-xs" style={{ color: 'var(--navy-mid)' }}>{job.company_name}</span>
          </div>
        )}
        <p className="text-base leading-relaxed line-clamp-2"
           style={{ color: 'var(--navy-light)' }}>
          {job.description}
        </p>
      </div>

      {/* Stats Grid - Only show for admins */}
      {isAdmin && (
        <div className="grid grid-cols-4 gap-3 mb-6">
          <div className="text-center">
            <div className="font-display text-3xl mb-1"
                 style={{ color: 'var(--navy-deep)' }}>
              {totalCandidates}
            </div>
            <div className="font-mono text-xs uppercase tracking-wider"
                 style={{ color: 'var(--navy-mid)' }}>
              Total
            </div>
          </div>
          <div className="text-center">
            <div className="font-display text-3xl mb-1"
                 style={{ color: 'var(--coral-warm)' }}>
              {pendingApprovals}
            </div>
            <div className="font-mono text-xs uppercase tracking-wider"
                 style={{ color: 'var(--navy-mid)' }}>
              Pending
            </div>
          </div>
          <div className="text-center">
            <div className="font-display text-3xl mb-1"
                 style={{ color: 'var(--sage-green)' }}>
              {approved}
            </div>
            <div className="font-mono text-xs uppercase tracking-wider"
                 style={{ color: 'var(--navy-mid)' }}>
              Approved
            </div>
          </div>
          <div className="text-center">
            <div className="font-display text-3xl mb-1"
                 style={{ color: 'var(--cyan-electric)' }}>
              {inProgress}
            </div>
            <div className="font-mono text-xs uppercase tracking-wider"
                 style={{ color: 'var(--navy-mid)' }}>
              Active
            </div>
          </div>
        </div>
      )}

      {/* Status Breakdown - Only show for admins */}
      {isAdmin && Object.keys(statusCounts).length > 0 && (
        <div className="mb-6 pb-6 border-b"
             style={{ borderColor: 'var(--warm-gray)' }}>
          <div className="flex flex-wrap gap-2">
            {Object.entries(statusCounts).map(([status, count]) => (
              <span
                key={status}
                className="inline-flex items-center gap-2 px-3 py-1 font-mono text-xs"
                style={{
                  background: 'var(--off-white)',
                  color: 'var(--navy-mid)',
                  border: '1px solid var(--warm-gray)'
                }}
              >
                <span className="w-1.5 h-1.5 rounded-full"
                      style={{ background: 'var(--cyan-electric)' }} />
                {status.replace('_', ' ')}: {count}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Meta Info */}
      <div className="mb-6 space-y-2">
        <div className="flex items-center gap-2 font-mono text-xs"
             style={{ color: 'var(--navy-mid)' }}>
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Posted on {format(new Date(job.created_at), 'MMM dd, yyyy \'at\' h:mm a')}
        </div>
        {isAdmin && job.hiring_manager_email && (
          <div className="flex items-center gap-2 font-mono text-xs"
               style={{ color: 'var(--navy-mid)' }}>
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            {job.hiring_manager_email}
          </div>
        )}
      </div>

      {/* Actions - Different for Admin vs Candidate */}
      <div className="flex gap-3">
        {isAdmin ? (
          <>
            <Link
              href={`/candidates?job_id=${job.id}`}
              className="flex-1 px-6 py-3 font-medium text-center transition-all hover:opacity-90"
              style={{
                background: 'var(--navy-deep)',
                color: 'var(--off-white)'
              }}
            >
              View Candidates
            </Link>
            <Link
              href={`/jobs/${job.id}`}
              className="flex-1 px-6 py-3 font-medium text-center border transition-all hover:opacity-70"
              style={{
                borderColor: 'var(--navy-deep)',
                color: 'var(--navy-deep)',
                background: 'transparent'
              }}
            >
              Manage
            </Link>
          </>
        ) : (
          <>
            {job.status === 'paused' ? (
              <div className="flex-1 px-6 py-3 font-medium text-center"
                style={{ background: 'rgba(220, 38, 38, 0.06)', color: '#DC2626', border: '1px solid rgba(220, 38, 38, 0.2)' }}>
                Applications Paused
              </div>
            ) : (
              <Link
                href={`/apply/${job.id}`}
                className="flex-1 px-6 py-3 font-medium text-center transition-all hover:opacity-90"
                style={{
                  background: 'var(--navy-deep)',
                  color: 'var(--off-white)'
                }}
              >
                Apply Now
              </Link>
            )}
            <Link
              href={`/jobs/${job.id}`}
              className="flex-1 px-6 py-3 font-medium text-center border transition-all hover:opacity-70"
              style={{
                borderColor: 'var(--navy-deep)',
                color: 'var(--navy-deep)',
                background: 'transparent'
              }}
            >
              Details
            </Link>
          </>
        )}
      </div>
    </div>
  )
}
