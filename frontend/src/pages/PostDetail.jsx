import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { format } from 'date-fns'
import { blogApi } from '../api/client'
import MarkdownContent from '../components/MarkdownContent'
import Seo from '../components/Seo'
import Spinner from '../components/Spinner'
import './PostDetail.css'

const DIFF_COLORS = {
  beginner: 'var(--success)',
  intermediate: 'var(--warning)',
  advanced: 'var(--danger)',
}

export default function PostDetail() {
  const { slug } = useParams()
  const [request, setRequest] = useState({
    slug: null,
    post: null,
    error: null,
  })
  const [comment, setComment] = useState({ author_name: '', author_email: '', body: '' })
  const [commentMsg, setCommentMsg] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    let cancelled = false

    blogApi.getPost(slug)
      .then(({ data }) => {
        if (!cancelled) setRequest({ slug, post: data, error: null })
      })
      .catch(() => {
        if (!cancelled) setRequest({ slug, post: null, error: 'Post not found.' })
      })

    return () => { cancelled = true }
  }, [slug])

  const handleComment = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      await blogApi.addComment(slug, comment)
      setCommentMsg('Comment submitted for review.')
      setComment({ author_name: '', author_email: '', body: '' })
    } catch {
      setCommentMsg('Failed to submit comment.')
    } finally {
      setSubmitting(false)
    }
  }

  if (request.slug !== slug) return <Spinner />
  if (request.error) return (
    <div className="post-error container">
      <p>{request.error}</p>
      <Link to="/posts" className="btn btn--ghost">Back to posts</Link>
    </div>
  )

  const post = request.post
  const description = post.excerpt || post.content.slice(0, 160)
  const articleSchema = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: post.title,
    description,
    datePublished: post.published_at,
    dateModified: post.updated_at,
    author: {
      '@type': 'Person',
      name: post.author?.username || 'wh1t3r4v3n',
    },
    ...(post.cover_image ? { image: post.cover_image } : {}),
  }

  return (
    <article className="post-detail">
      <Seo
        title={post.title}
        description={description}
        image={post.cover_image}
        type="article"
        jsonLd={articleSchema}
      />
      <header className="post-detail__header container">
        <div className="post-detail__breadcrumb">
          <Link to="/posts">#posts</Link>
          {post.category && (
            <>
              <span>/</span>
              <Link to={`/categories/${post.category.slug}`} style={{ color: post.category.color }}>
                {post.category.name}
              </Link>
            </>
          )}
        </div>

        <h1 className="post-detail__title">{post.title}</h1>

        <div className="post-detail__meta">
          <span className="post-detail__author">@{post.author?.username}</span>
          <span className="text-muted">·</span>
          <span className="text-muted">
            {post.published_at ? format(new Date(post.published_at), 'MMM d, yyyy') : 'Draft'}
          </span>
          <span className="text-muted">·</span>
          <span className="text-muted">{post.read_time} min read</span>
          <span className="text-muted">·</span>
          <span className="text-muted">{post.views} views</span>
          <span
            className="post-detail__diff"
            style={{ color: DIFF_COLORS[post.difficulty] }}
          >
            · {post.difficulty}
          </span>
        </div>

        {post.tags?.length > 0 && (
          <div className="post-detail__tags">
            {post.tags.map((t) => (
              <Link key={t.id} to={`/posts?tags__slug=${t.slug}`} className="tag">{t.name}</Link>
            ))}
          </div>
        )}
      </header>

      {post.cover_image && (
        <div className="post-detail__cover">
          <img src={post.cover_image} alt={post.title} />
        </div>
      )}

      <div className="post-detail__body container">
        <MarkdownContent className="post-detail__content">{post.content}</MarkdownContent>

        <aside className="post-detail__sidebar">
          <div className="sidebar-card">
            <h4>Author</h4>
            <div className="sidebar-author">
              <div className="sidebar-author__avatar">
                {post.author?.username?.[0]?.toUpperCase()}
              </div>
              <div>
                <p className="sidebar-author__name">@{post.author?.username}</p>
                {post.author?.bio && <p className="sidebar-author__bio">{post.author.bio}</p>}
              </div>
            </div>
          </div>

          {post.category && (
            <div className="sidebar-card">
              <h4>Category</h4>
              <Link
                to={`/categories/${post.category.slug}`}
                className="sidebar-cat"
                style={{ borderColor: post.category.color + '60' }}
              >
                <span className="sidebar-cat__dot" style={{ background: post.category.color }} />
                {post.category.name}
              </Link>
            </div>
          )}

          {post.tags?.length > 0 && (
            <div className="sidebar-card">
              <h4>Tags</h4>
              <div className="sidebar-tags">
                {post.tags.map((t) => (
                  <Link key={t.id} to={`/posts?tags__slug=${t.slug}`} className="tag">{t.name}</Link>
                ))}
              </div>
            </div>
          )}
        </aside>
      </div>

      {/* Comments */}
      <div className="post-comments container">
        <h2><span className="accent">#</span>comments ({post.comments?.length || 0})</h2>

        {post.comments?.length > 0 && (
          <div className="comments-list">
            {post.comments.map((c) => (
              <div key={c.id} className="comment">
                <div className="comment__header">
                  <span className="comment__author">{c.author_name}</span>
                  <span className="comment__date text-muted">
                    {format(new Date(c.created_at), 'MMM d, yyyy')}
                  </span>
                </div>
                <p className="comment__body">{c.body}</p>
              </div>
            ))}
          </div>
        )}

        <form className="comment-form" onSubmit={handleComment}>
          <h3>Leave a comment</h3>
          <div className="comment-form__row">
            <label className="sr-only" htmlFor="comment-name">Your name</label>
            <input
              id="comment-name"
              className="input"
              placeholder="Your name"
              value={comment.author_name}
              onChange={(e) => setComment({ ...comment, author_name: e.target.value })}
              required
            />
            <label className="sr-only" htmlFor="comment-email">Email address</label>
            <input
              id="comment-email"
              className="input"
              type="email"
              placeholder="your@email.com"
              value={comment.author_email}
              onChange={(e) => setComment({ ...comment, author_email: e.target.value })}
              required
            />
          </div>
          <label className="sr-only" htmlFor="comment-body">Comment</label>
          <textarea
            id="comment-body"
            className="input"
            placeholder="Write your comment..."
            rows={5}
            value={comment.body}
            onChange={(e) => setComment({ ...comment, body: e.target.value })}
            required
          />
          <button type="submit" className="btn btn--primary" disabled={submitting}>
            {submitting ? 'Sending...' : 'Send comment'}
          </button>
          {commentMsg && <p className="comment-form__msg">{commentMsg}</p>}
        </form>
      </div>
    </article>
  )
}
