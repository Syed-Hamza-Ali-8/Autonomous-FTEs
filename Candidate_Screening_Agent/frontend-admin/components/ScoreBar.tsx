interface ScoreBarProps {
  totalScore: number
  skillScore?: number
  experienceScore?: number
  projectScore?: number
  communicationScore?: number
  scoreBreakdown?: Record<string, number> | null
}

function scoreColorVar(score: number): string {
  if (score >= 80) return 'var(--sage-green)'
  if (score >= 60) return '#B8860B'
  return 'var(--coral-warm)'
}

function SubBar({ label, score, max = 40 }: { label: string; score: number; max?: number }) {
  const pct = Math.min(100, Math.max(0, (score / max) * 100))
  return (
    <div>
      <div className="flex justify-between mb-2">
        <span className="font-mono text-xs uppercase tracking-wider capitalize"
              style={{ color: 'var(--navy-mid)' }}>
          {label}
        </span>
        <span className="font-mono text-sm" style={{ color: 'var(--navy-deep)' }}>
          {score}/{max}
        </span>
      </div>
      <div className="w-full rounded-full h-2" style={{ background: 'var(--warm-gray)' }}>
        <div
          className="h-2 rounded-full transition-all"
          style={{
            width: `${pct}%`,
            background: scoreColorVar(pct),
          }}
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
      <div className="flex items-center justify-between mb-4">
        <span className="font-mono text-xs uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>
          Total Score
        </span>
        <span className="font-display text-4xl" style={{ color: scoreColorVar(totalScore) }}>
          {totalScore.toFixed(0)}
        </span>
      </div>
      <div className="w-full rounded-full h-3 mb-8" style={{ background: 'var(--warm-gray)' }}>
        <div
          className="h-3 rounded-full transition-all"
          style={{
            width: `${Math.min(100, totalScore)}%`,
            background: scoreColorVar(totalScore),
          }}
        />
      </div>
      <div className="space-y-4">
        <SubBar label="Skill" score={skill} max={40} />
        <SubBar label="Experience" score={experience} max={25} />
        <SubBar label="Project" score={project} max={20} />
        <SubBar label="Communication" score={communication} max={15} />
      </div>
    </div>
  )
}
