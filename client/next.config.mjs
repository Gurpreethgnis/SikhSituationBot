/** @type {import('next').NextConfig} */

/**
 * When FLASK_API_URL is set at build time, browser requests to /ask and /api/* (except NextAuth)
 * are proxied to Flask. Use this if you do NOT set NEXT_PUBLIC_API_URL — otherwise the client
 * bundle falls back to http://localhost:5000 and your live site never hits Railway (empty backend logs).
 */
const flaskBase = (process.env.FLASK_API_URL || process.env.BACKEND_URL || '').replace(/\/$/, '')

if (process.env.NODE_ENV === 'production' && !flaskBase && !process.env.NEXT_PUBLIC_API_URL) {
  console.warn(
    '[next.config] Production: neither FLASK_API_URL nor NEXT_PUBLIC_API_URL is set. ' +
      'Browser API calls will 404 unless you set one of them (see client/lib/api.js comment).',
  )
}

function flaskRewrites() {
  if (!flaskBase) return []
  const b = flaskBase
  return [
    { source: '/ask', destination: `${b}/ask` },
    { source: '/health', destination: `${b}/health` },
    { source: '/api/health', destination: `${b}/api/health` },
    { source: '/random-shabads', destination: `${b}/random-shabads` },
    { source: '/api/stats/:path*', destination: `${b}/api/stats/:path*` },
    { source: '/api/chats', destination: `${b}/api/chats` },
    { source: '/api/chats/:path*', destination: `${b}/api/chats/:path*` },
    { source: '/api/shared/:path*', destination: `${b}/api/shared/:path*` },
    { source: '/api/parmaans/:path*', destination: `${b}/api/parmaans/:path*` },
    { source: '/api/search', destination: `${b}/api/search` },
    { source: '/api/admin/:path*', destination: `${b}/api/admin/:path*` },
    /* Flask auth only — do not use /api/auth/:path* or NextAuth breaks */
    { source: '/api/auth/login', destination: `${b}/api/auth/login` },
    { source: '/api/auth/register', destination: `${b}/api/auth/register` },
    { source: '/api/auth/oauth-sync', destination: `${b}/api/auth/oauth-sync` },
    { source: '/api/auth/me', destination: `${b}/api/auth/me` },
    { source: '/api/memory', destination: `${b}/api/memory` },
    { source: '/api/memory/:path*', destination: `${b}/api/memory/:path*` },
    { source: '/api/feedback', destination: `${b}/api/feedback` },
  ]
}

const nextConfig = {
  async rewrites() {
    return flaskRewrites()
  },
}

export default nextConfig
