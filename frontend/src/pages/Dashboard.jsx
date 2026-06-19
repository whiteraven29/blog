import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { format } from 'date-fns'
import { blogApi } from '../api/client'
import useAuth from '../context/useAuth'
import Spinner from '../components/Spinner'
import './Dashboard.css'

const DIFF_COLORS = {
  beginner: 'var(--success)',
  intermediate: 'var(--warning)',
  advanced: 'var(--danger)',
}

export default function Dashboard() {
  const { user } = useAuth()
  const [posts, setPosts] = useState([])
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState(null)

  useEffect(() => {
    blogApi.myPosts()
      .then(({ data }) => setPosts(data.results || data))
      .finally(() => setLoading(false))
  }, [])

  const handleDelete = async (slug, title) => {
    if (!confirm(`Delete "${title}"? This cannot be undone.`)) return
    setDeleting(slug)
    try {
      await blogApi.deletePost(slug)
      setPosts((p) => p.filter((x) => x.slug !== slug))
    } catch {
      alert('Failed to delete post.')
    } finally {
      setDeleting(null)
    }
  }

  const drafts = posts.filter((p) => p.status === 'draft')
  const published = posts.filter((p) => p.status === 'published')

  return (
    <main className="dashboard container">
      <div className="dashboard__header">
        <div>
          <h1><span className="accent">/</span>dashboard</h1>
          <p className="text-muted">Welcome back, <span className="accent">@{user?.username}</span></p>
        </div>
        <Link to="/editor/new" className="btn btn--primary">+ New post</Link>
      </div>

      <div className="dashboard__stats">
        <div className="dash-stat">
          <span className="dash-stat__num accent">{posts.length}</span>
          <span className="dash-stat__label">total</span>
        </div>
        <div className="dash-stat">
          <span className="dash-stat__num" style={{ color: 'var(--success)' }}>{published.length}</span>
          <span className="dash-stat__label">published</span>
        </div>
        <div className="dash-stat">
          <span className="dash-stat__num" style={{ color: 'var(--warning)' }}>{drafts.length}</span>
          <span className="dash-stat__label">drafts</span>
        </div>
      </div>

      {loading ? <Spinner /> : posts.length === 0 ? (
        <div className="dashboard__empty">
          <p>No posts yet.</p>
          <Link to="/editor/new" className="btn btn--primary">Write your first post</Link>
        </div>
      ) : (
        <div className="posts-table">
          <div className="posts-table__head">
            <span>Title</span>
            <span>Category</span>
            <span>Status</span>
            <span>Difficulty</span>
            <span>Views</span>
            <span>Date</span>
            <span>Actions</span>
          </div>

          {posts.map((p) => (
            <div key={p.id} className={`posts-table__row${p.status === 'draft' ? ' posts-table__row--draft' : ''}`}>
              <span className="posts-table__title">
                <Link to={`/posts/${p.slug}`} className="posts-table__title-link" target="_blank">
                  {p.title}
                </Link>
                {p.is_featured && <span className="badge badge--featured">featured</span>}
              </span>
              <span className="text-muted" style={{ fontSize: '0.8rem' }}>
                {p.category?.name || '—'}
              </span>
              <span>
                <span className={`status-pill status-pill--${p.status}`}>{p.status}</span>
              </span>
              <span style={{ color: DIFF_COLORS[p.difficulty], fontSize: '0.8rem' }}>
                {p.difficulty}
              </span>
              <span className="text-muted" style={{ fontSize: '0.8rem' }}>{p.views}</span>
              <span className="text-muted" style={{ fontSize: '0.8rem' }}>
                {p.published_at
                  ? format(new Date(p.published_at), 'MMM d, yy')
                  : format(new Date(p.created_at), 'MMM d, yy')}
              </span>
              <span className="posts-table__actions">
                <Link to={`/editor/${p.slug}`} className="action-btn action-btn--edit">edit</Link>
                <button
                  className="action-btn action-btn--delete"
                  onClick={() => handleDelete(p.slug, p.title)}
                  disabled={deleting === p.slug}
                >
                  {deleting === p.slug ? '...' : 'delete'}
                </button>
              </span>
            </div>
          ))}
        </div>
      )}
    </main>
  )
}
