import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
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
  const [loadedQuery, setLoadedQuery] = useState(null)
  const [hasNext, setHasNext] = useState(false)
  const [loadError, setLoadError] = useState('')

  const search = params.get('search') || ''
  const category = params.get('category__slug') || ''
  const difficulty = params.get('difficulty') || ''
  const tag = params.get('tags__slug') || ''
  const page = Math.max(1, Number(params.get('page')) || 1)
  const queryKey = params.toString()

  useEffect(() => {
    let cancelled = false
    const q = {}
    if (search) q.search = search
    if (category) q['category__slug'] = category
    if (difficulty) q.difficulty = difficulty
    if (tag) q['tags__slug'] = tag
    q.page = page

    blogApi.getPosts(q).then(({ data }) => {
      if (cancelled) return
      const results = data.results || data
      setPosts(results)
      setCount(data.count ?? results.length)
      setHasNext(Boolean(data.next))
      setLoadError('')
      setLoadedQuery(queryKey)
    }).catch(() => {
      if (cancelled) return
      setPosts([])
      setCount(0)
      setHasNext(false)
      setLoadError('Could not load posts. Please try again.')
      setLoadedQuery(queryKey)
    })

    return () => { cancelled = true }
  }, [search, category, difficulty, tag, page, queryKey])

  useEffect(() => {
    blogApi.getCategories().then(({ data }) => setCategories(data.results || data))
    blogApi.getTags().then(({ data }) => setTags(data.results || data))
  }, [])

  const setFilter = (key, val) => {
    const next = new URLSearchParams(params)
    if (val) next.set(key, val)
    else next.delete(key)
    next.delete('page')
    setParams(next)
  }

  const setPage = (nextPage) => {
    const next = new URLSearchParams(params)
    if (nextPage > 1) next.set('page', String(nextPage))
    else next.delete('page')
    setParams(next)
  }

  const loading = loadedQuery !== queryKey

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
          ) : loadError ? (
            <div className="empty">
              <p>{loadError}</p>
            </div>
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
                  disabled={!hasNext}
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
