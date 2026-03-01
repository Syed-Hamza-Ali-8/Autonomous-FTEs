import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import Link from 'next/link';
import Navigation from '../../components/Navigation';

interface Message {
  id: string;
  role: string;
  content: string;
  channel: string;
  timestamp: string;
  metadata: any;
}

interface Ticket {
  id: string;
  customer_id: string;
  customer_name: string;
  customer_email: string;
  subject: string;
  status: string;
  priority: string;
  category: string;
  channel: string;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  escalated_at: string | null;
  escalation_reason: string | null;
  assigned_to: string | null;
}

interface TicketDetail {
  ticket: Ticket;
  messages: Message[];
}

export default function TicketDetailPage() {
  const router = useRouter();
  const { id } = router.query;

  const [ticketDetail, setTicketDetail] = useState<TicketDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [updating, setUpdating] = useState(false);

  // Update form state
  const [newStatus, setNewStatus] = useState('');
  const [newPriority, setNewPriority] = useState('');
  const [assignedTo, setAssignedTo] = useState('');
  const [escalationReason, setEscalationReason] = useState('');

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

  useEffect(() => {
    if (id) {
      fetchTicketDetail();
    }
  }, [id]);

  useEffect(() => {
    if (ticketDetail) {
      setNewStatus(ticketDetail.ticket.status);
      setNewPriority(ticketDetail.ticket.priority);
      setAssignedTo(ticketDetail.ticket.assigned_to || '');
      setEscalationReason(ticketDetail.ticket.escalation_reason || '');
    }
  }, [ticketDetail]);

  const fetchTicketDetail = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/tickets/${id}`);
      if (!response.ok) throw new Error('Failed to fetch ticket');

      const data = await response.json();
      setTicketDetail(data);
      setError('');
    } catch (err) {
      setError('Failed to load ticket. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateTicket = async () => {
    try {
      setUpdating(true);
      const updateData: any = {};

      if (newStatus !== ticketDetail?.ticket.status) {
        updateData.status = newStatus;
      }
      if (newPriority !== ticketDetail?.ticket.priority) {
        updateData.priority = newPriority;
      }
      if (assignedTo !== (ticketDetail?.ticket.assigned_to || '')) {
        updateData.assigned_to = assignedTo || null;
      }
      if (escalationReason !== (ticketDetail?.ticket.escalation_reason || '')) {
        updateData.escalation_reason = escalationReason || null;
      }

      const response = await fetch(`${API_URL}/tickets/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData),
      });

      if (!response.ok) throw new Error('Failed to update ticket');

      // Refresh ticket data
      await fetchTicketDetail();
      alert('Ticket updated successfully!');
    } catch (err) {
      alert('Failed to update ticket. Please try again.');
      console.error(err);
    } finally {
      setUpdating(false);
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

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'customer': return 'bg-blue-50 border-blue-200';
      case 'agent': return 'bg-green-50 border-green-200';
      case 'system': return 'bg-gray-50 border-gray-200';
      default: return 'bg-gray-50 border-gray-200';
    }
  };

  if (loading) {
    return (
      <>
        <Head>
          <title>Loading Ticket - Customer Success FTE</title>
        </Head>
        <div className="min-h-screen bg-gray-50">
          <Navigation />
          <div className="flex items-center justify-center" style={{ minHeight: 'calc(100vh - 64px)' }}>
            <div className="text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-500">Loading ticket...</p>
            </div>
          </div>
        </div>
      </>
    );
  }

  if (error || !ticketDetail) {
    return (
      <>
        <Head>
          <title>Error - Customer Success FTE</title>
        </Head>
        <div className="min-h-screen bg-gray-50">
          <Navigation />
          <div className="flex items-center justify-center" style={{ minHeight: 'calc(100vh - 64px)' }}>
            <div className="text-center">
              <p className="text-red-600 mb-4">{error || 'Ticket not found'}</p>
              <Link href="/tickets" className="text-blue-600 hover:text-blue-800">
                ← Back to Tickets
              </Link>
            </div>
          </div>
        </div>
      </>
    );
  }

  const { ticket, messages } = ticketDetail;

  return (
    <>
      <Head>
        <title>Ticket #{ticket.id.slice(0, 8)} - Customer Success FTE</title>
      </Head>

      <div className="min-h-screen bg-gray-50">
        <Navigation />

        {/* Header */}
        <div className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <Link href="/tickets" className="text-gray-500 hover:text-gray-700 mr-4">
                  ← Back
                </Link>
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">{ticket.subject}</h1>
                  <p className="mt-1 text-sm text-gray-500">
                    Ticket ID: {ticket.id.slice(0, 8)}... • Created {new Date(ticket.created_at).toLocaleString()}
                  </p>
                </div>
              </div>
              <div className="flex space-x-2">
                <span className={`px-3 py-1 inline-flex text-sm font-semibold rounded-full ${getStatusColor(ticket.status)}`}>
                  {ticket.status.replace('_', ' ')}
                </span>
                <span className={`px-3 py-1 inline-flex text-sm font-semibold rounded-full ${getPriorityColor(ticket.priority)}`}>
                  {ticket.priority}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Content - Conversation */}
            <div className="lg:col-span-2">
              <div className="bg-white rounded-lg shadow">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h2 className="text-lg font-semibold text-gray-900">Conversation History</h2>
                  <p className="text-sm text-gray-500">{messages.length} messages</p>
                </div>
                <div className="p-6 space-y-4 max-h-[600px] overflow-y-auto">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`p-4 rounded-lg border-2 ${getRoleColor(message.role)}`}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex items-center">
                          <span className="font-semibold text-gray-900 capitalize">
                            {message.role === 'customer' ? '👤 Customer' : message.role === 'agent' ? '🤖 AI Agent' : '⚙️ System'}
                          </span>
                          <span className="ml-2 text-xs text-gray-500">
                            via {message.channel.replace('_', ' ')}
                          </span>
                        </div>
                        <span className="text-xs text-gray-500">
                          {new Date(message.timestamp).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-gray-700 whitespace-pre-wrap">{message.content}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Sidebar - Ticket Details & Actions */}
            <div className="space-y-6">
              {/* Customer Info */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Customer Information</h3>
                <div className="space-y-3">
                  <div>
                    <label className="text-sm font-medium text-gray-500">Name</label>
                    <p className="text-gray-900">{ticket.customer_name || 'Unknown'}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Email</label>
                    <p className="text-gray-900">{ticket.customer_email}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Channel</label>
                    <p className="text-gray-900 capitalize">{ticket.channel.replace('_', ' ')}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-500">Category</label>
                    <p className="text-gray-900 capitalize">{ticket.category.replace('_', ' ')}</p>
                  </div>
                </div>
              </div>

              {/* Update Ticket */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Update Ticket</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
                    <select
                      value={newStatus}
                      onChange={(e) => setNewStatus(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="open">Open</option>
                      <option value="in_progress">In Progress</option>
                      <option value="resolved">Resolved</option>
                      <option value="escalated">Escalated</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Priority</label>
                    <select
                      value={newPriority}
                      onChange={(e) => setNewPriority(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Assigned To</label>
                    <input
                      type="text"
                      value={assignedTo}
                      onChange={(e) => setAssignedTo(e.target.value)}
                      placeholder="agent@example.com"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  {newStatus === 'escalated' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Escalation Reason</label>
                      <textarea
                        value={escalationReason}
                        onChange={(e) => setEscalationReason(e.target.value)}
                        rows={3}
                        placeholder="Reason for escalation..."
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                    </div>
                  )}

                  <button
                    onClick={handleUpdateTicket}
                    disabled={updating}
                    className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                  >
                    {updating ? 'Updating...' : 'Update Ticket'}
                  </button>
                </div>
              </div>

              {/* Ticket Metadata */}
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Metadata</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Created:</span>
                    <span className="text-gray-900">{new Date(ticket.created_at).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Updated:</span>
                    <span className="text-gray-900">{new Date(ticket.updated_at).toLocaleString()}</span>
                  </div>
                  {ticket.resolved_at && (
                    <div className="flex justify-between">
                      <span className="text-gray-500">Resolved:</span>
                      <span className="text-gray-900">{new Date(ticket.resolved_at).toLocaleString()}</span>
                    </div>
                  )}
                  {ticket.escalated_at && (
                    <div className="flex justify-between">
                      <span className="text-gray-500">Escalated:</span>
                      <span className="text-gray-900">{new Date(ticket.escalated_at).toLocaleString()}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
