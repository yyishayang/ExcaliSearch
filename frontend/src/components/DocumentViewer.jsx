import { useState, useEffect } from 'react'

const API_BASE = '/api'

/**
 * Highlight query terms within document text.
 */
function highlightText(text, query) {
    if (!text || !query) return text || ''

    const terms = query
        .split(/\s+/)
        .filter(t => t.length > 1)
        .map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))

    if (terms.length === 0) return text

    const pattern = new RegExp(`(${terms.join('|')})`, 'gi')
    const parts = text.split(pattern)

    return parts.map((part, i) => {
        if (pattern.test(part)) {
            return <mark key={i} className="highlight-mark">{part}</mark>
        }
        pattern.lastIndex = 0
        return part
    })
}

function formatFileSize(bytes) {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDate(isoDate) {
    try {
        return new Date(isoDate).toLocaleString()
    } catch {
        return isoDate
    }
}

export default function DocumentViewer({ docId, query, onClose }) {
    const [doc, setDoc] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        if (!docId) return

        const fetchDoc = async () => {
            setLoading(true)
            setError(null)
            try {
                const res = await fetch(`${API_BASE}/documents/${docId}`)
                if (!res.ok) throw new Error('Failed to load document')
                const text = await res.text()
                const data = JSON.parse(text)
                setDoc(data)
            } catch (err) {
                setError(err.message)
            } finally {
                setLoading(false)
            }
        }

        fetchDoc()
    }, [docId])

    // Close on Escape key
    useEffect(() => {
        const handleKey = (e) => {
            if (e.key === 'Escape') onClose()
        }
        window.addEventListener('keydown', handleKey)
        return () => window.removeEventListener('keydown', handleKey)
    }, [onClose])

    if (!docId) return null

    return (
        <div className="viewer-overlay" onClick={onClose}>
            <div className="viewer" onClick={(e) => e.stopPropagation()}>
                <div className="viewer__header">
                    <div>
                        <div className="viewer__title">
                            <span className={`result-card__type result-card__type--${doc?.file_type || ''}`}>
                                {doc?.file_type?.toUpperCase() || '...'}
                            </span>
                            {doc?.original_name || 'Loading...'}
                        </div>
                        {doc && (
                            <div className="viewer__meta">
                                <span>📁 {formatFileSize(doc.file_size)}</span>
                                <span>📝 {(doc.word_count || 0).toLocaleString()} words</span>
                                {doc.page_count && <span>📄 {doc.page_count} pages</span>}
                                <span>📅 {formatDate(doc.upload_date)}</span>
                            </div>
                        )}
                    </div>
                    <div className="viewer__actions">
                        {doc && (
                            <a
                                className="btn btn--primary"
                                href={`${API_BASE}/documents/${docId}/download`}
                                target="_blank"
                                rel="noopener noreferrer"
                            >
                                ⬇ Download
                            </a>
                        )}
                        <button className="viewer__close" onClick={onClose} title="Close">
                            ✕
                        </button>
                    </div>
                </div>

                <div className="viewer__content">
                    {loading && (
                        <div className="empty-state">
                            <div className="spinner" />
                            <p className="empty-state__text" style={{ marginTop: '1rem' }}>Loading document…</p>
                        </div>
                    )}
                    {error && (
                        <div className="empty-state">
                            <div className="empty-state__icon">⚠️</div>
                            <p className="empty-state__text">{error}</p>
                        </div>
                    )}
                    {doc && !loading && (
                        <div className="viewer__text">
                            {query ? highlightText(doc.content, query) : doc.content}
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
