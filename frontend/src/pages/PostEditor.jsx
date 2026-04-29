import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import MDEditor from '@uiw/react-md-editor'
import { blogApi } from '../api/client'
import Spinner from '../components/Spinner'
import './PostEditor.css'

const EMPTY = {
  title: '',
  excerpt: '',
  content: '## Introduction\n\nWrite your post here...',
  category: '',
  tags: '',
  difficulty: 'beginner',
  status: 'draft',
  read_time: 5,
  is_featured: false,
}

export default function PostEditor() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const isNew = slug === 'new'

  const [form, setForm] = useState(EMPTY)
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(!isNew)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [lastSaved, setLastSaved] = useState(null)
  const [preview, setPreview] = useState('live')

  useEffect(() => {
    blogApi.getCategories().then(({ data }) => setCategories(data.results || data))
  }, [])

  useEffect(() => {
    if (isNew) return
    blogApi.getPostForEdit(slug)
      .then(({ data }) => {
        setForm({
          title: data.title || '',
          excerpt: data.excerpt || '',
          content: data.content || '',
          category: data.category?.id || '',
          tags: (data.tags || []).map((t) => t.name).join(', '),
          difficulty: data.difficulty || 'beginner',
          status: data.status || 'draft',
          read_time: data.read_time || 5,
          is_featured: data.is_featured || false,
        })
      })
      .catch(() => setError('Could not load post. Check you are the author.'))
      .finally(() => setLoading(false))
  }, [slug, isNew])

  const set = (key, val) => setForm((f) => ({ ...f, [key]: val }))

  const buildPayload = (overrideStatus) => {
    const tagList = form.tags
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean)

    return {
      title: form.title,
      excerpt: form.excerpt,
      content: form.content,
      category: form.category || null,
      tags_by_name: tagList,
      difficulty: form.difficulty,
      status: overrideStatus ?? form.status,
      read_time: Number(form.read_time),
      is_featured: form.is_featured,
    }
  }

  const save = async (overrideStatus) => {
    if (!form.title.trim()) { setError('Title is required.'); return }
    setSaving(true)
    setError('')
    try {
      const payload = buildPayload(overrideStatus)
      let resultSlug
      if (isNew) {
        const { data } = await blogApi.createPost(payload)
        resultSlug = data.slug
        navigate(`/editor/${resultSlug}`, { replace: true })
      } else {
        await blogApi.updatePost(slug, payload)
        resultSlug = slug
      }
      setLastSaved(new Date())
      if (overrideStatus === 'published') {
        navigate(`/posts/${resultSlug}`)
      }
    } catch (err) {
      const detail = err.response?.data
      setError(typeof detail === 'string' ? detail : JSON.stringify(detail) || 'Save failed.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <Spinner />

  return (
    <div className="editor-layout">
      {/* Top bar */}
      <div className="editor-topbar">
        <Link to="/dashboard" className="editor-back">← dashboard</Link>
        <input
          className="editor-title-input"
          placeholder="Post title..."
          value={form.title}
          onChange={(e) => set('title', e.target.value)}
        />
        <div className="editor-topbar__actions">
          {lastSaved && (
            <span className="editor-saved">
              saved {lastSaved.toLocaleTimeString()}
            </span>
          )}
          <button
            className="btn btn--ghost"
            onClick={() => save()}
            disabled={saving}
          >
            {saving ? 'Saving…' : 'Save draft'}
          </button>
          <button
            className="btn btn--primary"
            onClick={() => save('published')}
            disabled={saving}
          >
            {form.status === 'published' ? 'Update' : 'Publish'} →
          </button>
        </div>
      </div>

      {error && <div className="editor-error">{error}</div>}

      <div className="editor-body">
        {/* Sidebar */}
        <aside className="editor-sidebar">
          <div className="editor-field">
            <label>Category</label>
            <select
              className="input"
              value={form.category}
              onChange={(e) => set('category', e.target.value)}
            >
              <option value="">None</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>

          <div className="editor-field">
            <label>Tags <span className="editor-hint">comma separated</span></label>
            <input
              className="input"
              placeholder="ctf, web, python"
              value={form.tags}
              onChange={(e) => set('tags', e.target.value)}
            />
          </div>

          <div className="editor-field">
            <label>Difficulty</label>
            <select
              className="input"
              value={form.difficulty}
              onChange={(e) => set('difficulty', e.target.value)}
            >
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
          </div>

          <div className="editor-field">
            <label>Read time (min)</label>
            <input
              className="input"
              type="number"
              min="1"
              max="120"
              value={form.read_time}
              onChange={(e) => set('read_time', e.target.value)}
            />
          </div>

          <div className="editor-field">
            <label>Excerpt</label>
            <textarea
              className="input"
              rows={4}
              placeholder="Brief summary shown in post cards..."
              value={form.excerpt}
              onChange={(e) => set('excerpt', e.target.value)}
            />
          </div>

          <div className="editor-field editor-field--check">
            <input
              type="checkbox"
              id="featured"
              checked={form.is_featured}
              onChange={(e) => set('is_featured', e.target.checked)}
            />
            <label htmlFor="featured">Featured post</label>
          </div>

          <div className="editor-field">
            <label>Status</label>
            <select
              className="input"
              value={form.status}
              onChange={(e) => set('status', e.target.value)}
            >
              <option value="draft">Draft</option>
              <option value="published">Published</option>
            </select>
          </div>

          {!isNew && (
            <Link
              to={`/posts/${slug}`}
              target="_blank"
              className="btn btn--ghost"
              style={{ textAlign: 'center', marginTop: '0.5rem' }}
            >
              View live →
            </Link>
          )}
        </aside>

        {/* Markdown editor */}
        <div className="editor-main" data-color-mode="dark">
          <MDEditor
            value={form.content}
            onChange={(val) => set('content', val || '')}
            preview={preview}
            height="100%"
            visibleDragbar={false}
            toolbarHeight={44}
            style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)', borderRadius: 'var(--radius)' }}
            previewOptions={{
              style: { background: 'var(--bg-secondary)', padding: '1.5rem' },
            }}
          />
          <div className="editor-preview-toggle">
            {['edit', 'live', 'preview'].map((m) => (
              <button
                key={m}
                className={`toggle-btn${preview === m ? ' toggle-btn--active' : ''}`}
                onClick={() => setPreview(m)}
              >
                {m}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
