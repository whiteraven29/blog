import { useState } from 'react'
import { LOCK_NOTICE, fillLockNotice } from '../config/lockNotice'
import './LockedPost.css'

export default function LockedPost({ post, onUnlock }) {
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const lock = { platform: post.lock_platform, hint: post.lock_hint }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!password.trim()) return
    setSubmitting(true)
    setError('')
    try {
      await onUnlock(password.trim())
    } catch (err) {
      setError(
        err.response?.status === 429
          ? 'Too many attempts. Please try again later.'
          : err.response?.status === 403
            ? 'Wrong password. Check it and try again.'
            : 'Could not unlock this post.'
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="locked-post" aria-labelledby="locked-post-title">
      <div className="locked-post__icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <rect x="4" y="11" width="16" height="10" rx="2" />
          <path d="M8 11V7a4 4 0 0 1 8 0v4" />
        </svg>
      </div>
      <h2 id="locked-post-title" className="locked-post__title">{LOCK_NOTICE.title}</h2>
      {LOCK_NOTICE.paragraphs.map((text) => (
        <p key={text} className="locked-post__text">{fillLockNotice(text, lock)}</p>
      ))}

      <form className="locked-post__form" onSubmit={handleSubmit}>
        <label className="sr-only" htmlFor="unlock-password">Password</label>
        <input
          id="unlock-password"
          className="input"
          type="password"
          autoComplete="off"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        <button type="submit" className="btn btn--primary" disabled={submitting}>
          {submitting ? 'Checking…' : 'Unlock'}
        </button>
      </form>
      {error && <p className="locked-post__error" role="alert">{error}</p>}
    </section>
  )
}
