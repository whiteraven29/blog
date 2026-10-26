import { useEffect, useState } from 'react'
import './TableOfContents.css'

function slugify(text) {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
}

export default function TableOfContents({ contentRef, content }) {
  const [headings, setHeadings] = useState([])
  const [activeId, setActiveId] = useState(null)

  // Collect headings from the rendered markdown and give each one an id.
  useEffect(() => {
    const root = contentRef.current
    if (!root) return

    const used = new Set()
    const items = [...root.querySelectorAll('h2, h3')].map((el) => {
      let id = el.id || slugify(el.textContent) || 'section'
      for (let n = 2; used.has(id); n++) id = `${slugify(el.textContent)}-${n}`
      used.add(id)
      el.id = id
      return { id, text: el.textContent, level: el.tagName === 'H3' ? 3 : 2 }
    })

    setHeadings(items)
    setActiveId(items[0]?.id ?? null)
  }, [contentRef, content])

  // Highlight the last heading that has scrolled past the top of the viewport.
  useEffect(() => {
    if (!headings.length) return

    const onScroll = () => {
      let current = headings[0].id
      for (const { id } of headings) {
        const el = document.getElementById(id)
        if (el && el.getBoundingClientRect().top <= 120) current = id
      }
      setActiveId(current)
    }

    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [headings])

  if (headings.length < 2) return null

  return (
    <nav className="toc" aria-label="Table of contents">
      <h4>On this page</h4>
      <ul>
        {headings.map(({ id, text, level }) => (
          <li key={id} className={`toc__item toc__item--h${level}`}>
            <a
              href={`#${id}`}
              className={id === activeId ? 'toc__link toc__link--active' : 'toc__link'}
              aria-current={id === activeId ? 'location' : undefined}
            >
              {text}
            </a>
          </li>
        ))}
      </ul>
    </nav>
  )
}
