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
      className="rounded-lg p-6 mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4"
      style={{
        background: 'linear-gradient(135deg, var(--navy-deep) 0%, var(--navy-mid) 100%)',
        color: 'var(--off-white)',
      }}
    >
      <div>
        <p className="font-mono text-xs uppercase tracking-wider opacity-80 mb-1">
          Today&apos;s Talent Digest
        </p>
        <div className="flex flex-wrap items-center gap-4 text-sm md:text-base">
          <span>
            <strong className="text-lg">{newApplications}</strong> new applications
          </span>
          <span className="opacity-50">|</span>
          <span className="flex items-center gap-2">
            <strong className="text-lg">{pendingApprovals}</strong> pending approvals
            {pendingApprovals > 0 && (
              <span className="px-2 py-0.5 text-xs font-bold rounded-full bg-red-500 text-white animate-pulse">
                URGENT
              </span>
            )}
          </span>
          <span className="opacity-50">|</span>
          <span>
            <strong className="text-lg">{shortlistedToday}</strong> shortlisted today
          </span>
        </div>
      </div>
      <Link
        href="/approvals"
        className="inline-flex items-center justify-center px-5 py-2.5 rounded-lg font-medium text-sm transition-opacity hover:opacity-90 shrink-0"
        style={{
          background: 'var(--cyan-electric)',
          color: 'var(--navy-deep)',
        }}
      >
        View Digest
      </Link>
    </div>
  )
}
