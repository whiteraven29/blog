import { Link } from 'react-router-dom'
import './Footer.css'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer__inner container">
        <div className="footer__left">
          <Link to="/" className="footer__logo">
            <svg width="16" height="16" viewBox="0 0 20 20" fill="none">
              <rect x="0" y="6" width="10" height="10" stroke="white" strokeWidth="1.5" fill="none"/>
              <rect x="6" y="10" width="10" height="10" stroke="white" strokeWidth="1.5" fill="var(--bg-secondary)"/>
              <rect x="10" y="0" width="10" height="10" stroke="var(--accent)" strokeWidth="1.5" fill="none"/>
            </svg>
            wh1t3r4v3n
          </Link>
          <p className="footer__tagline">Offensive security, web dev & programming writeups</p>
        </div>

        <div className="footer__links">
          <div className="footer__col">
            <span className="footer__col-title">Navigate</span>
            <Link to="/">#home</Link>
            <Link to="/posts">#posts</Link>
            <Link to="/categories">#categories</Link>
          </div>
          <div className="footer__col">
            <span className="footer__col-title">More</span>
            <Link to="/about">#about</Link>
            <Link to="/contact">#contact</Link>
          </div>
        </div>
      </div>
      <div className="footer__bottom container">
        <span>© {new Date().getFullYear()} wh1t3r4v3n. All rights reserved.</span>
        <span className="footer__made">cybersecurity enthusiast</span>
      </div>
    </footer>
  )
}
