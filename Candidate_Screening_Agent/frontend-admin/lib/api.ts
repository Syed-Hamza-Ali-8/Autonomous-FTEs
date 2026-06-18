import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 second timeout
  maxRedirects: 5, // Follow up to 5 redirects
})

// Candidates
export const getCandidates = async (jobId?: number) => {
  try {
    const url = jobId ? `/api/candidates?job_id=${jobId}` : '/api/candidates'
    const response = await api.get(url)
    return response.data
  } catch (error) {
    console.error('Error fetching candidates:', error)
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

// Approvals
export const getPendingApprovals = async () => {
  try {
    const response = await api.get('/api/approvals/pending')
    return response.data
  } catch (error) {
    console.error('Error fetching approvals:', error)
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
  } catch (error) {
    console.error('Error fetching jobs:', error)
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

export default api
