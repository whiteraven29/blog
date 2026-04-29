import { Link } from 'react-router-dom'
import { format } from 'date-fns'
import './PostCard.css'

const DIFF_COLORS = {
  beginner: 'var(--success)',
  intermediate: 'var(--warning)',
  advanced: 'var(--danger)',
}

export default function PostCard({ post }) {
  const date = post.published_at || post.created_at
  return (
    <article className="post-card">
      {post.cover_image && (
        <Link to={`/posts/${post.slug}`} className="post-card__img-wrap">
          <img src={post.cover_image} alt={post.title} className="post-card__img" loading="lazy" />
        </Link>
      )}
      <div className="post-card__body">
        <div className="post-card__meta">
          {post.category && (
            <Link
              to={`/categories/${post.category.slug}`}
              className="post-card__category"
              style={{ color: post.category.color }}
            >
              {post.category.name}
            </Link>
          )}
          <span
            className="post-card__diff"
            style={{ color: DIFF_COLORS[post.difficulty] }}
          >
            {post.difficulty}
          </span>
        </div>

        <h3 className="post-card__title">
          <Link to={`/posts/${post.slug}`}>{post.title}</Link>
        </h3>

        <p className="post-card__excerpt">{post.excerpt}</p>

        <div className="post-card__tags">
          {post.tags?.slice(0, 4).map((t) => (
            <Link key={t.id} to={`/posts?tags__slug=${t.slug}`} className="tag">
              {t.name}
            </Link>
          ))}
        </div>

        <div className="post-card__footer">
          <span className="post-card__date">
            {date ? format(new Date(date), 'MMM d, yyyy') : 'Draft'}
          </span>
          <span className="post-card__read">{post.read_time} min read</span>
          <Link to={`/posts/${post.slug}`} className="post-card__read-link">
            Read <span>--&gt;</span>
          </Link>
        </div>
      </div>
    </article>
  )
}
