import Link from 'next/link'
import './admin.css'

export default function AdminLayout({ children }) {
  return (
    <div className="admin-shell">
      <aside className="admin-sidebar">
        <h2 className="admin-brand">Admin</h2>
        <nav className="admin-nav">
          <Link href="/admin">Overview</Link>
          <Link href="/admin/users">Users</Link>
          <Link href="/admin/shabads">Shabads</Link>
          <Link href="/admin/analytics">Analytics</Link>
          <Link href="/admin/interactions">Interactions</Link>
          <Link href="/admin/llm">LLM</Link>
          <Link href="/chat">Back to app</Link>
        </nav>
      </aside>
      <div className="admin-main">{children}</div>
    </div>
  )
}
