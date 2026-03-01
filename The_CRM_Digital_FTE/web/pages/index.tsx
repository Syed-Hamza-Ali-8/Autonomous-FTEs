import Link from 'next/link'
import Head from 'next/head'
import Navigation from '../components/Navigation'

export default function Home() {
  return (
    <>
      <Head>
        <title>Customer Success Digital FTE</title>
      </Head>

      <div className="min-h-screen bg-gray-50">
        <Navigation />

        <div className="bg-gradient-to-br from-blue-50 to-indigo-100 py-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            {/* Header */}
            <div className="text-center mb-16">
              <h1 className="text-5xl font-bold text-gray-900 mb-4">
                Customer Success Digital FTE
              </h1>
              <p className="text-xl text-gray-600">
                24/7 AI-powered customer support across Email, WhatsApp, and Web Form
              </p>
            </div>

            {/* Main Navigation Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
              {/* Dashboard Card */}
              <Link href="/dashboard" className="block bg-white rounded-lg shadow-lg hover:shadow-xl transition-shadow p-8 border-2 border-transparent hover:border-purple-500">
                <div className="text-center">
                  <div className="text-6xl mb-4">📊</div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    Dashboard
                  </h2>
                  <p className="text-gray-600 mb-4">
                    View analytics, metrics, and insights about your customer success operations.
                  </p>
                  <span className="inline-flex items-center px-4 py-2 bg-purple-600 text-white rounded-md font-medium">
                    View Analytics →
                  </span>
                </div>
              </Link>

              {/* Submit Ticket Card */}
              <Link href="/support" className="block bg-white rounded-lg shadow-lg hover:shadow-xl transition-shadow p-8 border-2 border-transparent hover:border-blue-500">
                <div className="text-center">
                  <div className="text-6xl mb-4">📝</div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    Submit a Ticket
                  </h2>
                  <p className="text-gray-600 mb-4">
                    Need help? Submit a support request and our AI agent will assist you immediately.
                  </p>
                  <span className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md font-medium">
                    Get Support →
                  </span>
                </div>
              </Link>

              {/* View Tickets Card */}
              <Link href="/tickets" className="block bg-white rounded-lg shadow-lg hover:shadow-xl transition-shadow p-8 border-2 border-transparent hover:border-green-500">
                <div className="text-center">
                  <div className="text-6xl mb-4">🎫</div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    All Tickets
                  </h2>
                  <p className="text-gray-600 mb-4">
                    View and manage all support tickets. Track status, priority, and conversation history.
                  </p>
                  <span className="inline-flex items-center px-4 py-2 bg-green-600 text-white rounded-md font-medium">
                    View Tickets →
                  </span>
                </div>
              </Link>
            </div>

          {/* Features Section */}
          <div className="mt-16 max-w-6xl mx-auto">
            <h3 className="text-2xl font-bold text-gray-900 text-center mb-8">
              Key Features
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white rounded-lg shadow p-6 text-center">
                <div className="text-4xl mb-3">🤖</div>
                <h4 className="font-semibold text-gray-900 mb-2">AI-Powered</h4>
                <p className="text-sm text-gray-600">
                  Intelligent responses using Groq API with context-aware assistance
                </p>
              </div>
              <div className="bg-white rounded-lg shadow p-6 text-center">
                <div className="text-4xl mb-3">📊</div>
                <h4 className="font-semibold text-gray-900 mb-2">Real-time Tracking</h4>
                <p className="text-sm text-gray-600">
                  Monitor ticket status, priority, and resolution in real-time
                </p>
              </div>
              <div className="bg-white rounded-lg shadow p-6 text-center">
                <div className="text-4xl mb-3">💬</div>
                <h4 className="font-semibold text-gray-900 mb-2">Multi-Channel</h4>
                <p className="text-sm text-gray-600">
                  Support via Email, WhatsApp, and Web Form with unified tracking
                </p>
              </div>
            </div>
          </div>

          {/* Stats Section */}
          <div className="mt-16 bg-white rounded-lg shadow-lg p-8 max-w-6xl mx-auto">
            <h3 className="text-2xl font-bold text-gray-900 text-center mb-6">
              System Status
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 text-center">
              <div>
                <div className="text-3xl font-bold text-blue-600">24/7</div>
                <div className="text-sm text-gray-600 mt-1">Availability</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-green-600">99.8%</div>
                <div className="text-sm text-gray-600 mt-1">Cost Savings</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-purple-600">3</div>
                <div className="text-sm text-gray-600 mt-1">Channels</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-orange-600">Cloud</div>
                <div className="text-sm text-gray-600 mt-1">Neon.tech DB</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    </>
  )
}

