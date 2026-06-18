interface ScoreBarProps {
  totalScore: number
  skillScore?: number
  experienceScore?: number
  projectScore?: number
  communicationScore?: number
  scoreBreakdown?: Record<string, number> | null
}

function scoreColor(score: number): string {
  if (score >= 80) return 'bg-green-500'
  if (score >= 60) return 'bg-yellow-500'
  return 'bg-red-500'
}

function SubBar({ label, score, max = 40 }: { label: string; score: number; max?: number }) {
  const pct = Math.min(100, Math.max(0, (score / max) * 100))
  return (
    <div>
      <div className="flex justify-between text-xs text-gray-600 mb-1">
        <span className="capitalize">{label}</span>
        <span>{score}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`h-2 rounded-full ${scoreColor(pct)}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

export default function ScoreBar({
  totalScore,
  skillScore,
  experienceScore,
  projectScore,
  communicationScore,
  scoreBreakdown,
}: ScoreBarProps) {
  const breakdown = scoreBreakdown ?? {}
  const skill = skillScore ?? breakdown.skill_score ?? breakdown.skill ?? 0
  const experience = experienceScore ?? breakdown.experience_score ?? breakdown.experience ?? 0
  const project = projectScore ?? breakdown.project_score ?? breakdown.project ?? 0
  const communication =
    communicationScore ?? breakdown.communication_score ?? breakdown.communication ?? 0

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-700">Total Score</span>
        <span className="text-2xl font-bold text-gray-900">{totalScore.toFixed(0)}/100</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-4 mb-6">
        <div
          className={`h-4 rounded-full transition-all ${scoreColor(totalScore)}`}
          style={{ width: `${Math.min(100, totalScore)}%` }}
        />
      </div>
      <div className="space-y-3">
        <SubBar label="Skill" score={skill} max={40} />
        <SubBar label="Experience" score={experience} max={25} />
        <SubBar label="Project" score={project} max={20} />
        <SubBar label="Communication" score={communication} max={15} />
      </div>
    </div>
  )
}
