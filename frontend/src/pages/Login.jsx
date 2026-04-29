import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './Login.css'

export default function Login() {
  const [form, setForm] = useState({ username: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await login(form)
      navigate('/')
    } catch {
      setError('Invalid username or password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="auth-page container">
      <div className="auth-card">
        <h1><span className="accent">/</span>login</h1>
        <p className="text-muted">Access your account to manage posts.</p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="field">
            <label className="field__label">Username</label>
            <input
              className="input"
              placeholder="username"
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              required
            />
          </div>
          <div className="field">
            <label className="field__label">Password</label>
            <input
              className="input"
              type="password"
              placeholder="••••••••"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              required
            />
          </div>
          {error && <p className="auth-error">{error}</p>}
          <button type="submit" className="btn btn--primary" disabled={loading}>
            {loading ? 'Logging in...' : 'Login --&gt;'}
          </button>
        </form>

        <p className="auth-footer text-muted">
          Don't have an account? <Link to="/register" className="accent">Register</Link>
        </p>
      </div>
    </main>
  )
}
