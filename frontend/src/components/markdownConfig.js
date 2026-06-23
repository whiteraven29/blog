import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'

export const markdownPlugins = {
  remarkPlugins: [remarkGfm],
  rehypePlugins: [rehypeHighlight],
}

export function normalizeMarkdown(value) {
  const markdown = String(value || '')

  // Recover content imported or stored with escaped line breaks.
  if (!markdown.includes('\n') && markdown.includes('\\n')) {
    return markdown.replace(/\\r\\n|\\n/g, '\n')
  }

  return markdown
}
