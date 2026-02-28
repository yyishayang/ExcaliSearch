import { useState, useEffect, useRef } from 'react'
import { renderAsync } from 'docx-preview'
import * as XLSX from 'xlsx'
import Spreadsheet from "react-spreadsheet";
import { HiDatabase, HiPencilAlt, HiDocumentText, HiClock, HiDownload, HiX, HiTable } from 'react-icons/hi'

const API_BASE = '/api'

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
    const [spreadsheetData, setSpreadsheetData] = useState(null) // { sheetNames: [], sheets: { name: [[cell]] } }
    const [activeSheet, setActiveSheet] = useState(0)
    const docxContainerRef = useRef(null)

    // Fetch document metadata (and render DOCX if applicable)
    useEffect(() => {
        if (!docId) return

        const fetchDoc = async () => {
            setLoading(true)
            setError(null)
            setSpreadsheetData(null)
            try {
                const res = await fetch(`${API_BASE}/documents/${docId}`)
                if (!res.ok) throw new Error('Failed to load document')
                const data = await res.json()
                setDoc(data)

                // If DOCX, fetch binary and render with docx-preview
                if (data.file_type === 'docx') {
                    const fileRes = await fetch(`${API_BASE}/documents/${docId}/download?inline=true`)
                    if (!fileRes.ok) throw new Error('Failed to fetch DOCX file')
                    const arrayBuffer = await fileRes.arrayBuffer()
                    // Render after state update gives us the container div
                    setTimeout(() => {
                        if (docxContainerRef.current) {
                            docxContainerRef.current.innerHTML = ''
                            renderAsync(arrayBuffer, docxContainerRef.current, null, {
                                className: 'docx-preview',
                                inWrapper: true,
                                ignoreWidth: false,
                                ignoreHeight: false,
                                ignoreFonts: false,
                                breakPages: true,
                                renderHeaders: true,
                                renderFooters: true,
                                renderFootnotes: true,
                            })
                        }
                    }, 50)
                }

                // If spreadsheet (xlsx, csv), fetch binary and parse with XLSX
                if (data.file_type === 'xlsx' || data.file_type === 'csv') {
                    const fileRes = await fetch(`${API_BASE}/documents/${docId}/download?inline=true`)
                    if (!fileRes.ok) throw new Error('Failed to fetch spreadsheet file')
                    const arrayBuffer = await fileRes.arrayBuffer()
                    const workbook = XLSX.read(arrayBuffer, { type: 'array' })

                    const sheetsMap = {}
                    workbook.SheetNames.forEach(name => {
                        const sheet = workbook.Sheets[name]
                        const jsonData = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: "" })
                        // Transform to react-spreadsheet format
                        sheetsMap[name] = jsonData.map(row =>
                            row.map(cell => ({ value: String(cell) }))
                        )
                    })

                    setSpreadsheetData({
                        sheetNames: workbook.SheetNames,
                        sheets: sheetsMap
                    })
                    setActiveSheet(0)
                }
            } catch (err) {
                setError(err.message)
            } finally {
                setLoading(false)
            }
        }

        fetchDoc()
    }, [docId])

    useEffect(() => {
        const handleKey = (e) => {
            if (e.key === 'Escape') onClose()
        }
        window.addEventListener('keydown', handleKey)
        return () => window.removeEventListener('keydown', handleKey)
    }, [onClose])

    const renderSpreadsheet = () => {
        if (!spreadsheetData) return null;

        const sheetName = spreadsheetData.sheetNames[activeSheet];
        const data = spreadsheetData.sheets[sheetName];

        return (
            <div className="viewer__spreadsheet-comp">
                {spreadsheetData.sheetNames.length > 1 && (
                    <div className="viewer__spreadsheet-tabs">
                        {spreadsheetData.sheetNames.map((name, i) => (
                            <button
                                key={name}
                                className={`viewer__spreadsheet-tab ${activeSheet === i ? 'viewer__spreadsheet-tab--active' : ''}`}
                                onClick={() => setActiveSheet(i)}
                            >
                                <HiTable /> {name}
                            </button>
                        ))}
                    </div>
                )}
                <div className="viewer__spreadsheet-grid">
                    <Spreadsheet data={data} />
                </div>
            </div>
        );
    };

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
                                <span className="flex items-center gap-1"><HiDatabase /> {formatFileSize(doc.file_size)}</span>
                                <span className="flex items-center gap-1"><HiPencilAlt /> {(doc.word_count || 0).toLocaleString()} words</span>
                                {doc.page_count && <span className="flex items-center gap-1"><HiDocumentText /> {doc.page_count} pages</span>}
                                <span className="flex items-center gap-1"><HiClock /> {formatDate(doc.upload_date)}</span>
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
                                <HiDownload className="mr-1" /> Download
                            </a>
                        )}
                        <button className="viewer__close" onClick={onClose} title="Close">
                            <HiX size={24} />
                        </button>
                    </div>
                </div>

                <div className={`viewer__content ${doc?.file_type === 'pdf' ? 'viewer__content--pdf' : ''}`}>
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
                        doc.file_type === 'pdf' ? (
                            <iframe
                                src={`${API_BASE}/documents/${docId}/download?inline=true${query ? `#search=${encodeURIComponent(query)}` : ''}`}
                                className="viewer__pdf-iframe"
                                title={doc.original_name}
                            />
                        ) : doc.file_type === 'docx' ? (
                            <div ref={docxContainerRef} className="viewer__docx-container" />
                        ) : (doc.file_type === 'xlsx' || doc.file_type === 'csv') ? (
                            renderSpreadsheet()
                        ) : (
                            <div className="viewer__text">
                                {query ? highlightText(doc.content, query) : doc.content}
                            </div>
                        )
                    )}
                </div>
            </div>
        </div>
    )
}
