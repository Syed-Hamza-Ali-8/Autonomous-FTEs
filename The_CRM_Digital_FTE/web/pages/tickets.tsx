import { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import Navigation from '../components/Navigation';

interface Ticket {
  id: string;
  customer_name: string;
  customer_email: string;
  subject: string;
  status: string;
  priority: string;
  category: string;
  channel: string;
  created_at: string;
  updated_at: string;
}

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

export default function TicketsPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [stats, setStats] = useState<TicketStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [channelFilter, setChannelFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

  useEffect(() => {
    fetchTickets();
    fetchStats();
  }, [statusFilter, priorityFilter, channelFilter]);

  const fetchTickets = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);
      if (priorityFilter) params.append('priority', priorityFilter);
      if (channelFilter) params.append('channel', channelFilter);

      const response = await fetch(`${API_URL}/tickets?${params.toString()}`);
      if (!response.ok) throw new Error('Failed to fetch tickets');

      const data = await response.json();
      setTickets(data);
      setError('');
    } catch (err) {
      setError('Failed to load tickets. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_URL}/tickets/stats`);
      if (!response.ok) throw new Error('Failed to fetch stats');

      const data = await response.json();
      setStats(data);
    } catch (err) {
      console.error('Failed to load stats:', err);
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

  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case 'email': return '📧';
      case 'whatsapp': return '💬';
      case 'web_form': return '🌐';
      default: return '📝';
    }
  };

  const filteredTickets = tickets.filter(ticket => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      ticket.subject.toLowerCase().includes(query) ||
      ticket.customer_name?.toLowerCase().includes(query) ||
      ticket.customer_email?.toLowerCase().includes(query)
    );
  });

  return (
    <>
      <Head>
        <title>Tickets Dashboard - Customer Success FTE</title>
      </Head>

      <div className="min-h-screen bg-gray-50">
        <Navigation />

        {/* Page Header */}
        <div className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="flex justify-between items-center">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Tickets Dashboard</h1>
                <p className="mt-1 text-sm text-gray-500">Manage and track customer support tickets</p>
              </div>
              <Link href="/support" className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700">
                Submit New Ticket
              </Link>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Stats Cards */}
          {stats && (
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-8">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-sm font-medium text-gray-500">Total</div>
                <div className="mt-2 text-3xl font-bold text-gray-900">{stats.total}</div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-sm font-medium text-gray-500">Open</div>
                <div className="mt-2 text-3xl font-bold text-blue-600">{stats.open}</div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-sm font-medium text-gray-500">In Progress</div>
                <div className="mt-2 text-3xl font-bold text-yellow-600">{stats.in_progress}</div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-sm font-medium text-gray-500">Resolved</div>
                <div className="mt-2 text-3xl font-bold text-green-600">{stats.resolved}</div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="text-sm font-medium text-gray-500">Escalated</div>
                <div className="mt-2 text-3xl font-bold text-red-600">{stats.escalated}</div>
              </div>
            </div>
          )}

          {/* Filters and Search */}
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
                <input
                  type="text"
                  placeholder="Search tickets..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All Statuses</option>
                  <option value="open">Open</option>
                  <option value="in_progress">In Progress</option>
                  <option value="resolved">Resolved</option>
                  <option value="escalated">Escalated</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Priority</label>
                <select
                  value={priorityFilter}
                  onChange={(e) => setPriorityFilter(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All Priorities</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Channel</label>
                <select
                  value={channelFilter}
                  onChange={(e) => setChannelFilter(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All Channels</option>
                  <option value="email">Email</option>
                  <option value="whatsapp">WhatsApp</option>
                  <option value="web_form">Web Form</option>
                </select>
              </div>
            </div>
          </div>

          {/* Tickets Table */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            {loading ? (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <p className="mt-2 text-gray-500">Loading tickets...</p>
              </div>
            ) : error ? (
              <div className="text-center py-12">
                <p className="text-red-600">{error}</p>
                <button
                  onClick={fetchTickets}
                  className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Retry
                </button>
              </div>
            ) : filteredTickets.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-500">No tickets found</p>
              </div>
            ) : (
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Ticket
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Customer
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Priority
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Channel
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredTickets.map((ticket) => (
                    <tr key={ticket.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <div className="text-sm font-medium text-gray-900">{ticket.subject}</div>
                        <div className="text-sm text-gray-500">{ticket.category}</div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900">{ticket.customer_name || 'Unknown'}</div>
                        <div className="text-sm text-gray-500">{ticket.customer_email}</div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(ticket.status)}`}>
                          {ticket.status.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getPriorityColor(ticket.priority)}`}>
                          {ticket.priority}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        <span className="mr-1">{getChannelIcon(ticket.channel)}</span>
                        {ticket.channel.replace('_', ' ')}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {new Date(ticket.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 text-sm font-medium">
                        <Link href={`/tickets/${ticket.id}`} className="text-blue-600 hover:text-blue-900">
                          View
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
