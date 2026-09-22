import { Component } from 'react'

/**
 * Catches render errors in the routed subtree.
 *
 * The common case is a failed dynamic import: a deployment replaces the hashed
 * chunks a loaded tab still references, so the next lazy route 404s. React caches
 * that rejection, which is why the primary action is a reload rather than a retry.
 */
export default class ErrorBoundary extends Component {
  state = { error: null }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    console.error('Unhandled error while rendering a route:', error, info)
  }

  componentDidUpdate(prevProps) {
    // Navigating away should clear an error raised by the previous route.
    if (this.state.error && prevProps.resetKey !== this.props.resetKey) {
      this.setState({ error: null })
    }
  }

  render() {
    if (!this.state.error) return this.props.children

    return (
      <main className="container" style={{ padding: '5rem 0' }}>
        <div className="empty">
          <h1 className="accent" style={{ fontSize: '2rem' }}>Something broke</h1>
          <p>
            This page failed to load. If the site was updated a moment ago,
            reloading will pick up the new version.
          </p>
          <button className="btn btn--primary" onClick={() => window.location.reload()}>
            Reload page
          </button>
        </div>
      </main>
    )
  }
}
