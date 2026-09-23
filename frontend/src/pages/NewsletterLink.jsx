import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { blogApi } from '../api/client'
import Seo from '../components/Seo'
import './NewsletterLink.css'

const COPY = {
  confirm: {
    title: 'Confirm subscription',
    heading: 'confirm',
    working: 'Confirming your subscription…',
  },
  unsubscribe: {
    title: 'Unsubscribe',
    heading: 'unsubscribe',
    working: 'Unsubscribing…',
  },
}

function errorMessage(err) {
  if (err.response?.status === 429) return 'Too many attempts from here. Please try again in a minute.'
  return err.response?.data?.detail || 'Something went wrong. Please try again.'
}

// Landing page for the links in newsletter emails. Confirming happens as soon as
// the page loads. Unsubscribing waits for a click, because mail scanners open
// every link in a message and would otherwise unsubscribe people on delivery.
export default function NewsletterLink({ action }) {
  const [params] = useSearchParams()
  const token = params.get('token') || ''
  const copy = COPY[action]
  const [state, setState] = useState(() => (
    !token ? { phase: 'error', text: 'This link is incomplete. Copy the whole link from the email.' }
      : action === 'confirm' ? { phase: 'working', text: copy.working }
        : { phase: 'idle', text: '' }
  ))

  const run = async () => {
    setState({ phase: 'working', text: copy.working })
    try {
      const call = action === 'confirm' ? blogApi.confirmSubscription : blogApi.unsubscribe
      const { data } = await call(token)
      setState({ phase: 'done', text: data.message })
    } catch (err) {
      setState({ phase: 'error', text: errorMessage(err) })
    }
  }

  useEffect(() => {
    if (action !== 'confirm' || !token) return
    let cancelled = false
    blogApi.confirmSubscription(token)
      .then(({ data }) => { if (!cancelled) setState({ phase: 'done', text: data.message }) })
      .catch((err) => { if (!cancelled) setState({ phase: 'error', text: errorMessage(err) }) })
    return () => { cancelled = true }
  }, [action, token])

  return (
    <main className="newsletter-link container">
      <Seo title={copy.title} description={`${copy.title} for the wh1t3r4v3n newsletter.`} />
      <div className="newsletter-link__box">
        <h1><span className="accent" aria-hidden="true">#</span>{copy.heading}</h1>

        {action === 'unsubscribe' && state.phase === 'idle' && (
          <>
            <p className="text-muted">Stop getting an email when a new post goes up?</p>
            <button type="button" className="btn btn--primary" onClick={run}>Unsubscribe</button>
          </>
        )}

        {state.text && (
          <p
            className={`newsletter-link__msg newsletter-link__msg--${state.phase}`}
            role={state.phase === 'error' ? 'alert' : 'status'}
          >
            {state.text}
          </p>
        )}

        {state.phase === 'done' && action === 'unsubscribe' && (
          <p className="text-muted">Changed your mind? You can subscribe again from the home page.</p>
        )}

        {(state.phase === 'done' || state.phase === 'error') && (
          <Link to="/" className="btn btn--ghost">Back to the blog</Link>
        )}
      </div>
    </main>
  )
}
