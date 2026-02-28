import { useState, useEffect, useRef } from 'react'
import { HiSearch, HiXCircle, HiSparkles } from 'react-icons/hi'

export default function SearchBar({ onSearch, resultCount }) {
    const [query, setQuery] = useState('')
    const [mode, setMode] = useState('hybrid')
    const debounceRef = useRef(null)

    useEffect(() => {
        if (debounceRef.current) {
            clearTimeout(debounceRef.current)
        }

        if (query.trim().length === 0) {
            onSearch('', mode)
            return
        }

        debounceRef.current = setTimeout(() => {
            onSearch(query.trim(), mode)
        }, 350)

        return () => {
            if (debounceRef.current) clearTimeout(debounceRef.current)
        }
    }, [query, mode, onSearch])

    const handleClear = () => {
        setQuery('')
        onSearch('', mode)
    }

    const getModeLabel = (mode) => {
        switch(mode) {
            case 'hybrid': return 'Hybrid'
            case 'semantic': return 'Semantic'
            case 'normal': return 'Keywords'
            default: return mode
        }
    }

    const getModeDescription = (mode) => {
        switch(mode) {
            case 'hybrid': return 'Combines AI understanding + exact keywords (70% semantic + 30% keywords)'
            case 'semantic': return 'AI-powered search that understands meaning and concepts'
            case 'normal': return 'Traditional keyword matching'
            default: return ''
        }
    }

    return (
        <div className="search-section">
            <div className="search-bar">
                <span className="search-bar__icon">
                    <HiSearch size={20} />
                </span>
                <input
                    className="search-bar__input"
                    type="text"
                    placeholder="Search within your documents..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    id="search-input"
                />
                <select
                    className="search-bar__mode"
                    value={mode}
                    onChange={(e) => setMode(e.target.value)}
                    aria-label="Search mode"
                    title="Choose search mode"
                >
                    <option value="hybrid">Hybrid</option>
                    <option value="semantic">Semantic</option>
                    <option value="normal">Keywords</option>
                </select>
                {query && (
                    <button
                        className="search-bar__clear"
                        onClick={handleClear}
                        title="Clear search"
                    >
                        <HiXCircle size={18} />
                    </button>
                )}
            </div>

            {query.trim() && resultCount !== null && (
                <div className="search-info">
                    <span className="search-info__count">
                        <HiSparkles className="inline mr-1 text-accent" />
                        <strong>{resultCount}</strong> result{resultCount !== 1 ? 's' : ''} found
                    </span>
                    <span className="search-info__mode" title={getModeDescription(mode)}>
                        Mode: {getModeLabel(mode)}
                    </span>
                </div>
            )}
        </div>
    )
}
