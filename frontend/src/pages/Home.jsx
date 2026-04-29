import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { blogApi } from '../api/client'
import PostCard from '../components/PostCard'
import Spinner from '../components/Spinner'
import './Home.css'

export default function Home() {
  const [featured, setFeatured] = useState([])
  const [recent, setRecent] = useState([])
  const [categories, setCategories] = useState([])
  const [stats, setStats] = useState(null)
  const [email, setEmail] = useState('')
  const [subMsg, setSubMsg] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      blogApi.getFeatured(),
      blogApi.getPosts({ page_size: 6 }),
      blogApi.getCategories(),
      blogApi.getStats(),
    ]).then(([feat, posts, cats, st]) => {
      setFeatured(feat.data.results || feat.data)
      setRecent(posts.data.results || posts.data)
      setCategories(cats.data.results || cats.data)
      setStats(st.data)
    }).finally(() => setLoading(false))
  }, [])

  const handleSubscribe = async (e) => {
    e.preventDefault()
    try {
      await blogApi.subscribe(email)
      setSubMsg('Subscribed!')
      setEmail('')
    } catch {
      setSubMsg('Already subscribed or invalid email.')
    }
  }

  if (loading) return <Spinner />

  return (
    <main className="home">
      {/* Hero */}
      <section className="hero container">
        <div className="hero__content">
          <p className="hero__greeting">// welcome to</p>
          <h1 className="hero__title">
            <span className="accent">wh1t3r4v3n</span>blog
          </h1>
          <p className="hero__sub">
            Writeups on <span className="accent">offensive security</span>, CTF challenges,{' '}
            <span className="accent">web development</span> & programming languages.
          </p>
          <div className="hero__actions">
            <Link to="/posts" className="btn btn--primary">Browse posts --&gt;</Link>
            <Link to="/categories" className="btn btn--ghost">#categories</Link>
          </div>
        </div>
        <div className="hero__deco" aria-hidden>
          <div className="hero__squares">
            <div className="sq sq--1" />
            <div className="sq sq--2" />
            <div className="sq sq--3" />
          </div>
        </div>
      </section>

      {/* Stats */}
      {stats && (
        <section className="stats container">
          <div className="stats__grid">
            <div className="stats__item">
              <span className="stats__num accent">{stats.total_posts}</span>
              <span className="stats__label">posts</span>
            </div>
            <div className="stats__item">
              <span className="stats__num accent">{stats.total_categories}</span>
              <span className="stats__label">categories</span>
            </div>
            <div className="stats__item">
              <span className="stats__num accent">{stats.total_tags}</span>
              <span className="stats__label">tags</span>
            </div>
            <div className="stats__item">
              <span className="stats__num accent">{stats.total_views}</span>
              <span className="stats__label">views</span>
            </div>
          </div>
        </section>
      )}

      {/* Featured */}
      {featured.length > 0 && (
        <section className="section container">
          <div className="section__header">
            <h2><span className="accent">#</span>featured</h2>
            <Link to="/posts?is_featured=true" className="section__more">view all --&gt;</Link>
          </div>
          <div className="posts-grid">
            {featured.slice(0, 3).map((p) => <PostCard key={p.id} post={p} />)}
          </div>
        </section>
      )}

      {/* Categories */}
      {categories.length > 0 && (
        <section className="section container">
          <div className="section__header">
            <h2><span className="accent">#</span>categories</h2>
            <Link to="/categories" className="section__more">all --&gt;</Link>
          </div>
          <div className="cats-grid">
            {categories.map((c) => (
              <Link key={c.id} to={`/categories/${c.slug}`} className="cat-card">
                <span className="cat-card__dot" style={{ background: c.color }} />
                <span className="cat-card__name">{c.name}</span>
                <span className="cat-card__count">{c.post_count} posts</span>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Recent */}
      {recent.length > 0 && (
        <section className="section container">
          <div className="section__header">
            <h2><span className="accent">#</span>recent-posts</h2>
            <Link to="/posts" className="section__more">view all --&gt;</Link>
          </div>
          <div className="posts-grid">
            {recent.slice(0, 6).map((p) => <PostCard key={p.id} post={p} />)}
          </div>
        </section>
      )}

      {/* Newsletter */}
      <section className="newsletter container">
        <div className="newsletter__box">
          <h2><span className="accent">#</span>stay-updated</h2>
          <p>Get notified when new writeups drop — no spam, ever.</p>
          <form className="newsletter__form" onSubmit={handleSubscribe}>
            <input
              type="email"
              className="input"
              placeholder="your@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <button type="submit" className="btn btn--primary">Subscribe</button>
          </form>
          {subMsg && <p className="newsletter__msg">{subMsg}</p>}
        </div>
      </section>
    </main>
  )
}
