import ReactMarkdown from 'react-markdown'
import 'highlight.js/styles/github-dark.css'
import { markdownPlugins, normalizeMarkdown } from './markdownConfig'

export default function MarkdownContent({ children, className = '' }) {
  return (
    <div className={`prose markdown-content ${className}`.trim()}>
      <ReactMarkdown {...markdownPlugins}>
        {normalizeMarkdown(children)}
      </ReactMarkdown>
    </div>
  )
}
