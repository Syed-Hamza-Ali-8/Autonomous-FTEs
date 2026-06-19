import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { AuthProvider } from '@/components/AuthProvider'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Candidate Screening — AI-Powered Hiring',
  description: 'AI-powered candidate screening platform with human-in-the-loop approval',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (<html lang="en"><body className={inter.className}><AuthProvider>{children}</AuthProvider></body></html>)
}
