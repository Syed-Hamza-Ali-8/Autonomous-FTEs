import CandidateCard from './CandidateCard'

interface Candidate {
  id: number
  name: string
  email: string
  status: string
  total_score?: number
  recommendation?: string
  created_at: string
}

interface PipelineBoardProps {
  candidates: Candidate[]
  pendingApprovalCandidateIds?: number[]
}

const COLUMNS = [
  {
    key: 'applied',
    title: 'Applied',
    statuses: ['queued', 'scoring', 'scored'],
  },
  {
    key: 'screening',
    title: 'Screening',
    statuses: ['questions_sent', 'awaiting_reply', 'replied'],
  },
  {
    key: 'shortlisted',
    title: 'Shortlisted',
    statuses: ['shortlisted', 'hired'],
  },
  {
    key: 'pending_approval',
    title: 'Pending Approval',
    statuses: [] as string[],
  },
] as const

export default function PipelineBoard({ candidates, pendingApprovalCandidateIds = [] }: PipelineBoardProps) {
  const pendingIds = new Set(pendingApprovalCandidateIds)

  const getColumnCandidates = (columnKey: string, statuses: readonly string[]) => {
    if (columnKey === 'pending_approval') {
      return candidates.filter((c) => pendingIds.has(c.id))
    }
    return candidates.filter(
      (c) => statuses.includes(c.status) && !pendingIds.has(c.id)
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
      {COLUMNS.map((column) => {
        const columnCandidates = getColumnCandidates(column.key, column.statuses)
        return (
          <div
            key={column.key}
            className="bg-gray-50 rounded-lg p-4 min-h-[320px] flex flex-col"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900">{column.title}</h3>
              <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-white text-sm font-medium text-gray-700 shadow-sm">
                {columnCandidates.length}
              </span>
            </div>
            <div className="flex-1 space-y-3 overflow-y-auto max-h-[480px] pr-1">
              {columnCandidates.length === 0 ? (
                <p className="text-sm text-gray-400 text-center py-8">No candidates</p>
              ) : (
                columnCandidates.map((candidate) => (
                  <CandidateCard key={candidate.id} candidate={candidate} compact />
                ))
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
