import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center px-6"
         style={{ background: 'var(--off-white)' }}>
      <div className="max-w-md w-full text-center">
        <div className="mb-8">
          <div className="font-display text-9xl leading-none"
               style={{ color: 'var(--navy-deep)' }}>
            404
          </div>
          <div className="w-16 h-16 mx-auto my-6 rounded-full flex items-center justify-center"
               style={{ background: 'rgba(0, 229, 255, 0.1)' }}>
            <span className="text-3xl">🔍</span>
          </div>
        </div>
        <h2 className="font-display text-3xl mb-4" style={{ color: 'var(--navy-deep)' }}>
          Page Not Found
        </h2>
        <p className="mb-10 text-lg" style={{ color: 'var(--navy-light)' }}>
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="space-y-4">
          <Link
            href="/"
            className="block w-full px-6 py-3 rounded-lg font-medium transition-all hover:opacity-90"
            style={{ background: 'var(--navy-deep)', color: 'var(--off-white)' }}
          >
            Go to Dashboard
          </Link>
          <Link
            href="/jobs"
            className="block w-full px-6 py-3 rounded-lg font-medium transition-all hover:opacity-90"
            style={{
              background: 'var(--off-white)',
              color: 'var(--navy-deep)',
              border: '1px solid var(--warm-gray)',
            }}
          >
            View Jobs
          </Link>
        </div>
      </div>
    </div>
  )
}
