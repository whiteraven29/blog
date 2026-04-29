import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { blogApi } from '../api/client'
import PostCard from '../components/PostCard'
import Spinner from '../components/Spinner'
import './PostList.css'

export default function CategoryDetail() {
  const { slug } = useParams()
  const [category, setCategory] = useState(null)
  const [posts, setPosts] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      blogApi.getCategory(slug),
      blogApi.getPosts({ 'category__slug': slug, page_size: 50 }),
    ]).then(([cat, ps]) => {
      setCategory(cat.data)
      setPosts(ps.data.results || ps.data)
    }).finally(() => setLoading(false))
  }, [slug])

  if (loading) return <Spinner />
  if (!category) return (
    <div className="post-list-page container">
      <p className="text-muted">Category not found.</p>
      <Link to="/categories" className="btn btn--ghost">All categories</Link>
    </div>
  )

  return (
    <main className="post-list-page container">
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ width: 12, height: 12, borderRadius: '50%', background: category.color }} />
          <h1 style={{ fontSize: '2rem' }}>{category.name}</h1>
        </div>
        {category.description && <p className="text-muted" style={{ marginTop: '0.5rem' }}>{category.description}</p>}
        <p className="text-muted" style={{ marginTop: '0.25rem' }}>{category.post_count} posts</p>
      </div>

      {posts.length === 0 ? (
        <div className="empty"><p>No posts in this category yet.</p></div>
      ) : (
        <div className="posts-grid">
          {posts.map((p) => <PostCard key={p.id} post={p} />)}
        </div>
      )}
    </main>
  )
}
