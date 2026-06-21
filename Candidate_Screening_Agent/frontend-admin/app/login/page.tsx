'use client'

import { useState, FormEvent } from 'react'
import { useAuth } from '@/components/AuthProvider'
import Link from 'next/link'

export default function LoginPage() {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault(); setError(''); setSubmitting(true)
    try {
      await login(email, password)
      window.location.href = '/'
    } catch (err: any) {
      setError(err.message || 'Login failed')
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6" style={{ background: 'var(--off-white)' }}>
      <div className="w-full max-w-md">
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4" style={{ background: 'var(--navy-deep)' }}><span className="font-display text-3xl" style={{ color: 'var(--off-white)' }}>C</span></div>
          <h1 className="font-display text-3xl" style={{ color: 'var(--navy-deep)' }}>Sign In</h1>
          <p className="mt-2" style={{ color: 'var(--navy-light)' }}>Access your hiring dashboard</p>
        </div>
        <form onSubmit={handleSubmit} className="p-8 rounded-2xl" style={{ background: 'white', border: '1px solid var(--warm-gray)' }}>
          {error && (<div className="mb-6 p-4 rounded-lg border-l-4" style={{ borderColor: 'var(--coral-warm)', background: 'rgba(255, 107, 107, 0.05)' }}><p className="text-sm" style={{ color: 'var(--coral-warm)' }}>{error}</p></div>)}
          <div className="mb-5"><label className="block font-mono text-xs uppercase tracking-wider mb-2" style={{ color: 'var(--navy-mid)' }}>Email</label><input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required className="w-full px-4 py-3 rounded-lg text-sm" style={{ background: 'var(--off-white)', border: '1px solid var(--warm-gray)', color: 'var(--navy-deep)' }} placeholder="admin@demo.com" /></div>
          <div className="mb-8"><label className="block font-mono text-xs uppercase tracking-wider mb-2" style={{ color: 'var(--navy-mid)' }}>Password</label><input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required className="w-full px-4 py-3 rounded-lg text-sm" style={{ background: 'var(--off-white)', border: '1px solid var(--warm-gray)', color: 'var(--navy-deep)' }} placeholder="demo1234" /></div>
          <button type="submit" disabled={submitting} className="w-full px-6 py-3 rounded-lg font-medium transition-all hover:opacity-90 disabled:opacity-50" style={{ background: 'var(--navy-deep)', color: 'var(--off-white)' }}>{submitting ? 'Signing in...' : 'Sign In'}</button>
        </form>
        <p className="text-center mt-6" style={{ color: 'var(--navy-light)' }}>Don't have an account?{' '}<Link href="/register" className="font-medium hover:opacity-70" style={{ color: 'var(--cyan-electric)' }}>Create one</Link></p>
      </div>
    </div>
  )
}
