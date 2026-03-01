import { useState, useRef } from 'react'
import { HiUpload, HiCloudUpload, HiCheckCircle, HiExclamationCircle, HiX, HiViewGrid, HiDocument } from 'react-icons/hi'

const API_BASE = '/api'

export default function UploadPanel({ onUploadComplete, compact = false }) {
    const [isDragging, setIsDragging] = useState(false)
    const [uploading, setUploading] = useState(false)
    const [progress, setProgress] = useState(0)
    const [message, setMessage] = useState(null) // { type: 'success'|'error', text }
    const [batchMode, setBatchMode] = useState(false)
    const [batchFiles, setBatchFiles] = useState([]) // Array of files with status
    const [batchProgress, setBatchProgress] = useState(null) // { successful, failed, total }
    const fileInputRef = useRef(null)

    const handleDragOver = (e) => {
        e.preventDefault()
        setIsDragging(true)
    }

    const handleDragLeave = (e) => {
        e.preventDefault()
        setIsDragging(false)
    }

    const handleDrop = (e) => {
        e.preventDefault()
        setIsDragging(false)
        const files = Array.from(e.dataTransfer.files)
        if (files.length > 0) {
            if (batchMode || files.length > 1) {
                handleBatchFiles(files)
            } else {
                uploadFile(files[0])
            }
        }
    }

    const handleFileSelect = (e) => {
        const files = Array.from(e.target.files)
        if (files.length > 0) {
            if (batchMode || files.length > 1) {
                handleBatchFiles(files)
            } else {
                uploadFile(files[0])
            }
        }
    }

    const handleBatchFiles = (files) => {
        const allowed = ['pdf', 'txt', 'docx', 'csv', 'xlsx']
        const validFiles = files.filter(file => {
            const ext = file.name.split('.').pop().toLowerCase()
            return allowed.includes(ext)
        })

        if (validFiles.length === 0) {
            setMessage({ type: 'error', text: 'No valid files selected. Use: PDF, TXT, DOCX, CSV, XLSX' })
            return
        }

        if (validFiles.length < files.length) {
            setMessage({
                type: 'warning',
                text: `${files.length - validFiles.length} file(s) skipped (invalid format)`
            })
        }

        setBatchFiles(validFiles.map(f => ({
            file: f,
            status: 'pending',
            name: f.name
        })))
        uploadBatch(validFiles)
    }

    const removeBatchFile = (index) => {
        setBatchFiles(prev => prev.filter((_, i) => i !== index))
    }

    const clearBatch = () => {
        setBatchFiles([])
        setBatchProgress(null)
        setMessage(null)
    }

    const uploadBatch = async (files) => {
        setUploading(true)
        setBatchProgress({ successful: 0, failed: 0, total: files.length })
        setMessage(null)

        try {
            const formData = new FormData()
            files.forEach(file => {
                formData.append('files', file)
            })

            const res = await fetch(`${API_BASE}/documents/upload/batch`, {
                method: 'POST',
                body: formData,
            })

            const text = await res.text()
            let data
            try {
                data = JSON.parse(text)
            } catch {
                throw new Error('Invalid response from server')
            }

            if (!res.ok) {
                throw new Error(data.detail || `Upload failed (${res.status})`)
            }

            // Update individual file statuses
            setBatchFiles(prev => prev.map(item => {
                const result = data.results.find(r => r.filename === item.name)
                if (result) {
                    return {
                        ...item,
                        status: result.status,
                        error: result.error,
                        doc_id: result.doc_id
                    }
                }
                return item
            }))

            setBatchProgress({
                successful: data.successful,
                failed: data.failed,
                total: data.total_files
            })

            setMessage({
                type: data.failed === 0 ? 'success' : 'warning',
                text: `Batch upload complete: ${data.successful} successful, ${data.failed} failed`
            })

            if (onUploadComplete && data.successful > 0) {
                onUploadComplete({ batch: true, ...data })
            }

            // Auto-clear success after 5 seconds
            if (data.failed === 0) {
                setTimeout(() => {
                    clearBatch()
                }, 5000)
            }

        } catch (err) {
            setMessage({ type: 'error', text: err.message })
            setBatchFiles(prev => prev.map(item => ({
                ...item,
                status: 'error',
                error: err.message
            })))
        } finally {
            setUploading(false)
            // Reset input
            if (fileInputRef.current) fileInputRef.current.value = ''
        }
    }

    const uploadFile = async (file) => {
        const allowed = ['pdf', 'txt', 'docx', 'csv', 'xlsx']
        const ext = file.name.split('.').pop().toLowerCase()
        if (!allowed.includes(ext)) {
            setMessage({ type: 'error', text: `File type .${ext} not supported. Use: PDF, TXT, DOCX, CSV, XLSX` })
            return
        }

        setUploading(true)
        setProgress(0)
        setMessage(null)

        // Simulate progress since fetch doesn't support upload progress natively
        const progressInterval = setInterval(() => {
            setProgress(prev => Math.min(prev + 15, 90))
        }, 200)

        try {
            const formData = new FormData()
            formData.append('file', file)

            const res = await fetch(`${API_BASE}/documents/upload`, {
                method: 'POST',
                body: formData,
            })

            clearInterval(progressInterval)
            setProgress(100)

            // Read response body as text first, then try to parse as JSON
            const text = await res.text()
            let data
            try {
                data = JSON.parse(text)
            } catch {
                // Response is not valid JSON
                if (!res.ok) {
                    throw new Error(`Server error (${res.status}): ${text.substring(0, 200)}`)
                }
                throw new Error('Invalid response from server')
            }

            if (!res.ok) {
                throw new Error(data.detail || `Upload failed (${res.status})`)
            }

            setMessage({ type: 'success', text: `"${data.original_name}" uploaded and indexed successfully` })

            // Auto-hide success message after 3 seconds
            setTimeout(() => {
                setMessage(current => current?.type === 'success' ? null : current)
            }, 3000)

            if (onUploadComplete) {
                onUploadComplete(data)
            }
        } catch (err) {
            clearInterval(progressInterval)
            setMessage({ type: 'error', text: err.message })
        } finally {
            setUploading(false)
            setTimeout(() => setProgress(0), 1000)
            // Reset input
            if (fileInputRef.current) fileInputRef.current.value = ''
        }
    }

    return (
        <div className={`upload-panel ${compact ? 'upload-panel--compact' : ''}`}>
            {!compact && (
                <div className="upload-mode-toggle">
                    <button
                        className={`mode-toggle-btn ${!batchMode ? 'active' : ''}`}
                        onClick={() => {
                            setBatchMode(false)
                            clearBatch()
                        }}
                        disabled={uploading}
                    >
                        <HiDocument size={18} />
                        Single
                    </button>
                    <button
                        className={`mode-toggle-btn ${batchMode ? 'active' : ''}`}
                        onClick={() => setBatchMode(true)}
                        disabled={uploading}
                    >
                        <HiViewGrid size={18} />
                        Batch
                    </button>
                </div>
            )}

            <div
                className={`upload-zone ${isDragging ? 'upload-zone--active' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                title={batchMode ? "Sube múltiples documentos" : "Sube un documento nuevo"}
            >
                <div className="upload-zone__icon">
                    <img
                        src={
                            message?.type === 'error' ? "/arturofail.webp" :
                                message?.type === 'success' ? "/arturowin.webp" :
                                    "/arturoIdle.webp"
                        }
                        alt={
                            message?.type === 'error' ? "Arturo Error" :
                                message?.type === 'success' ? "Arturo Success" :
                                    "Arturo"
                        }
                        className={compact ? "upload-zone__arturo--compact" : "upload-zone__arturo"}
                    />
                </div>
                {!compact && (
                    <>
                        <div className="upload-zone__text">
                            Drag & drop {batchMode ? 'files' : 'a file'} here or <strong>click to browse</strong>
                        </div>
                        <div className="upload-zone__formats">
                            {batchMode ? 'Select multiple files at once' : 'Supported formats: PDF, TXT, DOCX, CSV, XLSX'}
                        </div>
                    </>
                )}
                {compact && (
                    <div className="upload-zone__text">
                        <strong>Subir archivo</strong>
                    </div>
                )}
                <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.txt,.docx,.csv,.xlsx"
                    multiple={batchMode}
                    onChange={handleFileSelect}
                />
            </div>

            {batchFiles.length > 0 && !uploading && (
                <div className="batch-files-list">
                    <div className="batch-files-header">
                        <span>{batchFiles.length} file(s) selected</span>
                        <button className="btn-clear" onClick={clearBatch}>
                            <HiX size={16} /> Clear all
                        </button>
                    </div>
                    <div className="batch-files-items">
                        {batchFiles.map((item, idx) => (
                            <div key={idx} className="batch-file-item">
                                <span className="batch-file-name">{item.name}</span>
                                <button
                                    className="btn-remove"
                                    onClick={(e) => {
                                        e.stopPropagation()
                                        removeBatchFile(idx)
                                    }}
                                >
                                    <HiX size={14} />
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Batch upload progress */}
            {batchFiles.length > 0 && uploading && (
                <div className="batch-upload-progress">
                    <div className="batch-progress-header">
                        <span>Uploading {batchFiles.length} files...</span>
                    </div>
                </div>
            )}

            {/* Batch results */}
            {batchFiles.length > 0 && !uploading && batchProgress && (
                <div className="batch-results">
                    <div className="batch-results-summary">
                        <div className="summary-item success">
                            <HiCheckCircle size={20} />
                            <span>{batchProgress.successful} successful</span>
                        </div>
                        <div className="summary-item failed">
                            <HiExclamationCircle size={20} />
                            <span>{batchProgress.failed} failed</span>
                        </div>
                    </div>
                    <div className="batch-results-items">
                        {batchFiles.map((item, idx) => (
                            <div key={idx} className={`batch-result-item ${item.status}`}>
                                <span className="result-icon">
                                    {item.status === 'success' ? (
                                        <HiCheckCircle size={16} />
                                    ) : (
                                        <HiExclamationCircle size={16} />
                                    )}
                                </span>
                                <span className="result-name">{item.name}</span>
                                {item.error && <span className="result-error">{item.error}</span>}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Single file upload progress */}
            {uploading && !batchFiles.length && (
                <div className="upload-progress">
                    <div className="spinner" />
                    <div className="upload-progress__bar-container">
                        <div
                            className="upload-progress__bar"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                    <span className="upload-progress__text">{progress}%</span>
                </div>
            )}

            {/* Messages */}
            {message && !batchProgress && (
                <div className={`upload-message upload-message--${message.type}`}>
                    <span>
                        {message.type === 'success' ? (
                            <HiCheckCircle size={18} />
                        ) : (
                            <HiExclamationCircle size={18} />
                        )}
                    </span>
                    <span>{message.text}</span>
                </div>
            )}
        </div>
    )
}
