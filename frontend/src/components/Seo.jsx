import { useEffect } from 'react'

const SITE_NAME = 'wh1t3r4v3n'
const DEFAULT_DESCRIPTION = 'Offensive security, CTF, web development, and programming writeups.'

function setMeta(selector, attributes) {
  let element = document.head.querySelector(selector)
  if (!element) {
    element = document.createElement('meta')
    document.head.appendChild(element)
  }
  Object.entries(attributes).forEach(([name, value]) => element.setAttribute(name, value))
}

export default function Seo({
  title,
  description = DEFAULT_DESCRIPTION,
  image,
  type = 'website',
  jsonLd,
}) {
  useEffect(() => {
    const pageTitle = title ? `${title} | ${SITE_NAME}` : `${SITE_NAME} Blog`
    const url = window.location.href

    document.title = pageTitle
    setMeta('meta[name="description"]', { name: 'description', content: description })
    setMeta('meta[property="og:title"]', { property: 'og:title', content: pageTitle })
    setMeta('meta[property="og:description"]', { property: 'og:description', content: description })
    setMeta('meta[property="og:type"]', { property: 'og:type', content: type })
    setMeta('meta[property="og:url"]', { property: 'og:url', content: url })
    setMeta('meta[name="twitter:card"]', {
      name: 'twitter:card',
      content: image ? 'summary_large_image' : 'summary',
    })
    setMeta('meta[name="twitter:title"]', { name: 'twitter:title', content: pageTitle })
    setMeta('meta[name="twitter:description"]', { name: 'twitter:description', content: description })

    if (image) {
      setMeta('meta[property="og:image"]', { property: 'og:image', content: image })
      setMeta('meta[name="twitter:image"]', { name: 'twitter:image', content: image })
    }

    let canonical = document.head.querySelector('link[rel="canonical"]')
    if (!canonical) {
      canonical = document.createElement('link')
      canonical.rel = 'canonical'
      document.head.appendChild(canonical)
    }
    canonical.href = url.split(/[?#]/)[0]

    const oldSchema = document.head.querySelector('#page-json-ld')
    oldSchema?.remove()
    if (jsonLd) {
      const schema = document.createElement('script')
      schema.id = 'page-json-ld'
      schema.type = 'application/ld+json'
      schema.text = JSON.stringify(jsonLd)
      document.head.appendChild(schema)
    }
  }, [description, image, jsonLd, title, type])

  return null
}
