import { Link } from 'react-router-dom'
import './About.css'

const skills = {
  'Offensive Security': ['Penetration Testing', 'CTF Challenges', 'Web App Security', 'Network Security', 'Reverse Engineering', 'Exploit Development'],
  'Web Development': ['React', 'Django', 'REST APIs', 'JavaScript', 'TypeScript', 'CSS / SCSS'],
  'Programming': ['Python', 'JavaScript', 'Rust', 'C', 'Assembly', 'Lua'],
  'Tools': ['Burp Suite', 'Nmap', 'Metasploit', 'Ghidra', 'Wireshark', 'Git'],
}

const funFacts = [
  'I prefer dark terminals over dark themes',
  'CTF is my favorite weekend activity',
  'Coffee fuels the late-night debugging sessions',
  'I read CVE advisories for fun',
  "printf debugging is a valid strategy",
  'The best code is the code you delete',
]

export default function About() {
  return (
    <main className="about-page">
      <section className="about-hero container">
        <div className="about-hero__text">
          <p className="about-hero__greet">// about me</p>
          <h1><span className="accent">/</span>about-me</h1>
          <div className="about-bio">
            <p>
              Hey, I'm a security researcher and developer passionate about breaking things (with permission)
              and building them back stronger. This blog is where I document my findings, challenges, and learnings.
            </p>
            <p>
              My focus areas include web application security, CTF writeups, offensive security techniques,
              and full-stack development. I believe the best developers are those who understand both
              how to build and how to break systems.
            </p>
          </div>
          <div className="about-hero__actions">
            <Link to="/posts" className="btn btn--primary">Read posts --&gt;</Link>
            <Link to="/contact" className="btn btn--ghost">#contact</Link>
          </div>
        </div>
        <div className="about-hero__visual" aria-hidden>
          <div className="terminal">
            <div className="terminal__bar">
              <span/><span/><span/>
              <span className="terminal__title">whoami.sh</span>
            </div>
            <div className="terminal__body">
              <p><span className="t-prompt">$ </span>whoami</p>
              <p className="t-output">security researcher & developer</p>
              <p><span className="t-prompt">$ </span>cat skills.txt</p>
              <p className="t-output">[offensive security, web dev, CTF]</p>
              <p><span className="t-prompt">$ </span>ls ./blog/</p>
              <p className="t-output">writeups/ tutorials/ projects/</p>
              <p><span className="t-prompt">$</span><span className="t-cursor">_</span></p>
            </div>
          </div>
        </div>
      </section>

      <section className="skills-section container">
        <h2><span className="accent">#</span>skills</h2>
        <div className="skills-grid">
          {Object.entries(skills).map(([cat, items]) => (
            <div key={cat} className="skill-card">
              <h3 className="skill-card__title">{cat}</h3>
              <div className="skill-card__items">
                {items.map((s) => (
                  <span key={s} className="skill-item">{s}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="fun-facts container">
        <h2><span className="accent">#</span>fun-facts</h2>
        <div className="fun-facts__grid">
          {funFacts.map((f, i) => (
            <div key={i} className="fun-fact">
              <span className="fun-fact__num accent">0{i + 1}</span>
              <p>{f}</p>
            </div>
          ))}
        </div>
      </section>
    </main>
  )
}
