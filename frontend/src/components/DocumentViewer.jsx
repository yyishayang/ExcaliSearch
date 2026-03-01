// SPDX-FileCopyrightText: 2026 @albabsuarez
// SPDX-FileCopyrightText: 2026 @aslangallery
// SPDX-FileCopyrightText: 2026 @david598Uni
// SPDX-FileCopyrightText: 2026 @yyishayang
//
// SPDX-License-Identifier: AGPL-3.0-or-later

import { useState, useEffect, useRef } from 'react'
import { renderAsync } from 'docx-preview'
import * as XLSX from 'xlsx'
import Spreadsheet from "react-spreadsheet";
import { HiDatabase, HiPencilAlt, HiDocumentText, HiClock, HiDownload, HiX, HiTable, HiLightBulb, HiRefresh, HiChip, HiBeaker, HiLightningBolt } from 'react-icons/hi'

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
    const [regeneratingSummary, setRegeneratingSummary] = useState(false)
    const [showSummary, setShowSummary] = useState(true)
    const [showSummaryOptions, setShowSummaryOptions] = useState(false)
    const [summaryMethod, setSummaryMethod] = useState('auto')
    const [summaryAlgorithm, setSummaryAlgorithm] = useState('lsa')
    const [sentenceCount, setSentenceCount] = useState(5)
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

                {/* Summary Section */}
                {doc && doc.summary && showSummary && (
                    <div className="viewer__summary">
                        <div className="viewer__summary-header">
                            <div className="flex items-center gap-2">
                                <HiLightBulb className="text-yellow-500" size={22} />
                                <h3 className="text-lg font-semibold" style={{ marginBottom: 0 }}>Resumen automático</h3>
                                {/* Method badge - will show after regeneration with new API */}
                                {summaryMethod && (
                                    <span className={`summary-badge summary-badge--${summaryMethod}`} title={`Método: ${summaryMethod}`}>
                                        {summaryMethod === 'llm' && <HiChip size={12} />}
                                        {summaryMethod === 'extractive' && <HiLightningBolt size={12} />}
                                        {summaryMethod === 'auto' && <HiBeaker size={12} />}
                                        {summaryMethod}
                                    </span>
                                )}
                            </div>
                            <div className="flex gap-2">
                                <button
                                    className="btn btn--secondary btn--sm"
                                    onClick={() => setShowSummaryOptions(!showSummaryOptions)}
                                    disabled={regeneratingSummary}
                                    title="Opciones de resumen"
                                >
                                    <HiRefresh className={regeneratingSummary ? 'animate-spin' : ''} />
                                </button>
                                <button
                                    className="btn btn--secondary btn--sm"
                                    onClick={() => setShowSummary(false)}
                                    title="Cerrar resumen"
                                >
                                    <HiX />
                                </button>
                            </div>
                        </div>
                        
                        {/* Summary options panel */}
                        {showSummaryOptions && (
                            <div className="viewer__summary-options">
                                <div className="summary-info-box">
                                    <span className="summary-info-icon">💡</span>
                                    <div className="summary-info-text">
                                        <strong>Auto:</strong> Usa LLM si está disponible, sino extractivo<br/>
                                        <strong>Rápido:</strong> Extrae frases del documento (~1s)<br/>
                                        <strong>LLM:</strong> Reformula el contenido (mejor calidad, ~10-30s)
                                    </div>
                                </div>
                                
                                <div className="summary-option-group">
                                    <label className="summary-option-label">
                                        Método:
                                    </label>
                                    <div className="summary-method-buttons">
                                        <button
                                            className={`method-btn ${summaryMethod === 'auto' ? 'active' : ''}`}
                                            onClick={() => setSummaryMethod('auto')}
                                            title="Usa LLM si está disponible, sino extractivo"
                                        >
                                            <HiBeaker size={16} /> Auto
                                        </button>
                                        <button
                                            className={`method-btn ${summaryMethod === 'extractive' ? 'active' : ''}`}
                                            onClick={() => setSummaryMethod('extractive')}
                                            title="Rápido, extrae frases del documento"
                                        >
                                            <HiLightningBolt size={16} /> Rápido
                                        </button>
                                        <button
                                            className={`method-btn ${summaryMethod === 'llm' ? 'active' : ''}`}
                                            onClick={() => setSummaryMethod('llm')}
                                            title="Mejor calidad, requiere Ollama"
                                        >
                                            <HiChip size={16} /> LLM
                                        </button>
                                    </div>
                                </div>
                                
                                {summaryMethod === 'extractive' && (
                                    <div className="summary-option-group">
                                        <label className="summary-option-label">
                                            Algoritmo:
                                        </label>
                                        <select
                                            value={summaryAlgorithm}
                                            onChange={(e) => setSummaryAlgorithm(e.target.value)}
                                            className="summary-select"
                                        >
                                            <option value="lsa">LSA (rápido)</option>
                                            <option value="lexrank">LexRank (preciso)</option>
                                            <option value="textrank">TextRank (balanceado)</option>
                                        </select>
                                    </div>
                                )}
                                
                                <div className="summary-option-group">
                                    <label className="summary-option-label">
                                        Frases: {sentenceCount}
                                    </label>
                                    <input
                                        type="range"
                                        min="2"
                                        max="10"
                                        value={sentenceCount}
                                        onChange={(e) => setSentenceCount(Number(e.target.value))}
                                        className="summary-slider"
                                    />
                                </div>
                                
                                <button
                                    className="btn btn--primary btn--sm w-full"
                                    onClick={async () => {
                                        setShowSummaryOptions(false)
                                        setRegeneratingSummary(true)
                                        try {
                                            const res = await fetch(`${API_BASE}/summary/${docId}/regenerate`, {
                                                method: 'POST',
                                                headers: { 'Content-Type': 'application/json' },
                                                body: JSON.stringify({
                                                    method: summaryMethod,
                                                    sentence_count: sentenceCount,
                                                    algorithm: summaryAlgorithm,
                                                    language: 'spanish'
                                                })
                                            })
                                            if (res.ok) {
                                                const data = await res.json()
                                                setDoc(prev => ({ ...prev, summary: data.summary }))
                                                // Update the method indicator based on what was actually used
                                                if (data.method) {
                                                    setSummaryMethod(data.method)
                                                }
                                            } else {
                                                const error = await res.json()
                                                alert(`Error: ${error.detail || 'Failed to regenerate summary'}`)
                                            }
                                        } catch (err) {
                                            console.error('Failed to regenerate summary:', err)
                                            alert('Error: No se pudo regenerar el resumen')
                                        } finally {
                                            setRegeneratingSummary(false)
                                        }
                                    }}
                                    disabled={regeneratingSummary}
                                >
                                    {regeneratingSummary ? (
                                        <span className="flex items-center gap-2 justify-center">
                                            <HiRefresh className="animate-spin" /> Generando...
                                        </span>
                                    ) : (
                                        'Regenerar resumen'
                                    )}
                                </button>
                            </div>
                        )}
                        
                        <div className="viewer__summary-text">
                            {doc.summary}
                        </div>
                    </div>
                )}

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
