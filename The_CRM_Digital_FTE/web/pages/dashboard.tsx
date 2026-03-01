import { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import Navigation from '../components/Navigation';

interface TicketStats {
  total: number;
  open: number;
  in_progress: number;
  resolved: number;
  escalated: number;
  by_priority: { [key: string]: number };
  by_channel: { [key: string]: number };
  by_category: { [key: string]: number };
}

interface RecentTicket {
  id: string;
  subject: string;
  status: string;
  priority: string;
  created_at: string;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<TicketStats | null>(null);
  const [recentTickets, setRecentTickets] = useState<RecentTicket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);

      // Fetch stats
      const statsResponse = await fetch(`${API_URL}/tickets/stats`);
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStats(statsData);
      }

      // Fetch recent tickets
      const ticketsResponse = await fetch(`${API_URL}/tickets?limit=5`);
      if (ticketsResponse.ok) {
        const ticketsData = await ticketsResponse.json();
        setRecentTickets(ticketsData);
      }

      setError('');
    } catch (err) {
      setError('Failed to load dashboard data. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open': return 'bg-blue-100 text-blue-800';
      case 'in_progress': return 'bg-yellow-100 text-yellow-800';
      case 'resolved': return 'bg-green-100 text-green-800';
      case 'escalated': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <>
        <Head>
          <title>Dashboard - Customer Success FTE</title>
        </Head>
        <div className="min-h-screen bg-gray-50">
          <Navigation />
          <div className="flex items-center justify-center" style={{ minHeight: 'calc(100vh - 64px)' }}>
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-2 text-gray-500">Loading dashboard...</p>
            </div>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Head>
        <title>Dashboard - Customer Success FTE</title>
      </Head>

      <div className="min-h-screen bg-gray-50">
        <Navigation />

        {/* Page Header */}
        <div className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="flex justify-between items-center">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
                <p className="mt-1 text-sm text-gray-500">Overview of your customer success operations</p>
              </div>
              <Link href="/support" className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700">
                Submit New Ticket
              </Link>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-600">{error}</p>
            </div>
          )}

          {/* Key Metrics */}
          {stats && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
                <div className="bg-white rounded-lg shadow p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm font-medium text-gray-500">Total Tickets</div>
                      <div className="mt-2 text-3xl font-bold text-gray-900">{stats.total}</div>
                    </div>
                    <div className="text-4xl">📊</div>
                  </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm font-medium text-gray-500">Open</div>
                      <div className="mt-2 text-3xl font-bold text-blue-600">{stats.open}</div>
                    </div>
                    <div className="text-4xl">🔵</div>
                  </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm font-medium text-gray-500">In Progress</div>
                      <div className="mt-2 text-3xl font-bold text-yellow-600">{stats.in_progress}</div>
                    </div>
                    <div className="text-4xl">⚡</div>
                  </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm font-medium text-gray-500">Resolved</div>
                      <div className="mt-2 text-3xl font-bold text-green-600">{stats.resolved}</div>
                    </div>
                    <div className="text-4xl">✅</div>
                  </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm font-medium text-gray-500">Escalated</div>
                      <div className="mt-2 text-3xl font-bold text-red-600">{stats.escalated}</div>
                    </div>
                    <div className="text-4xl">🚨</div>
                  </div>
                </div>
              </div>

              {/* Charts Section */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                {/* Priority Distribution */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">By Priority</h2>
                  <div className="space-y-3">
                    {Object.entries(stats.by_priority).map(([priority, count]) => (
                      <div key={priority}>
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-sm font-medium text-gray-700 capitalize">{priority}</span>
                          <span className="text-sm font-semibold text-gray-900">{count}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              priority === 'high' ? 'bg-red-500' :
                              priority === 'medium' ? 'bg-yellow-500' :
                              'bg-green-500'
                            }`}
                            style={{ width: `${stats.total > 0 ? (count / stats.total) * 100 : 0}%` }}
                          ></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Channel Distribution */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">By Channel</h2>
                  <div className="space-y-3">
                    {Object.entries(stats.by_channel).map(([channel, count]) => (
                      <div key={channel}>
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-sm font-medium text-gray-700 capitalize">
                            {channel === 'email' ? '📧 Email' :
                             channel === 'whatsapp' ? '💬 WhatsApp' :
                             channel === 'web_form' ? '🌐 Web Form' :
                             channel.replace('_', ' ')}
                          </span>
                          <span className="text-sm font-semibold text-gray-900">{count}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-500 h-2 rounded-full"
                            style={{ width: `${stats.total > 0 ? (count / stats.total) * 100 : 0}%` }}
                          ></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Category Distribution */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">By Category</h2>
                  <div className="space-y-3">
                    {Object.entries(stats.by_category).map(([category, count]) => (
                      <div key={category}>
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-sm font-medium text-gray-700 capitalize">{category.replace('_', ' ')}</span>
                          <span className="text-sm font-semibold text-gray-900">{count}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-purple-500 h-2 rounded-full"
                            style={{ width: `${stats.total > 0 ? (count / stats.total) * 100 : 0}%` }}
                          ></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </>
          )}

          {/* Recent Tickets */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Recent Tickets</h2>
                <p className="text-sm text-gray-500">Latest customer inquiries</p>
              </div>
              <Link href="/tickets" className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                View All →
              </Link>
            </div>
            <div className="p-6">
              {recentTickets.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  No tickets yet. Submit your first ticket to get started!
                </div>
              ) : (
                <div className="space-y-4">
                  {recentTickets.map((ticket) => (
                    <Link
                      key={ticket.id}
                      href={`/tickets/${ticket.id}`}
                      className="block p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:shadow-md transition-all"
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h3 className="text-sm font-semibold text-gray-900">{ticket.subject}</h3>
                          <p className="text-xs text-gray-500 mt-1">
                            {new Date(ticket.created_at).toLocaleString()}
                          </p>
                        </div>
                        <div className="flex space-x-2 ml-4">
                          <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(ticket.status)}`}>
                            {ticket.status.replace('_', ' ')}
                          </span>
                          <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getPriorityColor(ticket.priority)}`}>
                            {ticket.priority}
                          </span>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
            <Link href="/support" className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-center">
                <div className="text-4xl mr-4">✉️</div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Submit Ticket</h3>
                  <p className="text-sm text-gray-500">Create a new support request</p>
                </div>
              </div>
            </Link>

            <Link href="/tickets" className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-center">
                <div className="text-4xl mr-4">🎫</div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">View All Tickets</h3>
                  <p className="text-sm text-gray-500">Browse and manage tickets</p>
                </div>
              </div>
            </Link>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="text-4xl mr-4">📈</div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Performance</h3>
                  <p className="text-sm text-gray-500">
                    {stats ? `${stats.resolved} resolved tickets` : 'Loading...'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
