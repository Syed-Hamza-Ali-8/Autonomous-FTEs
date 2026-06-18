import { NextAuthOptions } from 'next-auth'
import CredentialsProvider from 'next-auth/providers/credentials'

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        email: { label: "Email", type: "email", placeholder: "admin@company.com" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        // For demo purposes, using hardcoded admin credentials
        // In production, this should check against a database
        if (
          credentials?.email === 'admin@company.com' &&
          credentials?.password === 'admin123'
        ) {
          return {
            id: '1',
            email: 'admin@company.com',
            name: 'Admin User',
            role: 'admin'
          }
        }

        // You can add more users here or check against a database
        return null
      }
    })
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.role = (user as any).role
      }
      return token
    },
    async session({ session, token }) {
      if (session?.user) {
        (session.user as any).role = token.role
      }
      return session
    }
  },
  pages: {
    signIn: '/login',
  },
  session: {
    strategy: 'jwt',
  },
  secret: process.env.NEXTAUTH_SECRET || 'your-secret-key-change-in-production',
}
