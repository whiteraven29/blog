import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { blogApi } from '../api/client'
import Spinner from '../components/Spinner'
import Seo from '../components/Seo'
import './Categories.css'

export default function Categories() {
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    blogApi.getCategories()
      .then(({ data }) => setCategories(data.results || data))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />

  return (
    <main className="categories-page container">
      <Seo title="Categories" description="Browse wh1t3r4v3n blog posts by topic." />
      <div className="page-header">
        <h1><span className="accent" aria-hidden="true">/</span>categories</h1>
        <p className="text-muted">Browse posts by topic</p>
      </div>

      <div className="categories-grid">
        {categories.map((c) => (
          <Link key={c.id} to={`/categories/${c.slug}`} className="category-card">
            <div className="category-card__bar" style={{ background: c.color }} />
            <div className="category-card__body">
              <div className="category-card__header">
                <h2 className="category-card__name">{c.name}</h2>
                <span className="category-card__count" style={{ color: c.color }}>
                  {c.post_count}
                </span>
              </div>
              {c.description && (
                <p className="category-card__desc">{c.description}</p>
              )}
              <span className="category-card__link">View posts --&gt;</span>
            </div>
          </Link>
        ))}
      </div>
    </main>
  )
}
