import Link from 'next/link'
import { formatDistanceToNow } from 'date-fns'

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

function getScoreBadgeClass(score: number): string {
  if (score >= 80) return 'bg-green-100 text-green-800'
  if (score >= 60) return 'bg-yellow-100 text-yellow-800'
  return 'bg-red-100 text-red-800'
}

const statusColors: Record<string, string> = {
  queued: 'bg-gray-100 text-gray-800',
  screening: 'bg-blue-100 text-blue-800',
  awaiting_reply: 'bg-yellow-100 text-yellow-800',
  pending_approval: 'bg-purple-100 text-purple-800',
  approved: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800',
  manual_review: 'bg-orange-100 text-orange-800',
}

export default function CandidateCard({ candidate, compact = false }: CandidateCardProps) {
  const statusColor = statusColors[candidate.status] || 'bg-gray-100 text-gray-800'

  return (
    <div className={`bg-white shadow rounded-lg hover:shadow-md transition-shadow ${compact ? 'p-4' : 'p-6'}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900">
            {candidate.name || candidate.email}
          </h3>
          <p className="text-sm text-gray-500 mt-1">{candidate.email}</p>
        </div>
        <span
          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColor}`}
        >
          {candidate.status.replace('_', ' ')}
        </span>
      </div>

      <div className={`mt-4 ${compact ? 'space-y-2' : 'grid grid-cols-2 gap-4'}`}>
        {candidate.total_score !== null && candidate.total_score !== undefined && (
          <div>
            <p className="text-xs text-gray-500">Score</p>
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded-full text-sm font-semibold ${getScoreBadgeClass(candidate.total_score)}`}
            >
              {candidate.total_score.toFixed(0)}
            </span>
          </div>
        )}
        {candidate.recommendation && (
          <div>
            <p className="text-xs text-gray-500">Recommendation</p>
            <p className="text-sm font-medium text-gray-900 capitalize">
              {candidate.recommendation}
            </p>
          </div>
        )}
      </div>

      <div className="mt-4 flex items-center justify-between">
        <p className="text-xs text-gray-500">
          Applied {formatDistanceToNow(new Date(candidate.created_at), { addSuffix: true })}
        </p>
        <Link
          href={`/candidates/${candidate.id}`}
          className="text-sm font-medium text-primary-600 hover:text-primary-500"
        >
          View Details →
        </Link>
      </div>
    </div>
  )
}
