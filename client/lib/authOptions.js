import CredentialsProvider from 'next-auth/providers/credentials'
import GoogleProvider from 'next-auth/providers/google'

const flaskBase = () =>
  process.env.FLASK_API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'

/** Re-sync is_admin and birth-year gate from Flask so JWT matches DB after ADMIN_EMAIL / manual admin changes. */
const CLAIMS_REFRESH_MS = 60_000

async function refreshAdminFromFlask(token) {
  if (!token?.accessToken) return
  const now = Date.now()
  const last = typeof token.claimsRefreshedAt === 'number' ? token.claimsRefreshedAt : 0
  if (last && now - last < CLAIMS_REFRESH_MS) return
  try {
    const res = await fetch(`${flaskBase()}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token.accessToken}` },
      cache: 'no-store',
    })
    const data = await res.json().catch(() => ({}))
    if (res.ok && data.user) {
      token.isAdmin = Boolean(data.user.is_admin)
      if (data.user.id != null) token.flaskUserId = String(data.user.id)
      token.needsBirthYear = data.user.birth_year == null
    }
  } catch {
    /* ignore */
  }
  token.claimsRefreshedAt = now
}

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
          needsBirthYear: data.user.birth_year == null,
        }
      },
    }),
]

export const authOptions = {
  providers,
  callbacks: {
    async jwt({ token, user, account, trigger, session }) {
      if (trigger === 'update' && session?.birthYearComplete) {
        token.needsBirthYear = false
      }

      if (account?.provider === 'google' && user?.email) {
        token.authProvider = 'google'
        if (user.email) token.email = user.email
        const key = process.env.FLASK_INTERNAL_API_KEY
        if (!key) {
          console.warn(
            '[next-auth] FLASK_INTERNAL_API_KEY is not set. Google sign-in cannot sync with Flask; ' +
              'set the same secret on Vercel and Railway and redeploy.',
          )
        } else {
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
            token.needsBirthYear = data.user?.birth_year == null
          } else if (!res.ok) {
            console.warn(
              '[next-auth] Flask oauth-sync failed:',
              res.status,
              data?.error || '',
              '— check FLASK_INTERNAL_API_KEY matches Railway and FLASK_API_URL points to your API.',
            )
          }
        }
      }
      if (account?.provider === 'credentials' && user) {
        token.authProvider = 'credentials'
        token.accessToken = user.accessToken
        token.isAdmin = Boolean(user.isAdmin)
        token.flaskUserId = user.id
        if (typeof user.needsBirthYear === 'boolean') {
          token.needsBirthYear = user.needsBirthYear
        }
      }

      // Retry Flask sync for Google sessions still missing an API token (transient errors or key fixed later).
      const OAUTH_RETRY_MS = 60_000
      const internalKey = process.env.FLASK_INTERNAL_API_KEY
      const email = token.email || user?.email
      if (
        internalKey &&
        !token.accessToken &&
        token.authProvider === 'google' &&
        typeof email === 'string' &&
        email.length > 0
      ) {
        const now = Date.now()
        const last = typeof token.lastOauthRetry === 'number' ? token.lastOauthRetry : 0
        if (now - last >= OAUTH_RETRY_MS) {
          token.lastOauthRetry = now
          const res = await fetch(`${flaskBase()}/api/auth/oauth-sync`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-Internal-Key': internalKey,
            },
            body: JSON.stringify({
              email,
              name: token.name,
              avatar_url: token.picture,
            }),
          })
          const data = await res.json().catch(() => ({}))
          if (res.ok && data.token) {
            token.accessToken = data.token
            token.isAdmin = Boolean(data.user?.is_admin)
            if (data.user?.id != null) token.flaskUserId = String(data.user.id)
            token.needsBirthYear = data.user?.birth_year == null
          }
        }
      }
      await refreshAdminFromFlask(token)
      return token
    },
    async session({ session, token }) {
      session.accessToken = token.accessToken
      session.needsBirthYear = Boolean(token.needsBirthYear)
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
