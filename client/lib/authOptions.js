import CredentialsProvider from 'next-auth/providers/credentials'
import GoogleProvider from 'next-auth/providers/google'

const flaskBase = () =>
  process.env.FLASK_API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'

/** Omit Google provider when id/secret missing so email/password auth still works in dev/partial deploys. */
const googleId = (process.env.GOOGLE_CLIENT_ID || '').trim()
const googleSecret = (process.env.GOOGLE_CLIENT_SECRET || '').trim()
const googleProviderConfigured = Boolean(googleId && googleSecret)

const providers = [
  ...(googleProviderConfigured
    ? [
        GoogleProvider({
          clientId: googleId,
          clientSecret: googleSecret,
        }),
      ]
    : []),
  CredentialsProvider({
      name: 'Credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null
        const res = await fetch(`${flaskBase()}/api/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: credentials.email,
            password: credentials.password,
          }),
        })
        const data = await res.json().catch(() => ({}))
        if (!res.ok) return null
        return {
          id: String(data.user.id),
          email: data.user.email,
          name: data.user.name,
          image: data.user.avatar_url || undefined,
          accessToken: data.token,
          isAdmin: Boolean(data.user.is_admin),
        }
      },
    }),
]

export const authOptions = {
  providers,
  callbacks: {
    async jwt({ token, user, account }) {
      if (account?.provider === 'google' && user?.email) {
        const key = process.env.FLASK_INTERNAL_API_KEY
        if (key) {
          const res = await fetch(`${flaskBase()}/api/auth/oauth-sync`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-Internal-Key': key,
            },
            body: JSON.stringify({
              email: user.email,
              name: user.name,
              avatar_url: user.image,
            }),
          })
          const data = await res.json().catch(() => ({}))
          if (res.ok && data.token) {
            token.accessToken = data.token
            token.isAdmin = Boolean(data.user?.is_admin)
            token.flaskUserId = String(data.user?.id ?? user.id)
          }
        }
      }
      if (account?.provider === 'credentials' && user) {
        token.accessToken = user.accessToken
        token.isAdmin = Boolean(user.isAdmin)
        token.flaskUserId = user.id
      }
      return token
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken
      if (session.user) {
        session.user.isAdmin = Boolean(token.isAdmin)
        if (token.flaskUserId) session.user.id = token.flaskUserId
      }
      return session
    },
  },
  pages: {
    signIn: '/login',
  },
  session: {
    strategy: 'jwt',
    maxAge: 7 * 24 * 60 * 60,
  },
  secret: process.env.NEXTAUTH_SECRET,
}
