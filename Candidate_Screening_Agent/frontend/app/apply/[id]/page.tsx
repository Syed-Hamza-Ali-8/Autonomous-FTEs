'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useEffect } from 'react'
import Modal from '@/components/Modal'

interface Job {
  id: number
  title: string
  description: string
  total_candidates: number
  status?: string
}

export default function JobApplicationPage() {
  const params = useParams()
  const router = useRouter()
  const [job, setJob] = useState<Job | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [modalTitle, setModalTitle] = useState('')
  const [modalMessage, setModalMessage] = useState('')
  const [modalType, setModalType] = useState<'error' | 'success' | 'warning' | 'info'>('info')

  // Form state
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [resume, setResume] = useState<File | null>(null)

  // Helper function to show modal
  const showModal = (title: string, message: string, type: 'error' | 'success' | 'warning' | 'info') => {
    setModalTitle(title)
    setModalMessage(message)
    setModalType(type)
    setIsModalOpen(true)
  }

  useEffect(() => {
    const fetchJob = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/jobs/public/${params.id}`)
        if (!response.ok) throw new Error('Job not found')
        const data = await response.json()
        setJob(data)
      } catch (err: any) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    if (params.id) {
      fetchJob()
    }
  }, [params.id])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    setError(null)

    if (!resume) {
      showModal('Resume Required', 'Please upload your resume to continue with your application.', 'warning')
      setSubmitting(false)
      return
    }

    if (resume.type !== 'application/pdf') {
      showModal('Invalid File Type', 'Resume must be a PDF file. Please upload a PDF version of your resume.', 'error')
      setSubmitting(false)
      return
    }

    // Check file size (5MB limit)
    const maxSize = 5 * 1024 * 1024 // 5MB in bytes
    if (resume.size > maxSize) {
      showModal('File Too Large', 'Resume must be smaller than 5MB. Please compress your PDF or use a smaller file.', 'error')
      setSubmitting(false)
      return
    }

    try {
      const formData = new FormData()
      formData.append('name', name)
      formData.append('email', email)
      formData.append('resume', resume)
      formData.append('job_id', params.id as string)

      const response = await fetch('http://localhost:8000/api/applications/submit', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to submit application')
      }

      setSuccess(true)
      setName('')
      setEmail('')
      setResume(null)
    } catch (err: any) {
      showModal('Application Error', err.message, 'error')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="relative w-16 h-16 mx-auto mb-6">
            <div className="absolute inset-0 rounded-full border-2 animate-spin"
                 style={{
                   borderColor: 'var(--cyan-electric)',
                   borderTopColor: 'transparent'
                 }} />
          </div>
          <p className="font-mono text-sm uppercase tracking-wider"
             style={{ color: 'var(--navy-mid)' }}>
            Loading position details...
          </p>
        </div>
      </div>
    )
  }

  if (error && !job) {
    return (
      <div className="max-w-2xl mx-auto px-6 py-16">
        <div className="border-l-4 p-8"
             style={{
               borderColor: 'var(--coral-warm)',
               background: 'rgba(255, 107, 107, 0.05)'
             }}>
          <h2 className="font-display text-2xl mb-3"
              style={{ color: 'var(--navy-deep)' }}>
            Position Not Found
          </h2>
          <p style={{ color: 'var(--navy-mid)' }}>{error}</p>
        </div>
      </div>
    )
  }

  if (success) {
    return (
      <div className="max-w-2xl mx-auto px-6 py-16">
        <div className="text-center py-12"
             style={{ background: 'white', borderRadius: '12px', boxShadow: 'var(--shadow-soft)' }}>
          <div className="inline-flex items-center justify-center w-16 h-16 mb-6 rounded-full"
               style={{ background: 'rgba(78, 205, 196, 0.1)' }}>
            <svg className="w-8 h-8" style={{ color: 'var(--sage-green)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="font-display text-3xl mb-3"
              style={{ color: 'var(--navy-deep)' }}>
            Application Received
          </h2>
          <p className="text-lg mb-8"
             style={{ color: 'var(--navy-light)' }}>
            Thank you for applying, <span className="font-medium">{name}</span>
          </p>
          <p className="text-sm mb-10 max-w-md mx-auto"
             style={{ color: 'var(--navy-mid)' }}>
            Your application for <span className="font-medium">{job?.title}</span> has been submitted. We review all applications carefully and will be in touch if there's a fit.
          </p>
          <button
            onClick={() => router.push('/jobs')}
            className="px-8 py-3 font-medium transition-all hover:opacity-90"
            style={{
              background: 'var(--navy-deep)',
              color: 'var(--off-white)',
              borderRadius: '8px'
            }}
          >
            View More Jobs
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-16">
      {/* Modal for errors and warnings */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={modalTitle}
        message={modalMessage}
        type={modalType}
      />

      {/* Header */}
      <div className="mb-12">
        <div className="font-mono text-xs uppercase tracking-wider mb-4"
             style={{ color: 'var(--navy-mid)' }}>
          Application
        </div>
        <h1 className="font-display text-5xl mb-4"
            style={{ color: 'var(--navy-deep)' }}>
          {job?.title}
        </h1>
        <p className="text-xl leading-relaxed max-w-2xl"
           style={{ color: 'var(--navy-light)' }}>
          {job?.description}
        </p>
      </div>

      {/* Divider */}
      <div className="h-px mb-12" style={{ background: 'var(--warm-gray)' }} />

      {/* Paused State */}
      {job?.status === 'paused' ? (
        <div className="text-center py-16">
          <div className="inline-flex items-center justify-center w-16 h-16 mb-6 rounded-full"
               style={{ background: 'rgba(220, 38, 38, 0.08)' }}>
            <svg className="w-8 h-8" style={{ color: '#DC2626' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="font-display text-3xl mb-3" style={{ color: 'var(--navy-deep)' }}>Applications Paused</h2>
          <p className="text-lg mb-8 max-w-md mx-auto" style={{ color: 'var(--navy-light)' }}>
            This position is temporarily not accepting applications. Please check back later.
          </p>
          <button onClick={() => router.push('/jobs')} className="px-8 py-3 font-medium transition-all hover:opacity-90"
            style={{ background: 'var(--navy-deep)', color: 'var(--off-white)', borderRadius: '8px' }}>
            Browse Other Jobs
          </button>
        </div>
      ) : (

      {/* Application Form */}
      <div className="grid lg:grid-cols-12 gap-12">
        {/* Form - Main Column */}
        <div className="lg:col-span-7">
          <form onSubmit={handleSubmit} className="space-y-8">
            {/* Name */}
            <div>
              <label htmlFor="name"
                     className="block font-medium mb-3 text-sm uppercase tracking-wider"
                     style={{ color: 'var(--navy-mid)' }}>
                Full Name *
              </label>
              <input
                type="text"
                id="name"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-6 py-4 border-2 font-medium transition-all focus:outline-none"
                style={{
                  borderColor: 'var(--warm-gray)',
                  color: 'var(--navy-deep)',
                  background: 'white'
                }}
                onFocus={(e) => e.target.style.borderColor = 'var(--cyan-electric)'}
                onBlur={(e) => e.target.style.borderColor = 'var(--warm-gray)'}
                placeholder="John Doe"
              />
            </div>

            {/* Email */}
            <div>
              <label htmlFor="email"
                     className="block font-medium mb-3 text-sm uppercase tracking-wider"
                     style={{ color: 'var(--navy-mid)' }}>
                Email Address *
              </label>
              <input
                type="email"
                id="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-6 py-4 border-2 font-medium transition-all focus:outline-none"
                style={{
                  borderColor: 'var(--warm-gray)',
                  color: 'var(--navy-deep)',
                  background: 'white'
                }}
                onFocus={(e) => e.target.style.borderColor = 'var(--cyan-electric)'}
                onBlur={(e) => e.target.style.borderColor = 'var(--warm-gray)'}
                placeholder="john.doe@example.com"
              />
            </div>

            {/* Resume Upload */}
            <div>
              <label htmlFor="resume"
                     className="block font-medium mb-3 text-sm uppercase tracking-wider"
                     style={{ color: 'var(--navy-mid)' }}>
                Resume / CV (PDF only) *
              </label>
              <div className="border-2 border-dashed p-12 text-center transition-all hover:border-opacity-100 cursor-pointer"
                   style={{
                     borderColor: resume ? 'var(--sage-green)' : 'var(--warm-gray)',
                     background: resume ? 'rgba(78, 205, 196, 0.03)' : 'white'
                   }}>
                <div className="space-y-4">
                  <svg className="mx-auto h-12 w-12"
                       style={{ color: resume ? 'var(--sage-green)' : 'var(--navy-mid)' }}
                       stroke="currentColor"
                       fill="none"
                       viewBox="0 0 48 48">
                    <path
                      d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                      strokeWidth={2}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                  <div>
                    <label
                      htmlFor="resume"
                      className="relative cursor-pointer font-medium transition-opacity hover:opacity-70"
                      style={{ color: 'var(--cyan-electric)' }}
                    >
                      <span>Choose file</span>
                      <input
                        id="resume"
                        name="resume"
                        type="file"
                        accept=".pdf"
                        required
                        onChange={(e) => setResume(e.target.files?.[0] || null)}
                        className="sr-only"
                      />
                    </label>
                    <span className="ml-2" style={{ color: 'var(--navy-mid)' }}>
                      or drag and drop
                    </span>
                  </div>
                  <p className="font-mono text-xs uppercase tracking-wider"
                     style={{ color: 'var(--navy-mid)' }}>
                    PDF up to 5MB
                  </p>
                  {resume && (
                    <div className="pt-4 border-t"
                         style={{ borderColor: 'var(--warm-gray)' }}>
                      <p className="font-medium"
                         style={{ color: 'var(--sage-green)' }}>
                        ✓ {resume.name}
                      </p>
                      <p className="font-mono text-xs mt-1"
                         style={{ color: 'var(--navy-mid)' }}>
                        {(resume.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Submit Buttons */}
            <div className="flex gap-4 pt-4">
              <button
                type="button"
                onClick={() => router.push('/jobs')}
                className="flex-1 px-8 py-4 font-medium border-2 transition-all hover:opacity-70"
                style={{
                  borderColor: 'var(--navy-deep)',
                  color: 'var(--navy-deep)',
                  background: 'transparent'
                }}
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="flex-1 px-8 py-4 font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90"
                style={{
                  background: submitting ? 'var(--navy-mid)' : 'var(--navy-deep)',
                  color: 'var(--off-white)'
                }}
              >
                {submitting ? (
                  <span className="flex items-center justify-center gap-3">
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Submitting...
                  </span>
                ) : (
                  'Submit Application'
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Info Panel - Side Column */}
        <div className="lg:col-span-5">
          <div className="sticky top-8 space-y-6">
            {/* Application Tips */}
            <div className="p-6 rounded-xl" style={{ background: 'var(--warm-gray)', opacity: 0.3 }}>
              <h3 className="font-medium text-sm uppercase tracking-wider mb-4"
                  style={{ color: 'var(--navy-mid)' }}>
                Application Tips
              </h3>
              <ul className="space-y-3 text-sm" style={{ color: 'var(--navy-light)' }}>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 flex-shrink-0 mt-0.5" style={{ color: 'var(--sage-green)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Ensure your resume is up to date with your latest experience</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 flex-shrink-0 mt-0.5" style={{ color: 'var(--sage-green)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Tailor your resume to highlight relevant skills</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 flex-shrink-0 mt-0.5" style={{ color: 'var(--sage-green)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>Use a professional email address</span>
                </li>
              </ul>
            </div>

            {/* Required Documents */}
            <div className="p-6 rounded-xl" style={{ background: 'white', border: '1px solid var(--warm-gray)' }}>
              <h3 className="font-medium text-sm uppercase tracking-wider mb-4"
                  style={{ color: 'var(--navy-mid)' }}>
                Required Documents
              </h3>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg flex items-center justify-center"
                     style={{ background: 'rgba(0, 229, 255, 0.1)' }}>
                  <svg className="w-5 h-5" style={{ color: 'var(--cyan-electric)' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div>
                  <p className="font-medium" style={{ color: 'var(--navy-deep)' }}>Resume / CV</p>
                  <p className="text-sm" style={{ color: 'var(--navy-mid)' }}>PDF format only</p>
                </div>
              </div>
            </div>

            {/* Need Help */}
            <div className="p-6 rounded-xl" style={{ background: 'white', border: '1px solid var(--warm-gray)' }}>
              <h3 className="font-medium text-sm uppercase tracking-wider mb-3"
                  style={{ color: 'var(--navy-mid)' }}>
                Need Help?
              </h3>
              <p className="text-sm" style={{ color: 'var(--navy-light)' }}>
                If you have questions about this position, please contact the hiring team directly through the job posting.
              </p>
            </div>
          </div>
        </div>
      </div>
      )}
    </div>
  )
}
