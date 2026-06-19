'use client'

import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface User { id: number; email: string; name: string; role: string; company_id: number; company_name: string; company_slug: string }
interface AuthContextType { user: User | null; loading: boolean; login: (email: string, password: string, redirectTo?: string) => Promise<void>; register: (companyName: string, description: string, services: string, email: string, password: string, name: string, redirectTo?: string) => Promise<void>; logout: () => void }

const AuthContext = createContext<AuthContextType | null>(null)

function getToken(): string | null { try { return typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null } catch { return null } }
function setToken(token: string) { try { localStorage.setItem('auth_token', token) } catch {} }
function clearToken() { try { localStorage.removeItem('auth_token') } catch {} }
function parseUser(token: string): User | null {
  try {
    const parts = token.split('.'); if (parts.length !== 3) return null
    const payload = JSON.parse(atob(parts[1]))
    return { id: payload.sub, email: payload.email, name: payload.company_name || payload.email.split('@')[0], role: payload.role, company_id: payload.company_id, company_name: payload.company_name, company_slug: payload.company_slug }
  } catch { return null }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const redirectAfterAuth = useRef<string | null>(null)

  useEffect(() => { const token = getToken(); if (token) { const parsed = parseUser(token); if (parsed) { setUser(parsed) } else { clearToken() } } setLoading(false) }, [])
  useEffect(() => { if (user && redirectAfterAuth.current) { const path = redirectAfterAuth.current; redirectAfterAuth.current = null; window.location.href = path } }, [user])

  const login = useCallback(async (email: string, password: string, redirectTo?: string) => {
    const res = await fetch(`${API_URL}/api/auth/login`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password }) })
    if (!res.ok) { const err = await res.json().catch(() => ({ detail: 'Login failed' })); throw new Error(err.detail) }
    const data = await res.json(); setToken(data.access_token); const parsed = parseUser(data.access_token)
    if (parsed) { setUser(parsed); if (redirectTo) redirectAfterAuth.current = redirectTo }
  }, [])

  const register = useCallback(async (companyName: string, description: string, services: string, email: string, password: string, name: string, redirectTo?: string) => {
    const res = await fetch(`${API_URL}/api/auth/register`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ company_name: companyName, description, services, email, password, name }) })
    if (!res.ok) { const err = await res.json().catch(() => ({ detail: 'Registration failed' })); throw new Error(err.detail) }
    const data = await res.json(); setToken(data.access_token); const parsed = parseUser(data.access_token)
    if (parsed) { setUser(parsed); if (redirectTo) redirectAfterAuth.current = redirectTo }
  }, [])

  const logout = useCallback(() => { clearToken(); setUser(null); if (typeof window !== 'undefined') { window.location.href = '/login' } }, [])

  return (<AuthContext.Provider value={{ user, loading, login, register, logout }}>{children}</AuthContext.Provider>)
}

export function useAuth(): AuthContextType { const ctx = useContext(AuthContext); if (!ctx) throw new Error('useAuth must be used within AuthProvider'); return ctx }
