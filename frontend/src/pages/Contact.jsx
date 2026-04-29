import { useState } from 'react'
import './Contact.css'

export default function Contact() {
  const [form, setForm] = useState({ name: '', email: '', title: '', message: '' })
  const [status, setStatus] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    setStatus('Thanks for reaching out! I\'ll get back to you soon.')
    setForm({ name: '', email: '', title: '', message: '' })
  }

  return (
    <main className="contact-page container">
      <div className="page-header">
        <h1><span className="accent">/</span>contacts</h1>
        <p className="text-muted">
          Interested in collaboration, security research, or just want to say hi?
        </p>
      </div>

      <div className="contact-layout">
        <div className="contact-info">
          <div className="info-card">
            <h3><span className="accent">#</span>message-me</h3>
            <div className="info-items">
              <div className="info-item">
                <span className="info-label">Email</span>
                <a href="mailto:hello@wh1t3r4v3n.dev" className="info-val accent">hello@wh1t3r4v3n.dev</a>
              </div>
              <div className="info-item">
                <span className="info-label">GitHub</span>
                <a href="https://github.com" className="info-val" target="_blank" rel="noreferrer">
                  github.com/wh1t3r4v3n
                </a>
              </div>
              <div className="info-item">
                <span className="info-label">Twitter/X</span>
                <span className="info-val">@wh1t3r4v3n</span>
              </div>
            </div>
          </div>

          <div className="info-card">
            <h3><span className="accent">#</span>availability</h3>
            <p className="info-desc">
              Open to freelance security assessments, CTF team collaboration, and consulting.
              Response time: 24-48 hours.
            </p>
          </div>
        </div>

        <form className="contact-form" onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="field">
              <label className="field__label">Name</label>
              <input
                className="input"
                placeholder="Your name"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
              />
            </div>
            <div className="field">
              <label className="field__label">Email</label>
              <input
                className="input"
                type="email"
                placeholder="your@email.com"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                required
              />
            </div>
          </div>
          <div className="field">
            <label className="field__label">Subject</label>
            <input
              className="input"
              placeholder="What's this about?"
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              required
            />
          </div>
          <div className="field">
            <label className="field__label">Message</label>
            <textarea
              className="input"
              placeholder="Tell me more..."
              rows={7}
              value={form.message}
              onChange={(e) => setForm({ ...form, message: e.target.value })}
              required
            />
          </div>
          <button type="submit" className="btn btn--primary contact-form__submit">Send --&gt;</button>
          {status && <p className="contact-form__status">{status}</p>}
        </form>
      </div>
    </main>
  )
}
