'use client'

import dynamic from 'next/dynamic'
import React from 'react'

const ReactMarkdown = dynamic(() => import('react-markdown').then((m) => m.default), {
  ssr: false,
  loading: () => <div className="markdown-content markdown-content--loading" aria-hidden="true" />
})

const MarkdownRenderer = ({ content }) => {
  const markdown =
    typeof content === 'string' ? content : content == null ? '' : String(content)
  return (
    <div className="markdown-content">
      <ReactMarkdown>{markdown}</ReactMarkdown>
      <style jsx global>{`
        .markdown-content p {
          margin-bottom: 1rem;
          line-height: 1.6;
        }
        .markdown-content ul, .markdown-content ol {
          margin-bottom: 1rem;
          padding-left: 1.5rem;
        }
        .markdown-content li {
          margin-bottom: 0.5rem;
        }
        .markdown-content strong {
          color: var(--gold-primary, #D4AF37);
        }
      `}</style>
    </div>
  );
};

export default MarkdownRenderer;
