import { NextResponse } from 'next/server'
import { getToken } from 'next-auth/jwt'

function loginUrl(req, callbackPath) {
  const u = new URL('/login', req.url)
  u.searchParams.set('callbackUrl', callbackPath || '/chat')
  return u
}

function onboardingUrl(req, callbackPath) {
  const u = new URL('/onboarding', req.url)
  u.searchParams.set('callbackUrl', callbackPath || '/chat')
  return u
}

export async function middleware(req) {
  const secret = process.env.NEXTAUTH_SECRET
  const path = req.nextUrl.pathname
  const token = secret ? await getToken({ req, secret }) : null
  const authed = Boolean(token?.accessToken || token?.sub)

  const host = req.headers.get('host')
  if (host === 'sikhsituationbot.sage-school.com') {
    const newUrl = new URL(req.nextUrl.href)
    newUrl.hostname = 'gianiji.com'
    newUrl.port = ''
    newUrl.protocol = 'https:'
    return NextResponse.redirect(newUrl, 301)
  }

  if (path === '/onboarding' || path.startsWith('/onboarding/')) {
    if (!authed) {
      return NextResponse.redirect(loginUrl(req, '/onboarding'))
    }
    return NextResponse.next()
  }

  const needsProfileGate =
    path.startsWith('/admin') ||
    path.startsWith('/settings') ||
    path === '/chat' ||
    path.startsWith('/chat/') ||
    path === '/parmaans' ||
    path.startsWith('/parmaans/') ||
    path === '/'

  if (!needsProfileGate) {
    return NextResponse.next()
  }

  if (!authed) {
    if (path === '/') {
      return NextResponse.next()
    }
    return NextResponse.redirect(loginUrl(req, path))
  }

  if (token?.needsBirthYear === true) {
    return NextResponse.redirect(onboardingUrl(req, path === '/' ? '/chat' : path))
  }

  if (path.startsWith('/admin') && !token?.isAdmin) {
    return NextResponse.redirect(new URL('/chat', req.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    '/',
    '/admin/:path*',
    '/settings/:path*',
    '/chat',
    '/chat/:path*',
    '/parmaans',
    '/parmaans/:path*',
    '/onboarding',
    '/onboarding/:path*',
  ],
}
