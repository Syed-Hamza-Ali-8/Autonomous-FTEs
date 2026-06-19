'use client'

import { useState, FormEvent } from 'react'
import { useAuth } from '@/components/AuthProvider'
import Link from 'next/link'

export default function RegisterPage() {
  const { register } = useAuth()
  const [companyName, setCompanyName] = useState('')
  const [description, setDescription] = useState('')
  const [services, setServices] = useState('')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault(); setError('')
    if (password.length < 8) { setError('Password must be at least 8 characters'); return }
    setLoading(true)
    try { await register(companyName, description, services, email, password, name, '/') } catch (err: any) { setError(err.message || 'Registration failed'); setLoading(false) }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-12" style={{ background: 'var(--off-white)' }}>
      <div className="w-full max-w-lg">
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4" style={{ background: 'var(--navy-deep)' }}><span className="font-display text-3xl" style={{ color: 'var(--off-white)' }}>C</span></div>
          <h1 className="font-display text-3xl" style={{ color: 'var(--navy-deep)' }}>Create Account</h1>
          <p className="mt-2" style={{ color: 'var(--navy-light)' }}>Start screening candidates with AI</p>
        </div>
        <form onSubmit={handleSubmit} className="p-8 rounded-2xl" style={{ background: 'white', border: '1px solid var(--warm-gray)' }}>
          {error && (<div className="mb-6 p-4 rounded-lg border-l-4" style={{ borderColor: 'var(--coral-warm)', background: 'rgba(255, 107, 107, 0.05)' }}><p className="text-sm" style={{ color: 'var(--coral-warm)' }}>{error}</p></div>)}
          <div className="mb-5"><label className="block font-mono text-xs uppercase tracking-wider mb-2" style={{ color: 'var(--navy-mid)' }}>Company Name</label><input type="text" value={companyName} onChange={(e) => setCompanyName(e.target.value)} required className="w-full px-4 py-3 rounded-lg text-sm" style={{ background: 'var(--off-white)', border: '1px solid var(--warm-gray)', color: 'var(--navy-deep)' }} placeholder="Acme Corp" /></div>
          <div className="mb-5"><label className="block font-mono text-xs uppercase tracking-wider mb-2" style={{ color: 'var(--navy-mid)' }}>Company Description</label><textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} className="w-full px-4 py-3 rounded-lg text-sm resize-none" style={{ background: 'var(--off-white)', border: '1px solid var(--warm-gray)', color: 'var(--navy-deep)' }} placeholder="Tell us about your company..." /></div>
          <div className="mb-5"><label className="block font-mono text-xs uppercase tracking-wider mb-2" style={{ color: 'var(--navy-mid)' }}>Services / Industry</label><input type="text" value={services} onChange={(e) => setServices(e.target.value)} className="w-full px-4 py-3 rounded-lg text-sm" style={{ background: 'var(--off-white)', border: '1px solid var(--warm-gray)', color: 'var(--navy-deep)' }} placeholder="e.g., Software Development, AI, Consulting" /></div>
          <div className="mb-5"><label className="block font-mono text-xs uppercase tracking-wider mb-2" style={{ color: 'var(--navy-mid)' }}>Your Name</label><input type="text" value={name} onChange={(e) => setName(e.target.value)} required className="w-full px-4 py-3 rounded-lg text-sm" style={{ background: 'var(--off-white)', border: '1px solid var(--warm-gray)', color: 'var(--navy-deep)' }} placeholder="John Doe" /></div>
          <div className="mb-5"><label className="block font-mono text-xs uppercase tracking-wider mb-2" style={{ color: 'var(--navy-mid)' }}>Email</label><input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required className="w-full px-4 py-3 rounded-lg text-sm" style={{ background: 'var(--off-white)', border: '1px solid var(--warm-gray)', color: 'var(--navy-deep)' }} placeholder="you@company.com" /></div>
          <div className="mb-8"><label className="block font-mono text-xs uppercase tracking-wider mb-2" style={{ color: 'var(--navy-mid)' }}>Password</label><input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required className="w-full px-4 py-3 rounded-lg text-sm" style={{ background: 'var(--off-white)', border: '1px solid var(--warm-gray)', color: 'var(--navy-deep)' }} placeholder="Min 8 characters" /></div>
          <button type="submit" disabled={loading} className="w-full px-6 py-3 rounded-lg font-medium transition-all hover:opacity-90 disabled:opacity-50" style={{ background: 'var(--navy-deep)', color: 'var(--off-white)' }}>{loading ? 'Creating account...' : 'Create Account'}</button>
        </form>
        <p className="text-center mt-6" style={{ color: 'var(--navy-light)' }}>Already have an account?{' '}<Link href="/login" className="font-medium hover:opacity-70" style={{ color: 'var(--cyan-electric)' }}>Sign in</Link></p>
      </div>
    </div>
  )
}
