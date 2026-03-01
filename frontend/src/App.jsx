import { useState, useEffect, useCallback } from 'react'
import { HiShieldCheck, HiOutlineFolderOpen, HiOutlineDocumentSearch, HiInbox, HiTrash, HiChat } from 'react-icons/hi'
import { FaFilePdf, FaFileWord, FaFileAlt, FaFileExcel, FaFileCsv, FaRobot } from 'react-icons/fa'
import './App.css'
import UploadPanel from './components/UploadPanel'
import SearchBar from './components/SearchBar'
import ResultsList from './components/ResultsList'
import DocumentViewer from './components/DocumentViewer'
import ThemeSwitcher from './components/ThemeSwitcher'
import ChatPanel from './components/ChatPanel'

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
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [searchIn, setSearchIn] = useState('content')
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'forest')
  const [chatOpen, setChatOpen] = useState(false)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])

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

  const handleSearch = useCallback(async (query, mode = 'hybrid') => {
    setSearchQuery(query)

    if (!query) {
      setSearchResults(null)
      return
    }

    setLoading(true)
    try {
      const res = await fetch(
        `${API_BASE}/search?q=${encodeURIComponent(query)}&mode=${encodeURIComponent(mode)}`
      )
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

  const handleDelete = useCallback(async (docId) => {
    if (!confirm('Are you sure you want to delete this document?')) return

    try {
      const res = await fetch(`${API_BASE}/documents/${docId}`, { method: 'DELETE' })
      if (res.ok) {
        loadDocuments()
        if (searchResults) {
          setSearchResults(prev => prev.filter(r => r.doc_id !== docId))
        }
      }
    } catch (err) {
      console.error('Delete error:', err)
    }
  }, [searchResults, loadDocuments])

  const handleUploadComplete = useCallback(() => {
    loadDocuments()
  }, [loadDocuments])

  const typeIcons = {
    pdf: <FaFilePdf className="text-red-500" />,
    txt: <FaFileAlt className="text-green-500" />,
    docx: <FaFileWord className="text-blue-500" />,
    xlsx: <FaFileExcel className="text-emerald-500" />,
    csv: <FaFileCsv className="text-emerald-600" />
  }

  const getFilteredAndSorted = (list, isSearchList = false) => {
    if (!list) return list;
    let result = list.filter(item => {
      let typeMatch = filterType === 'all' || item.file_type === filterType;

      let dateMatch = true;
      if (startDate || endDate) {
        const docDateStr = item.upload_date || item.created_at || '';
        if (docDateStr) {
          const docDate = new Date(docDateStr);
          docDate.setHours(0, 0, 0, 0);

          if (startDate) {
            const start = new Date(startDate);
            start.setHours(0, 0, 0, 0);
            if (docDate < start) dateMatch = false;
          }
          if (endDate) {
            const end = new Date(endDate);
            end.setHours(0, 0, 0, 0);
            if (docDate > end) dateMatch = false;
          }
        }
      }

      let titleSearchMatch = true;
      if (isSearchList && searchIn === 'title' && searchQuery) {
        const normalizeText = (text) => text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
        const queryNormalized = normalizeText(searchQuery);
        const itemNameNormalized = normalizeText(item.original_name || item.filename || '');
        titleSearchMatch = itemNameNormalized.includes(queryNormalized);
      }

      return typeMatch && dateMatch && titleSearchMatch;
    });

    if (sortBy !== 'default') {
      result = [...result].sort((a, b) => {
        if (sortBy === 'name') return (a.original_name || '').localeCompare(b.original_name || '');
        if (sortBy === 'size') return (b.file_size || 0) - (a.file_size || 0);
        return 0;
      });
    }
    return result;
  };

  const displayedDocs = getFilteredAndSorted(documents, false);
  const displayedResults = searchResults ? getFilteredAndSorted(searchResults, true) : null;

  return (
    <div className="app">
      <header className="top-banner">
        <div className="top-banner__brand">
          <span className="top-banner__icon">
            <img src="../public/espada.png" alt="Logo" className="top-banner__logo-img" />
          </span>
          <h1 className="top-banner__title">ExcaliSearch</h1>
        </div>
        <div className="top-banner__search">
          <SearchBar
            onSearch={handleSearch}
            resultCount={searchResults ? displayedResults.length : null}
          />
        </div>
        <div className="top-banner__theme">
          <ThemeSwitcher currentTheme={theme} onThemeChange={setTheme} />
        </div>
      </header>

      <div className="filters-bar">
        <div className="filters-bar__group">
          <label className="filters-bar__label">Search in:</label>
          <select
            value={searchIn}
            onChange={e => setSearchIn(e.target.value)}
            className="filters-bar__select"
          >
            <option value="content">Content</option>
            <option value="title">Title only</option>
          </select>
        </div>
        <div className="filters-bar__group">
          <label className="filters-bar__label">Type:</label>
          <select
            value={filterType}
            onChange={e => setFilterType(e.target.value)}
            className="filters-bar__select"
          >
            <option value="all">All</option>
            <option value="pdf">PDF</option>
            <option value="txt">Text</option>
            <option value="docx">Word</option>
            <option value="xlsx">Excel</option>
            <option value="csv">CSV</option>
          </select>
        </div>
        <div className="filters-bar__group">
          <label className="filters-bar__label">From:</label>
          <input
            type="date"
            value={startDate}
            onChange={e => setStartDate(e.target.value)}
            className="filters-bar__input"
          />
        </div>
        <div className="filters-bar__group">
          <label className="filters-bar__label">To:</label>
          <input
            type="date"
            value={endDate}
            onChange={e => setEndDate(e.target.value)}
            className="filters-bar__input"
          />
        </div>
        <div className="filters-bar__group">
          <label className="filters-bar__label">Sort by:</label>
          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value)}
            className="filters-bar__select"
          >
            <option value="default">Default</option>
            <option value="name">Name</option>
            <option value="size">Size</option>
          </select>
        </div>
      </div>

      <main className="main-content">
        {loading && (
          <div className="empty-state">
            <div className="spinner" />
          </div>
        )}

        {!searchResults && !loading && (
          <div className="upload-section">
            <UploadPanel onUploadComplete={handleUploadComplete} compact={false} />
          </div>
        )}

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

        {!searchResults && !loading && (
          <div className="explorer-section">
            <div className="explorer-section__header">
              <h2 className="explorer-section__title">
                <HiOutlineFolderOpen className="text-accent" /> Documents Explorer {displayedDocs.length > 0 && `(${displayedDocs.length})`}
              </h2>
            </div>

            {displayedDocs.length > 0 ? (
              <div className="doc-grid">
                {displayedDocs.map((doc) => (
                  <div
                    key={doc.id}
                    className="doc-card"
                    onClick={() => setSelectedDocId(doc.id)}
                  >
                    <button
                      className="doc-card__delete"
                      title="Delete document"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(doc.id);
                      }}
                    >
                      <HiTrash size={16} />
                    </button>
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
                <p className="empty-state__text">This folder is empty. Upload your first document!</p>
              </div>
            )}
          </div>
        )}
      </main>

      {selectedDocId && (
        <DocumentViewer
          docId={selectedDocId}
          query={searchQuery}
          onClose={() => setSelectedDocId(null)}
        />
      )}

      {/* Chat floating button */}
      {!chatOpen && (
        <button 
          className="chat-button-float"
          onClick={() => setChatOpen(true)}
          title="AI Chat"
        >
          <FaRobot />
        </button>
      )}

      {/* Chat panel */}
      {chatOpen && (
        <ChatPanel onClose={() => setChatOpen(false)} />
      )}
    </div>
  )
}

export default App
