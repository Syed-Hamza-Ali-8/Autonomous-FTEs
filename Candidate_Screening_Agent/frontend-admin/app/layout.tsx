import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import AdminNav from '@/components/AdminNav'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Candidate Screening — Admin Panel',
  description: 'Admin dashboard for candidate screening',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen" style={{ background: 'var(--off-white)' }}>
          <AdminNav />
          <main>
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}
