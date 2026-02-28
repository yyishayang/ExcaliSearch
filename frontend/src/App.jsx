import { useState, useEffect, useCallback } from 'react'
import './App.css'
import UploadPanel from './components/UploadPanel'
import SearchBar from './components/SearchBar'
import ResultsList from './components/ResultsList'
import DocumentViewer from './components/DocumentViewer'

const API_BASE = '/api'

function formatFileSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatDate(isoDate) {
  try {
    const d = new Date(isoDate)
    return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch {
    return isoDate
  }
}

function App() {
  const [documents, setDocuments] = useState([])
  const [searchResults, setSearchResults] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedDocId, setSelectedDocId] = useState(null)
  const [loading, setLoading] = useState(false)

  // Load document list
  const loadDocuments = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/documents`)
      if (res.ok) {
        const text = await res.text()
        try {
          const data = JSON.parse(text)
          setDocuments(Array.isArray(data) ? data : [])
        } catch {
          console.error('Invalid JSON from /documents')
        }
      }
    } catch (err) {
      console.error('Failed to load documents:', err)
    }
  }, [])

  useEffect(() => {
    loadDocuments()
  }, [loadDocuments])

  // Search handler
  const handleSearch = useCallback(async (query) => {
    setSearchQuery(query)

    if (!query) {
      setSearchResults(null)
      return
    }

    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}`)
      if (res.ok) {
        const text = await res.text()
        try {
          const data = JSON.parse(text)
          setSearchResults(data.results || [])
        } catch {
          console.error('Invalid JSON from /search')
        }
      }
    } catch (err) {
      console.error('Search error:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  // Delete handler
  const handleDelete = useCallback(async (docId) => {
    if (!confirm('Are you sure you want to delete this document?')) return

    try {
      const res = await fetch(`${API_BASE}/documents/${docId}`, { method: 'DELETE' })
      if (res.ok) {
        loadDocuments()
        // Remove from search results if present
        if (searchResults) {
          setSearchResults(prev => prev.filter(r => r.doc_id !== docId))
        }
      }
    } catch (err) {
      console.error('Delete error:', err)
    }
  }, [searchResults, loadDocuments])

  // After upload, refresh list
  const handleUploadComplete = useCallback(() => {
    loadDocuments()
  }, [loadDocuments])

  const typeIcons = { pdf: '📕', txt: '📝', docx: '📘' }

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header__logo">
          <span className="header__icon">⚔️</span>
          <h1 className="header__title">ExcaliSearch</h1>
        </div>
        <p className="header__subtitle">Upload, index and search your documents instantly</p>
      </header>

      {/* Upload */}
      <UploadPanel onUploadComplete={handleUploadComplete} />

      {/* Search */}
      <SearchBar
        onSearch={handleSearch}
        resultCount={searchResults ? searchResults.length : null}
      />

      {/* Loading */}
      {loading && (
        <div className="empty-state">
          <div className="spinner" />
        </div>
      )}

      {/* Search Results */}
      {searchResults && !loading && (
        <>
          {searchResults.length > 0 ? (
            <ResultsList
              results={searchResults}
              query={searchQuery}
              onSelect={(docId) => setSelectedDocId(docId)}
              onDelete={handleDelete}
            />
          ) : (
            <div className="empty-state">
              <div className="empty-state__icon">🔍</div>
              <p className="empty-state__text">No results found for "{searchQuery}"</p>
            </div>
          )}
        </>
      )}

      {/* Document List (when not searching) */}
      {!searchResults && !loading && documents.length > 0 && (
        <div className="documents-section">
          <h2 className="documents-section__title">
            📚 Your Documents ({documents.length})
          </h2>
          <div className="doc-grid">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="doc-card"
                onClick={() => setSelectedDocId(doc.id)}
              >
                <div className="doc-card__icon">{typeIcons[doc.file_type] || '📄'}</div>
                <div className="doc-card__name">{doc.original_name}</div>
                <div className="doc-card__meta">
                  <span>{formatFileSize(doc.file_size || 0)}</span>
                  <span>{(doc.word_count || 0).toLocaleString()} words</span>
                  <span>{formatDate(doc.upload_date)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!searchResults && !loading && documents.length === 0 && (
        <div className="empty-state">
          <div className="empty-state__icon">📂</div>
          <p className="empty-state__text">No documents yet. Upload your first file above!</p>
        </div>
      )}

      {/* Document Viewer Modal */}
      {selectedDocId && (
        <DocumentViewer
          docId={selectedDocId}
          query={searchQuery}
          onClose={() => setSelectedDocId(null)}
        />
      )}
    </div>
  )
}

export default App
