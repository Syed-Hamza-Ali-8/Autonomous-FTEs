'use client'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div className="min-h-screen flex items-center justify-center px-6"
         style={{ background: 'var(--off-white)' }}>
      <div className="max-w-md w-full text-center">
        <div className="mb-8">
          <div className="font-display text-9xl leading-none"
               style={{ color: 'var(--coral-warm)' }}>
            500
          </div>
          <div className="w-16 h-16 mx-auto my-6 rounded-full flex items-center justify-center"
               style={{ background: 'rgba(255, 107, 107, 0.1)' }}>
            <span className="text-3xl">⚠️</span>
          </div>
        </div>
        <h2 className="font-display text-3xl mb-4" style={{ color: 'var(--navy-deep)' }}>
          Something Went Wrong
        </h2>
        <p className="mb-2" style={{ color: 'var(--navy-light)' }}>
          An unexpected error occurred.
        </p>
        {error.message && (
          <div className="text-sm font-mono p-4 rounded-lg mb-8 text-left"
               style={{
                 background: 'rgba(255, 107, 107, 0.05)',
                 border: '1px solid rgba(255, 107, 107, 0.2)',
                 color: 'var(--coral-warm)',
               }}>
            {error.message}
          </div>
        )}
        <div className="space-y-4">
          <button
            onClick={reset}
            className="block w-full px-6 py-3 rounded-lg font-medium transition-all hover:opacity-90"
            style={{ background: 'var(--navy-deep)', color: 'var(--off-white)' }}
          >
            Try Again
          </button>
          <a
            href="/"
            className="block w-full px-6 py-3 rounded-lg font-medium transition-all hover:opacity-90"
            style={{
              background: 'var(--off-white)',
              color: 'var(--navy-deep)',
              border: '1px solid var(--warm-gray)',
            }}
          >
            Go to Dashboard
          </a>
        </div>
      </div>
    </div>
  )
}
