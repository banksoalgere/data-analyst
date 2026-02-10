'use client'

import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

interface MarkdownMessageProps {
  content: string
}

const SAFE_LINK_PREFIXES = ["http://", "https://", "mailto:", "tel:", "/", "#"]

function toSafeHref(href?: string): string {
  if (!href) return "#"
  const normalized = href.trim()
  if (!normalized) return "#"
  return SAFE_LINK_PREFIXES.some((prefix) => normalized.startsWith(prefix)) ? normalized : "#"
}

export function MarkdownMessage({ content }: MarkdownMessageProps) {
  if (!content.trim()) {
    return null
  }

  return (
    <div className="chat-markdown mb-3 text-sm leading-7 text-neutral-100">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => <h1 className="mb-3 text-xl font-semibold text-white">{children}</h1>,
          h2: ({ children }) => <h2 className="mb-3 text-lg font-semibold text-white">{children}</h2>,
          h3: ({ children }) => <h3 className="mb-2 text-base font-semibold text-white">{children}</h3>,
          p: ({ children }) => <p className="mb-3 leading-7 last:mb-0">{children}</p>,
          ul: ({ children }) => <ul className="mb-3 list-disc space-y-1 pl-6">{children}</ul>,
          ol: ({ children }) => <ol className="mb-3 list-decimal space-y-1 pl-6">{children}</ol>,
          li: ({ children }) => <li className="leading-7">{children}</li>,
          strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
          em: ({ children }) => <em className="text-neutral-200">{children}</em>,
          blockquote: ({ children }) => (
            <blockquote className="mb-3 border-l-2 border-neutral-600 pl-4 text-neutral-300">{children}</blockquote>
          ),
          hr: () => <hr className="my-4 border-neutral-700" />,
          a: ({ href, children }) => {
            const safeHref = toSafeHref(href)
            const isExternal = safeHref.startsWith("http://") || safeHref.startsWith("https://")
            return (
              <a
                href={safeHref}
                target={isExternal ? "_blank" : undefined}
                rel={isExternal ? "noopener noreferrer" : undefined}
                className="underline decoration-neutral-500 underline-offset-2 transition-colors hover:text-white"
              >
                {children}
              </a>
            )
          },
          pre: ({ children }) => (
            <pre className="mb-3 overflow-x-auto rounded border border-neutral-700 bg-black/40 p-3 text-xs leading-6 text-neutral-200">
              {children}
            </pre>
          ),
          code: ({ className, children }) => {
            if (className) {
              return <code className={`${className} font-mono`}>{children}</code>
            }
            return <code className="rounded bg-neutral-800/90 px-1.5 py-0.5 font-mono text-[0.85em]">{children}</code>
          },
          table: ({ children }) => (
            <div className="mb-3 overflow-x-auto rounded border border-neutral-700">
              <table className="min-w-full border-collapse text-left text-xs text-neutral-200">{children}</table>
            </div>
          ),
          thead: ({ children }) => <thead className="bg-neutral-900 text-neutral-200">{children}</thead>,
          th: ({ children }) => <th className="border-b border-neutral-700 px-3 py-2 font-semibold">{children}</th>,
          td: ({ children }) => <td className="border-b border-neutral-800 px-3 py-2 align-top">{children}</td>,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
