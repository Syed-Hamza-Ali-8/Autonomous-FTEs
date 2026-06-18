import Link from 'next/link'

interface DigestBannerProps {
  newApplications: number
  pendingApprovals: number
  shortlistedToday: number
}

export default function DigestBanner({
  newApplications,
  pendingApprovals,
  shortlistedToday,
}: DigestBannerProps) {
  return (
    <div
      className="rounded-2xl p-8 mb-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6"
      style={{
        background: 'linear-gradient(135deg, var(--navy-deep) 0%, var(--navy-mid) 100%)',
        color: 'var(--off-white)',
      }}
    >
      <div>
        <p className="font-mono text-xs uppercase tracking-wider opacity-60 mb-2">
          Today&apos;s Talent Digest
        </p>
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center"
                 style={{ background: 'rgba(0, 229, 255, 0.15)' }}>
              <span className="font-display text-xl" style={{ color: 'var(--cyan-electric)' }}>
                {newApplications}
              </span>
            </div>
            <span className="text-sm opacity-80">new applications</span>
          </div>
          <div className="opacity-20">|</div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center"
                 style={{ background: pendingApprovals > 0 ? 'rgba(255, 107, 107, 0.2)' : 'rgba(255,255,255,0.05)' }}>
              <span className="font-display text-xl"
                    style={{ color: pendingApprovals > 0 ? 'var(--coral-warm)' : 'var(--off-white)', opacity: 0.8 }}>
                {pendingApprovals}
              </span>
            </div>
            <span className="text-sm opacity-80 flex items-center gap-2">
              pending approvals
              {pendingApprovals > 0 && (
                <span className="px-2 py-0.5 text-xs font-bold rounded-full animate-pulse"
                      style={{ background: 'var(--coral-warm)', color: 'white' }}>
                  URGENT
                </span>
              )}
            </span>
          </div>
          <div className="opacity-20">|</div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg flex items-center justify-center"
                 style={{ background: 'rgba(78, 205, 196, 0.15)' }}>
              <span className="font-display text-xl" style={{ color: 'var(--sage-green)' }}>
                {shortlistedToday}
              </span>
            </div>
            <span className="text-sm opacity-80">shortlisted</span>
          </div>
        </div>
      </div>
      <Link
        href="/approvals"
        className="inline-flex items-center justify-center px-6 py-3 rounded-lg font-medium text-sm transition-all hover:opacity-90 shrink-0"
        style={{
          background: 'var(--cyan-electric)',
          color: 'var(--navy-deep)',
        }}
      >
        View Digest →
      </Link>
    </div>
  )
}
