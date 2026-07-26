'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { getJob, updateJob, updateJobStatus } from '@/lib/api'

export default function JobDetailPage() {
  const params = useParams()
  const router = useRouter()
  const [job, setJob] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [isEditOpen, setIsEditOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [editForm, setEditForm] = useState({ title: '', description: '', rubric_path: '', hiring_manager_email: '' })

  const [statusLoading, setStatusLoading] = useState(false)

  const fetchJob = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await getJob(Number(params.id))
      setJob(data)
    } catch (err: any) {
      setError(err.message || 'Failed to load job details')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { if (params.id) fetchJob() }, [params.id])

  const openEdit = () => {
    setEditForm({
      title: job.title || '',
      description: job.description || '',
      rubric_path: job.rubric_path || '',
      hiring_manager_email: job.hiring_manager_email || '',
    })
    setSaveError(null)
    setIsEditOpen(true)
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setSaveError(null)
    try {
      await updateJob(job.id, {
        title: editForm.title,
        description: editForm.description,
        rubric_path: editForm.rubric_path,
        hiring_manager_email: editForm.hiring_manager_email || undefined,
      })
      setIsEditOpen(false)
      await fetchJob()
    } catch (err: any) {
      setSaveError(err.response?.data?.detail || err.message || 'Failed to update')
    } finally {
      setSaving(false)
    }
  }

  const handleStatusChange = async (newStatus: string) => {
    if (statusLoading) return
    const labels: Record<string, string> = { open: 'reopen', closed: 'close', paused: 'pause' }
    if (!confirm(`Are you sure you want to ${labels[newStatus]} this job?`)) return
    setStatusLoading(true)
    try {
      await updateJobStatus(job.id, newStatus)
      await fetchJob()
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to update status')
    } finally {
      setStatusLoading(false)
    }
  }

  const statusColors: Record<string, { bg: string; text: string; border: string }> = {
    open: { bg: 'rgba(78, 205, 196, 0.1)', text: 'var(--sage-green)', border: 'var(--sage-green)' },
    paused: { bg: 'rgba(255, 107, 107, 0.08)', text: 'var(--coral-warm)', border: 'var(--coral-warm)' },
    closed: { bg: 'rgba(197, 201, 208, 0.2)', text: 'var(--navy-mid)', border: 'var(--cool-gray)' },
  }

  const candidateStatusColors: Record<string, string> = {
    queued: 'bg-gray-100 text-gray-800',
    scoring: 'bg-blue-100 text-blue-800',
    scored: 'bg-indigo-100 text-indigo-800',
    questions_sent: 'bg-purple-100 text-purple-800',
    awaiting_reply: 'bg-yellow-100 text-yellow-800',
    replied: 'bg-cyan-100 text-cyan-800',
    shortlisted: 'bg-green-100 text-green-800',
    rejected: 'bg-red-100 text-red-800',
    hired: 'bg-emerald-100 text-emerald-800',
    manual_review: 'bg-orange-100 text-orange-800',
  }

  if (loading) return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="text-center">
        <div className="relative w-16 h-16 mx-auto mb-6">
          <div className="absolute inset-0 rounded-full border-2 animate-spin" style={{ borderColor: 'var(--cyan-electric)', borderTopColor: 'transparent' }} />
        </div>
        <p className="font-mono text-sm uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>Loading job...</p>
      </div>
    </div>
  )

  if (error) return (
    <div className="max-w-2xl mx-auto mt-12">
      <div className="border-l-4 p-8" style={{ borderColor: 'var(--coral-warm)', background: 'rgba(255, 107, 107, 0.05)' }}>
        <h3 className="font-display text-xl mb-2" style={{ color: 'var(--navy-deep)' }}>Error</h3>
        <p className="mb-4" style={{ color: 'var(--navy-mid)' }}>{error}</p>
        <button onClick={() => router.push('/jobs')} className="px-6 py-2 font-medium text-sm" style={{ background: 'var(--coral-warm)', color: 'white' }}>Back to Jobs</button>
      </div>
    </div>
  )

  if (!job) return null

  const sc = statusColors[job.status] || statusColors.open

  return (
    <div className="max-w-7xl mx-auto px-6 lg:px-12 py-16">
      {/* Back button */}
      <button onClick={() => router.push('/jobs')} className="flex items-center gap-2 mb-8 font-mono text-sm uppercase tracking-wider transition-colors hover:opacity-70" style={{ color: 'var(--navy-mid)' }}>
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
        Back to Jobs
      </button>

      {/* Header */}
      <div className="mb-12">
        <div className="flex items-start justify-between gap-6 mb-6">
          <div className="flex-1">
            <div className="flex items-center gap-4 mb-4">
              <h1 className="font-display text-4xl lg:text-5xl" style={{ color: 'var(--navy-deep)' }}>{job.title}</h1>
              <span className="px-3 py-1 font-mono text-xs uppercase tracking-wider border" style={{ background: sc.bg, color: sc.text, borderColor: sc.border }}>
                {job.status}
              </span>
            </div>
            <p className="text-lg" style={{ color: 'var(--navy-light)' }}>
              Posted {new Date(job.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
            </p>
          </div>

          {/* Action buttons */}
          <div className="hidden lg:flex items-center gap-3">
            <button onClick={openEdit} className="px-5 py-2.5 font-medium text-sm transition-all hover:opacity-90" style={{ background: 'var(--cyan-electric)', color: 'var(--navy-deep)' }}>
              Edit Job
            </button>
            {job.status === 'open' && (
              <>
                <button onClick={() => handleStatusChange('paused')} disabled={statusLoading} className="px-5 py-2.5 font-medium text-sm border transition-all hover:opacity-70 disabled:opacity-50" style={{ borderColor: 'var(--coral-warm)', color: 'var(--coral-warm)' }}>
                  Pause
                </button>
                <button onClick={() => handleStatusChange('closed')} disabled={statusLoading} className="px-5 py-2.5 font-medium text-sm border transition-all hover:opacity-70 disabled:opacity-50" style={{ borderColor: 'var(--navy-mid)', color: 'var(--navy-mid)' }}>
                  Close
                </button>
              </>
            )}
            {job.status === 'paused' && (
              <>
                <button onClick={() => handleStatusChange('open')} disabled={statusLoading} className="px-5 py-2.5 font-medium text-sm transition-all hover:opacity-90 disabled:opacity-50" style={{ background: 'var(--sage-green)', color: 'white' }}>
                  Reopen
                </button>
                <button onClick={() => handleStatusChange('closed')} disabled={statusLoading} className="px-5 py-2.5 font-medium text-sm border transition-all hover:opacity-70 disabled:opacity-50" style={{ borderColor: 'var(--navy-mid)', color: 'var(--navy-mid)' }}>
                  Close
                </button>
              </>
            )}
            {job.status === 'closed' && (
              <button onClick={() => handleStatusChange('open')} disabled={statusLoading} className="px-5 py-2.5 font-medium text-sm transition-all hover:opacity-90 disabled:opacity-50" style={{ background: 'var(--sage-green)', color: 'white' }}>
                Reopen
              </button>
            )}
          </div>
        </div>
        <div className="h-px" style={{ background: 'var(--warm-gray)' }} />
      </div>

      {/* Mobile action buttons */}
      <div className="lg:hidden flex flex-wrap gap-3 mb-8">
        <button onClick={openEdit} className="px-5 py-2.5 font-medium text-sm" style={{ background: 'var(--cyan-electric)', color: 'var(--navy-deep)' }}>Edit Job</button>
        {job.status === 'open' && (
          <>
            <button onClick={() => handleStatusChange('paused')} disabled={statusLoading} className="px-5 py-2.5 font-medium text-sm border disabled:opacity-50" style={{ borderColor: 'var(--coral-warm)', color: 'var(--coral-warm)' }}>Pause</button>
            <button onClick={() => handleStatusChange('closed')} disabled={statusLoading} className="px-5 py-2.5 font-medium text-sm border disabled:opacity-50" style={{ borderColor: 'var(--navy-mid)', color: 'var(--navy-mid)' }}>Close</button>
          </>
        )}
        {job.status === 'paused' && (
          <>
            <button onClick={() => handleStatusChange('open')} disabled={statusLoading} className="px-5 py-2.5 font-medium text-sm disabled:opacity-50" style={{ background: 'var(--sage-green)', color: 'white' }}>Reopen</button>
            <button onClick={() => handleStatusChange('closed')} disabled={statusLoading} className="px-5 py-2.5 font-medium text-sm border disabled:opacity-50" style={{ borderColor: 'var(--navy-mid)', color: 'var(--navy-mid)' }}>Close</button>
          </>
        )}
        {job.status === 'closed' && (
          <button onClick={() => handleStatusChange('open')} disabled={statusLoading} className="px-5 py-2.5 font-medium text-sm disabled:opacity-50" style={{ background: 'var(--sage-green)', color: 'white' }}>Reopen</button>
        )}
      </div>

      {/* Job Information */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">
        <div className="lg:col-span-2 border-l-4 p-8" style={{ borderColor: 'var(--cyan-electric)', background: 'white', boxShadow: 'var(--shadow-soft)' }}>
          <h2 className="font-display text-2xl mb-6" style={{ color: 'var(--navy-deep)' }}>Job Description</h2>
          <p className="text-base leading-relaxed whitespace-pre-wrap" style={{ color: 'var(--navy-light)' }}>{job.description}</p>
        </div>
        <div className="space-y-6">
          <div className="p-6" style={{ background: 'white', boxShadow: 'var(--shadow-soft)' }}>
            <div className="font-mono text-xs uppercase tracking-wider mb-3" style={{ color: 'var(--navy-mid)' }}>Rubric</div>
            <div className="font-mono text-sm" style={{ color: 'var(--navy-deep)' }}>{job.rubric_path}</div>
          </div>
          <div className="p-6" style={{ background: 'white', boxShadow: 'var(--shadow-soft)' }}>
            <div className="font-mono text-xs uppercase tracking-wider mb-3" style={{ color: 'var(--navy-mid)' }}>Hiring Manager</div>
            <div className="text-sm" style={{ color: 'var(--navy-deep)' }}>{job.hiring_manager_email || 'Not specified'}</div>
          </div>
          <div className="p-6" style={{ background: 'white', boxShadow: 'var(--shadow-soft)' }}>
            <div className="font-mono text-xs uppercase tracking-wider mb-3" style={{ color: 'var(--navy-mid)' }}>Candidates</div>
            <div className="font-display text-4xl" style={{ color: 'var(--cyan-electric)' }}>{job.total_candidates || 0}</div>
          </div>
        </div>
      </div>

      {/* Candidates Table */}
      <div style={{ background: 'white', boxShadow: 'var(--shadow-soft)' }}>
        <div className="px-8 py-6 border-b" style={{ borderColor: 'var(--warm-gray)' }}>
          <h2 className="font-display text-2xl" style={{ color: 'var(--navy-deep)' }}>
            Candidates ({job.candidates?.length || 0})
          </h2>
        </div>
        <div className="p-8">
          {!job.candidates || job.candidates.length === 0 ? (
            <div className="text-center py-16">
              <div className="w-16 h-16 mx-auto mb-6 flex items-center justify-center" style={{ background: 'var(--off-white)' }}>
                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" style={{ color: 'var(--cool-gray)' }}>
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <h3 className="font-display text-xl mb-2" style={{ color: 'var(--navy-deep)' }}>No candidates yet</h3>
              <p className="text-sm" style={{ color: 'var(--navy-mid)' }}>Candidates will appear here once they apply.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead>
                  <tr style={{ borderBottom: '2px solid var(--warm-gray)' }}>
                    <th className="px-6 py-3 text-left font-mono text-xs uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>Candidate</th>
                    <th className="px-6 py-3 text-left font-mono text-xs uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>Status</th>
                    <th className="px-6 py-3 text-left font-mono text-xs uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>Score</th>
                    <th className="px-6 py-3 text-left font-mono text-xs uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>Recommendation</th>
                    <th className="px-6 py-3 text-left font-mono text-xs uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>Applied</th>
                  </tr>
                </thead>
                <tbody>
                  {job.candidates.map((c: any) => (
                    <tr key={c.id} onClick={() => router.push(`/candidates/${c.id}`)} className="cursor-pointer transition-colors" style={{ borderBottom: '1px solid var(--warm-gray)' }}
                      onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--off-white)')}
                      onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}>
                      <td className="px-6 py-4">
                        <div className="text-sm font-medium" style={{ color: 'var(--navy-deep)' }}>{c.name}</div>
                        <div className="text-xs" style={{ color: 'var(--navy-mid)' }}>{c.email}</div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-0.5 inline-flex text-xs font-semibold rounded-full ${candidateStatusColors[c.status] || 'bg-gray-100 text-gray-800'}`}>
                          {c.status.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm" style={{ color: 'var(--navy-deep)' }}>{c.total_score ? `${c.total_score}/100` : 'N/A'}</td>
                      <td className="px-6 py-4 text-sm" style={{ color: 'var(--navy-deep)' }}>{c.recommendation || 'N/A'}</td>
                      <td className="px-6 py-4 text-sm" style={{ color: 'var(--navy-mid)' }}>{c.created_at ? new Date(c.created_at).toLocaleDateString() : 'N/A'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Edit Modal */}
      {isEditOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: 'rgba(10, 22, 40, 0.8)' }} onClick={() => setIsEditOpen(false)}>
          <div className="max-w-2xl w-full border-l-4 p-8" style={{ borderColor: 'var(--cyan-electric)', background: 'white', maxHeight: '90vh', overflowY: 'auto' }} onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between mb-8">
              <h2 className="font-display text-3xl" style={{ color: 'var(--navy-deep)' }}>Edit Job</h2>
              <button onClick={() => setIsEditOpen(false)} className="p-2" style={{ color: 'var(--navy-mid)' }}>✕</button>
            </div>
            {saveError && (
              <div className="mb-6 p-4 border-l-4" style={{ borderColor: 'var(--coral-warm)' }}>
                <p style={{ color: 'var(--coral-warm)' }}>{saveError}</p>
              </div>
            )}
            <form onSubmit={handleSave} className="space-y-6">
              <div>
                <label className="block font-medium mb-3 text-sm uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>Job Title *</label>
                <input type="text" required value={editForm.title} onChange={(e) => setEditForm({ ...editForm, title: e.target.value })} className="w-full px-4 py-3 border-2" style={{ borderColor: 'var(--warm-gray)' }} />
              </div>
              <div>
                <label className="block font-medium mb-3 text-sm uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>Description *</label>
                <textarea required rows={6} value={editForm.description} onChange={(e) => setEditForm({ ...editForm, description: e.target.value })} className="w-full px-4 py-3 border-2" style={{ borderColor: 'var(--warm-gray)' }} />
              </div>
              <div>
                <label className="block font-medium mb-3 text-sm uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>Rubric Path *</label>
                <input type="text" required value={editForm.rubric_path} onChange={(e) => setEditForm({ ...editForm, rubric_path: e.target.value })} className="w-full px-4 py-3 border-2" style={{ borderColor: 'var(--warm-gray)' }} />
              </div>
              <div>
                <label className="block font-medium mb-3 text-sm uppercase tracking-wider" style={{ color: 'var(--navy-mid)' }}>Hiring Manager Email</label>
                <input type="email" value={editForm.hiring_manager_email} onChange={(e) => setEditForm({ ...editForm, hiring_manager_email: e.target.value })} className="w-full px-4 py-3 border-2" style={{ borderColor: 'var(--warm-gray)' }} />
              </div>
              <div className="flex gap-4 pt-4">
                <button type="button" onClick={() => setIsEditOpen(false)} className="flex-1 px-6 py-3 font-medium border-2" style={{ borderColor: 'var(--navy-deep)', color: 'var(--navy-deep)' }}>Cancel</button>
                <button type="submit" disabled={saving} className="flex-1 px-6 py-3 font-medium disabled:opacity-50" style={{ background: saving ? 'var(--navy-mid)' : 'var(--navy-deep)', color: 'var(--off-white)' }}>
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
