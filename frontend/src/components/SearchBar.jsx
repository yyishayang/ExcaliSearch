import { useState, useEffect, useRef } from 'react'

export default function SearchBar({ onSearch, resultCount }) {
    const [query, setQuery] = useState('')
    const debounceRef = useRef(null)

    useEffect(() => {
        if (debounceRef.current) {
            clearTimeout(debounceRef.current)
        }

        if (query.trim().length === 0) {
            onSearch('')
            return
        }

        debounceRef.current = setTimeout(() => {
            onSearch(query.trim())
        }, 350)

        return () => {
            if (debounceRef.current) clearTimeout(debounceRef.current)
        }
    }, [query])

    const handleClear = () => {
        setQuery('')
        onSearch('')
    }

    return (
        <div className="search-section">
            <div className="search-bar">
                <span className="search-bar__icon">🔍</span>
                <input
                    className="search-bar__input"
                    type="text"
                    placeholder="Search within your documents…"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    id="search-input"
                />
                {query && (
                    <button
                        className="search-bar__clear"
                        onClick={handleClear}
                        title="Clear search"
                    >
                        ✕
                    </button>
                )}
            </div>

            {query.trim() && resultCount !== null && (
                <div className="search-info">
                    <span className="search-info__count">
                        <strong>{resultCount}</strong> result{resultCount !== 1 ? 's' : ''} found
                    </span>
                </div>
            )}
        </div>
    )
}
