import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 60000,
  maxRedirects: 5,
})

// Inject JWT token from localStorage
api.interceptors.request.use((config) => {
  try {
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
  } catch {}
  return config
})

// Redirect to login on 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      try { localStorage.removeItem('auth_token') } catch {}
      if (typeof window !== 'undefined') window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Candidates
export const getCandidates = async (jobId?: number) => {
  try {
    const url = jobId ? `/api/candidates?job_id=${jobId}` : '/api/candidates'
    const response = await api.get(url)
    return response.data
  } catch {
    return []
  }
}

export const getCandidate = async (id: number) => {
  const response = await api.get(`/api/candidates/${id}`)
  return response.data
}

export const getCandidatesByStatus = async (status: string) => {
  const response = await api.get(`/api/candidates/by-status/${status}`)
  return response.data
}

export const getCandidateBrief = async (id: number) => {
  const response = await api.get(`/api/candidates/${id}/brief`)
  return response.data
}

export const getCandidateInterview = async (id: number) => {
  const response = await api.get(`/api/candidates/${id}/interview`)
  return response.data
}

// Approvals
export const getPendingApprovals = async () => {
  try {
    const response = await api.get('/api/approvals/pending')
    return response.data
  } catch {
    return []
  }
}

export const approveCandidate = async (approvalId: number) => {
  const response = await api.post(`/api/approvals/${approvalId}/approve`)
  return response.data
}

export const rejectCandidate = async (approvalId: number) => {
  const response = await api.post(`/api/approvals/${approvalId}/reject`)
  return response.data
}

// Jobs
export const getJobs = async () => {
  try {
    const response = await api.get('/api/jobs/')
    return response.data
  } catch {
    return []
  }
}

export const getJob = async (id: number) => {
  const response = await api.get(`/api/jobs/${id}`)
  return response.data
}

export const createJob = async (jobData: {
  title: string
  description: string
  rubric_path: string
  hiring_manager_email?: string
}) => {
  const response = await api.post('/api/jobs/', jobData)
  return response.data
}

export const updateJob = async (id: number, jobData: {
  title?: string
  description?: string
  rubric_path?: string
  hiring_manager_email?: string
}) => {
  const response = await api.put(`/api/jobs/${id}`, jobData)
  return response.data
}

export const updateJobStatus = async (id: number, status: string) => {
  const response = await api.patch(`/api/jobs/${id}/status`, { status })
  return response.data
}

export default api
