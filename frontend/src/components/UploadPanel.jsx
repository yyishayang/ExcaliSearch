import { useState, useRef } from 'react'
import { HiUpload, HiCloudUpload, HiCheckCircle, HiExclamationCircle } from 'react-icons/hi'

const API_BASE = '/api'

export default function UploadPanel({ onUploadComplete, compact = false }) {
    const [isDragging, setIsDragging] = useState(false)
    const [uploading, setUploading] = useState(false)
    const [progress, setProgress] = useState(0)
    const [message, setMessage] = useState(null) // { type: 'success'|'error', text }
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
        const files = e.dataTransfer.files
        if (files.length > 0) {
            uploadFile(files[0])
        }
    }

    const handleFileSelect = (e) => {
        if (e.target.files.length > 0) {
            uploadFile(e.target.files[0])
        }
    }

    const uploadFile = async (file) => {
        const allowed = ['pdf', 'txt', 'docx']
        const ext = file.name.split('.').pop().toLowerCase()
        if (!allowed.includes(ext)) {
            setMessage({ type: 'error', text: `File type .${ext} not supported. Use: PDF, TXT, DOCX` })
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
            <div
                className={`upload-zone ${isDragging ? 'upload-zone--active' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                title="Sube un documento nuevo"
            >
                <div className="upload-zone__icon">
                    {compact ? (
                        <HiUpload size={24} className="mx-auto" />
                    ) : (
                        <HiCloudUpload size={48} className="mx-auto opacity-70" />
                    )}
                </div>
                {!compact && (
                    <>
                        <div className="upload-zone__text">
                            Drag & drop a file here or <strong>click to browse</strong>
                        </div>
                        <div className="upload-zone__formats">
                            Supported formats: PDF, TXT, DOCX
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
                    accept=".pdf,.txt,.docx"
                    onChange={handleFileSelect}
                />
            </div>

            {uploading && (
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

            {message && (
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
