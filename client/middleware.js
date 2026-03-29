import { withAuth } from 'next-auth/middleware'

export default withAuth({
  pages: {
    signIn: '/login',
  },
  callbacks: {
    authorized: ({ token, req }) => {
      const path = req.nextUrl.pathname
      if (path.startsWith('/admin')) return Boolean(token?.isAdmin)
      if (path.startsWith('/settings')) return Boolean(token)
      if (path === '/chat' || path.startsWith('/chat/')) return Boolean(token)
      if (path === '/parmaans' || path.startsWith('/parmaans/')) return Boolean(token)
      return true
    },
  },
})

export const config = {
  matcher: ['/admin/:path*', '/settings/:path*', '/chat', '/chat/:path*', '/parmaans', '/parmaans/:path*'],
}
