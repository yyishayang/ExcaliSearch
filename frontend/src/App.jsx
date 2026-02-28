import { useState, useEffect, useCallback } from 'react'
import { HiShieldCheck, HiOutlineFolderOpen, HiSearch, HiOutlineDocumentSearch, HiInbox } from 'react-icons/hi'
import { FaFilePdf, FaFileWord, FaFileAlt } from 'react-icons/fa'
import './App.css'
import UploadPanel from './components/UploadPanel'
import SearchBar from './components/SearchBar'
import ResultsList from './components/ResultsList'
import DocumentViewer from './components/DocumentViewer'
import ThemeSwitcher from './components/ThemeSwitcher'

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
  const [filterType, setFilterType] = useState('all')
  const [sortBy, setSortBy] = useState('default')
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'forest')

  // Theme effect
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])

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

  const typeIcons = {
    pdf: <FaFilePdf className="text-red-500" />,
    txt: <FaFileAlt className="text-green-500" />,
    docx: <FaFileWord className="text-blue-500" />
  }

  // Filter & Sort helper
  const getFilteredAndSorted = (list) => {
    if (!list) return list;
    let result = list.filter(item => filterType === 'all' || item.file_type === filterType);

    if (sortBy !== 'default') {
      result = [...result].sort((a, b) => {
        if (sortBy === 'name') return (a.original_name || '').localeCompare(b.original_name || '');
        if (sortBy === 'size') return (b.file_size || 0) - (a.file_size || 0);
        return 0;
      });
    }
    return result;
  };

  const displayedDocs = getFilteredAndSorted(documents);
  const displayedResults = searchResults ? getFilteredAndSorted(searchResults) : null;

  return (
    <div className="app">
      {/* Top Banner */}
      <header className="top-banner">
        <div className="top-banner__brand">
          <span className="top-banner__icon">
            <HiShieldCheck size={28} className="text-accent" />
          </span>
          <h1 className="top-banner__title">ExcaliSearch</h1>
        </div>
        <div className="top-banner__search">
          <SearchBar
            onSearch={handleSearch}
            resultCount={searchResults ? searchResults.length : null}
          />
        </div>
        <div className="top-banner__theme">
          <ThemeSwitcher currentTheme={theme} onThemeChange={setTheme} />
        </div>
      </header>

      {/* Filters Bar */}
      <div className="filters-bar">
        <div className="filters-bar__group">
          <label className="filters-bar__label">Tipo:</label>
          <select
            value={filterType}
            onChange={e => setFilterType(e.target.value)}
            className="filters-bar__select"
          >
            <option value="all">Todos</option>
            <option value="pdf">PDF</option>
            <option value="txt">Texto</option>
            <option value="docx">Word</option>
          </select>
        </div>
        <div className="filters-bar__group">
          <label className="filters-bar__label">Ordenar por:</label>
          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value)}
            className="filters-bar__select"
          >
            <option value="default">Por defecto</option>
            <option value="name">Nombre</option>
            <option value="size">Tamaño</option>
          </select>
        </div>
      </div>

      <main className="main-content">
        {/* Loading */}
        {loading && (
          <div className="empty-state">
            <div className="spinner" />
          </div>
        )}

        {/* Search Results */}
        {displayedResults && !loading && (
          <>
            {displayedResults.length > 0 ? (
              <ResultsList
                results={displayedResults}
                query={searchQuery}
                onSelect={(docId) => setSelectedDocId(docId)}
                onDelete={handleDelete}
              />
            ) : (
              <div className="empty-state">
                <div className="empty-state__icon">
                  <HiOutlineDocumentSearch size={48} className="mx-auto opacity-20" />
                </div>
                <p className="empty-state__text">No results found for &quot;{searchQuery}&quot;</p>
              </div>
            )}
          </>
        )}

        {/* Document Explorer (when not searching) */}
        {!searchResults && !loading && (
          <div className="explorer-section">
            <div className="explorer-section__header">
              <h2 className="explorer-section__title">
                <HiOutlineFolderOpen className="text-accent" /> Explorador de Archivos {displayedDocs.length > 0 && `(${displayedDocs.length})`}
              </h2>
              <div className="explorer-section__actions">
                <UploadPanel onUploadComplete={handleUploadComplete} compact={true} />
              </div>
            </div>

            {displayedDocs.length > 0 ? (
              <div className="doc-grid">
                {displayedDocs.map((doc) => (
                  <div
                    key={doc.id}
                    className="doc-card"
                    onClick={() => setSelectedDocId(doc.id)}
                  >
                    <div className="doc-card__icon text-5xl mb-2">{typeIcons[doc.file_type] || <FaFileAlt />}</div>
                    <div className="doc-card__name" title={doc.original_name}>{doc.original_name}</div>
                    <div className="doc-card__meta">
                      <span>{formatFileSize(doc.file_size || 0)}</span>
                      <span>{formatDate(doc.upload_date)}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-state__icon">
                  <HiInbox size={48} className="mx-auto opacity-20" />
                </div>
                <p className="empty-state__text">Esta carpeta está vacía. ¡Sube tu primer archivo!</p>
              </div>
            )}
          </div>
        )}
      </main>

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
