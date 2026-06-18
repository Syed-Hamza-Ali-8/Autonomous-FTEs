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
            className="rounded-2xl p-6 min-h-[320px] flex flex-col"
            style={{
              background: 'var(--off-white)',
              border: '1px solid var(--warm-gray)',
            }}
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-display text-lg" style={{ color: 'var(--navy-deep)' }}>
                {column.title}
              </h3>
              <div className="w-7 h-7 rounded-full flex items-center justify-center font-mono text-xs"
                   style={{
                     background: columnCandidates.length > 0 ? 'rgba(0, 229, 255, 0.15)' : 'var(--warm-gray)',
                     color: columnCandidates.length > 0 ? 'var(--cyan-electric)' : 'var(--navy-mid)',
                   }}>
                {columnCandidates.length}
              </div>
            </div>
            <div className="flex-1 space-y-3 overflow-y-auto max-h-[480px] pr-1">
              {columnCandidates.length === 0 ? (
                <div className="text-center py-12">
                  <p className="font-mono text-xs uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>
                    None
                  </p>
                </div>
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
