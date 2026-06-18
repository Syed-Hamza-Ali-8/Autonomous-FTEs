'use client'

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center">
        <div className="mb-8">
          <h1 className="text-9xl font-bold text-red-600">500</h1>
          <div className="text-6xl mb-4">⚠️</div>
        </div>
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          Something Went Wrong
        </h2>
        <p className="text-gray-600 mb-2">
          An unexpected error occurred while processing your request.
        </p>
        {error.message && (
          <p className="text-sm text-gray-500 mb-8 font-mono bg-gray-100 p-3 rounded">
            {error.message}
          </p>
        )}
        <div className="space-y-3">
          <button
            onClick={reset}
            className="block w-full bg-primary-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-primary-700 transition-colors"
          >
            Try Again
          </button>
          <a
            href="/"
            className="block w-full bg-white text-gray-700 px-6 py-3 rounded-lg font-medium border border-gray-300 hover:bg-gray-50 transition-colors"
          >
            Go to Dashboard
          </a>
        </div>
      </div>
    </div>
  )
}
