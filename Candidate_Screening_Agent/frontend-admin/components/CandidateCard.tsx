import Link from 'next/link'
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

interface CandidateCardProps {
  candidate: {
    id: number
    name: string
    email: string
    status: string
    total_score?: number
    recommendation?: string
    created_at: string
  }
  compact?: boolean
}

function getScoreColor(score: number): string {
  if (score >= 80) return 'var(--sage-green)'
  if (score >= 60) return '#B8860B'
  return 'var(--coral-warm)'
}

function getScoreBgTint(score: number): string {
  if (score >= 80) return 'rgba(78, 205, 196, 0.1)'
  if (score >= 60) return 'rgba(255, 191, 0, 0.1)'
  return 'rgba(255, 107, 107, 0.1)'
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

export default function CandidateCard({ candidate, compact = false }: CandidateCardProps) {
  const statusColor = statusColors[candidate.status] || 'bg-gray-100 text-gray-800'

  return (
    <div className="rounded-xl p-6 hover:shadow-md transition-shadow cursor-pointer"
         style={{
           background: 'var(--off-white)',
           border: '1px solid var(--warm-gray)',
         }}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="font-display text-lg" style={{ color: 'var(--navy-deep)' }}>
            {candidate.name || candidate.email}
          </h3>
          <p className="font-mono text-sm mt-1" style={{ color: 'var(--navy-mid)' }}>
            {candidate.email}
          </p>
        </div>
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColor}`}>
          {candidate.status.replace('_', ' ')}
        </span>
      </div>

      <div className="mt-5 flex items-center gap-4">
        {candidate.total_score !== null && candidate.total_score !== undefined && (
          <div className="px-3 py-1.5 rounded-lg" style={{ background: getScoreBgTint(candidate.total_score) }}>
            <p className="font-mono text-xs" style={{ color: 'var(--navy-mid)' }}>Score</p>
            <span className="font-display text-lg" style={{ color: getScoreColor(candidate.total_score) }}>
              {candidate.total_score.toFixed(0)}
            </span>
          </div>
        )}
        {candidate.recommendation && (
          <div>
            <p className="font-mono text-xs uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>
              AI
            </p>
            <p className="font-medium capitalize" style={{ color: 'var(--navy-deep)' }}>
              {candidate.recommendation}
            </p>
          </div>
        )}
      </div>

      <div className="mt-5 pt-4 flex items-center justify-between"
           style={{ borderTop: '1px solid var(--warm-gray)' }}>
        <p className="font-mono text-xs uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>
          Applied {formatAppliedDate(candidate.created_at)}
        </p>
        <Link
          href={`/candidates/${candidate.id}`}
          className="font-mono text-xs uppercase tracking-wider transition-colors hover:opacity-70"
          style={{ color: 'var(--navy-light)' }}
        >
          View →
        </Link>
      </div>
    </div>
  )
}
