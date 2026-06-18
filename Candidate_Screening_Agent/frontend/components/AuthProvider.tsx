'use client'

import { SessionProvider, useSession } from 'next-auth/react'
import { createContext, useContext, type ReactNode } from 'react'

interface AuthContextValue {
  session: any
  status: 'loading' | 'authenticated' | 'unauthenticated'
}

const AuthContext = createContext<AuthContextValue>({ session: null, status: 'loading' })

export function useAuth(): AuthContextValue {
  return useContext(AuthContext)
}

function InnerProvider({ children }: { children: ReactNode }) {
  const { data: session, status } = useSession()
  return (
    <AuthContext.Provider value={{ session, status }}>
      {children}
    </AuthContext.Provider>
  )
}

export default function AuthProvider({ children }: { children: ReactNode }) {
  return (
    <SessionProvider refetchOnWindowFocus={false} refetchInterval={0}>
      <InnerProvider>{children}</InnerProvider>
    </SessionProvider>
  )
}
