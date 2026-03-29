import { withAuth } from 'next-auth/middleware'

export default withAuth({
  callbacks: {
    authorized: ({ token, req }) => {
      const path = req.nextUrl.pathname
      if (path.startsWith('/settings')) return Boolean(token)
      if (path.startsWith('/admin')) return Boolean(token?.isAdmin)
      return true
    },
  },
})

export const config = {
  matcher: ['/admin/:path*', '/settings/:path*'],
}
