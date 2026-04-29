import { useState, useEffect } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './Navbar.css'

export default function Navbar() {
  const [open, setOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', onScroll)
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => {
    if (open) document.body.style.overflow = 'hidden'
    else document.body.style.overflow = ''
    return () => { document.body.style.overflow = '' }
  }, [open])

  const handleLogout = () => {
    logout()
    navigate('/')
    setOpen(false)
  }

  const links = [
    { to: '/', label: '#home' },
    { to: '/posts', label: '#posts' },
    { to: '/categories', label: '#categories' },
    { to: '/about', label: '#about' },
    { to: '/contact', label: '#contact' },
  ]

  return (
    <header className={`navbar${scrolled ? ' navbar--scrolled' : ''}`}>
      <div className="navbar__inner container">
        <Link to="/" className="navbar__logo">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <rect x="0" y="6" width="10" height="10" stroke="white" strokeWidth="1.5" fill="none"/>
            <rect x="6" y="10" width="10" height="10" stroke="white" strokeWidth="1.5" fill="var(--bg-primary)"/>
            <rect x="10" y="0" width="10" height="10" stroke="var(--accent)" strokeWidth="1.5" fill="none"/>
          </svg>
          <span>wh1t3r4v3n</span>
        </Link>

        <nav className={`navbar__nav${open ? ' navbar__nav--open' : ''}`}>
          {links.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) => `navbar__link${isActive ? ' navbar__link--active' : ''}`}
              onClick={() => setOpen(false)}
            >
              {label}
            </NavLink>
          ))}

          {user ? (
            <div className="navbar__user">
              <Link to="/dashboard" className="navbar__username" onClick={() => setOpen(false)}>
                @{user.username}
              </Link>
              <Link to="/editor/new" className="navbar__cta" onClick={() => setOpen(false)}>
                + write
              </Link>
              <button className="navbar__logout" onClick={handleLogout}>logout</button>
            </div>
          ) : (
            <Link to="/login" className="navbar__cta" onClick={() => setOpen(false)}>
              login
            </Link>
          )}
        </nav>

        <button
          className={`navbar__burger${open ? ' navbar__burger--open' : ''}`}
          onClick={() => setOpen(!open)}
          aria-label="Toggle menu"
        >
          <span/><span/><span/>
        </button>
      </div>

      {open && <div className="navbar__overlay" onClick={() => setOpen(false)} />}
    </header>
  )
}
