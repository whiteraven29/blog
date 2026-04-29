import { useState, useEffect, useCallback } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { blogApi } from '../api/client'
import PostCard from '../components/PostCard'
import Spinner from '../components/Spinner'
import './PostList.css'

const DIFFICULTIES = ['', 'beginner', 'intermediate', 'advanced']

export default function PostList() {
  const [params, setParams] = useSearchParams()
  const [posts, setPosts] = useState([])
  const [count, setCount] = useState(0)
  const [categories, setCategories] = useState([])
  const [tags, setTags] = useState([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)

  const search = params.get('search') || ''
  const category = params.get('category__slug') || ''
  const difficulty = params.get('difficulty') || ''
  const tag = params.get('tags__slug') || ''

  const fetchPosts = useCallback(() => {
    setLoading(true)
    const q = {}
    if (search) q.search = search
    if (category) q['category__slug'] = category
    if (difficulty) q.difficulty = difficulty
    if (tag) q['tags__slug'] = tag
    q.page = page

    blogApi.getPosts(q).then(({ data }) => {
      setPosts(data.results || data)
      setCount(data.count || (data.results || data).length)
    }).finally(() => setLoading(false))
  }, [search, category, difficulty, tag, page])

  useEffect(() => {
    blogApi.getCategories().then(({ data }) => setCategories(data.results || data))
    blogApi.getTags().then(({ data }) => setTags(data.results || data))
  }, [])

  useEffect(() => { setPage(1) }, [search, category, difficulty, tag])
  useEffect(() => { fetchPosts() }, [fetchPosts])

  const setFilter = (key, val) => {
    const next = new URLSearchParams(params)
    if (val) next.set(key, val)
    else next.delete(key)
    setParams(next)
  }

  return (
    <main className="post-list-page container">
      <div className="page-header">
        <h1><span className="accent">/</span>posts</h1>
        <p className="text-muted">{count} articles published</p>
      </div>

      {/* Search bar */}
      <div className="search-bar">
        <input
          className="input"
          type="search"
          placeholder="Search posts..."
          value={search}
          onChange={(e) => setFilter('search', e.target.value)}
        />
      </div>

      <div className="post-list-layout">
        {/* Sidebar filters */}
        <aside className="filters">
          <div className="filter-group">
            <h3 className="filter-title">Category</h3>
            <button
              className={`filter-btn${!category ? ' filter-btn--active' : ''}`}
              onClick={() => setFilter('category__slug', '')}
            >
              All
            </button>
            {categories.map((c) => (
              <button
                key={c.id}
                className={`filter-btn${category === c.slug ? ' filter-btn--active' : ''}`}
                onClick={() => setFilter('category__slug', c.slug)}
                style={category === c.slug ? { borderColor: c.color, color: c.color } : {}}
              >
                {c.name}
              </button>
            ))}
          </div>

          <div className="filter-group">
            <h3 className="filter-title">Difficulty</h3>
            {DIFFICULTIES.map((d) => (
              <button
                key={d}
                className={`filter-btn${difficulty === d ? ' filter-btn--active' : ''}`}
                onClick={() => setFilter('difficulty', d)}
              >
                {d || 'All'}
              </button>
            ))}
          </div>

          {tags.length > 0 && (
            <div className="filter-group">
              <h3 className="filter-title">Tags</h3>
              <div className="tags-cloud">
                {tags.slice(0, 20).map((t) => (
                  <button
                    key={t.id}
                    className={`tag${tag === t.slug ? ' tag--active' : ''}`}
                    onClick={() => setFilter('tags__slug', tag === t.slug ? '' : t.slug)}
                  >
                    {t.name}
                  </button>
                ))}
              </div>
            </div>
          )}
        </aside>

        {/* Post grid */}
        <div className="post-list-content">
          {loading ? (
            <Spinner />
          ) : posts.length === 0 ? (
            <div className="empty">
              <p>No posts found.</p>
              <button className="btn btn--ghost" onClick={() => setParams({})}>Clear filters</button>
            </div>
          ) : (
            <>
              <div className="posts-grid">
                {posts.map((p) => <PostCard key={p.id} post={p} />)}
              </div>
              <div className="pagination">
                <button
                  className="btn btn--ghost"
                  disabled={page === 1}
                  onClick={() => setPage(page - 1)}
                >
                  &lt;-- prev
                </button>
                <span className="pagination__info">page {page}</span>
                <button
                  className="btn btn--ghost"
                  disabled={posts.length < 12}
                  onClick={() => setPage(page + 1)}
                >
                  next --&gt;
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </main>
  )
}
