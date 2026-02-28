import { HiEye, HiDownload, HiTrash } from 'react-icons/hi'
import { FaFilePdf, FaFileWord, FaFileAlt } from 'react-icons/fa'
import { BiTargetLock } from 'react-icons/bi'

const API_BASE = '/api'

/**
 * Converts Whoosh UPPERCASE highlights into <mark> elements.
 * Whoosh UppercaseFormatter wraps matches in UPPERCASE.
 * We detect sequences of uppercase words surrounded by lowercase text.
 *
 * Since Whoosh returns highlights with UPPERCASED matched terms,
 * we parse the snippet to find them and wrap them in <mark> tags.
 */
function formatSnippet(snippet, query) {
    if (!snippet || !query) return snippet || ''

    // Build a regex from query terms to find matches (case-insensitive)
    const terms = query
        .split(/\s+/)
        .filter(t => t.length > 1)
        .map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))

    if (terms.length === 0) return snippet

    const pattern = new RegExp(`(${terms.join('|')})`, 'gi')
    const parts = snippet.split(pattern)

    return parts.map((part, i) => {
        if (pattern.test(part)) {
            return <mark key={i} className="highlight-mark">{part}</mark>
        }
        // Reset lastIndex since we reuse the regex
        pattern.lastIndex = 0
        return part
    })
}

export default function ResultsList({ results, query, onSelect, onDelete }) {
    if (!results || results.length === 0) {
        return null
    }

    const typeIcons = {
        pdf: <FaFilePdf className="text-red-500" />,
        txt: <FaFileAlt className="text-green-500" />,
        docx: <FaFileWord className="text-blue-500" />
    }

    return (
        <div className="results-list">
            {results.map((result) => (
                <div
                    key={result.doc_id}
                    className="result-card"
                    onClick={() => onSelect(result.doc_id)}
                >
                    <div className="result-card__header">
                        <div className="result-card__title">
                            <span className={`result-card__type result-card__type--${result.file_type}`}>
                                {result.file_type.toUpperCase()}
                            </span>
                            <span className="flex items-center gap-2">
                                {typeIcons[result.file_type] || <FaFileAlt />}
                                {result.original_name}
                            </span>
                        </div>
                        <span className="result-card__score flex items-center gap-1">
                            <BiTargetLock className="text-accent" /> {result.score.toFixed(2)}
                        </span>
                    </div>

                    <div className="result-card__snippet">
                        {formatSnippet(result.snippet, query)}
                    </div>

                    <div className="result-card__actions">
                        <button
                            className="btn btn--primary"
                            onClick={(e) => {
                                e.stopPropagation()
                                onSelect(result.doc_id)
                            }}
                        >
                            <HiEye className="mr-1" /> View
                        </button>
                        <a
                            className="btn btn--ghost"
                            href={`${API_BASE}/documents/${result.doc_id}/download`}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <HiDownload className="mr-1" /> Download
                        </a>
                        <button
                            className="btn btn--danger"
                            onClick={(e) => {
                                e.stopPropagation()
                                onDelete(result.doc_id)
                            }}
                        >
                            <HiTrash />
                        </button>
                    </div>
                </div>
            ))}
        </div>
    )
}
