import { useState, useRef, useEffect } from 'react'
import PropTypes from 'prop-types'
import { HiPaperAirplane, HiX, HiRefresh, HiLightBulb, HiDocumentText } from 'react-icons/hi'
import { FaRobot, FaUser } from 'react-icons/fa'

const API_BASE = '/api'

export default function ChatPanel({ onClose, documentContext = null }) {
    const [messages, setMessages] = useState([])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [chatAvailable, setChatAvailable] = useState(null)
    const [useRAG, setUseRAG] = useState(true)
    const messagesEndRef = useRef(null)
    const inputRef = useRef(null)

    // Check if chat is available on mount
    useEffect(() => {
        checkChatStatus()
    }, [])

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    // Focus input on mount
    useEffect(() => {
        inputRef.current?.focus()
    }, [])

    const checkChatStatus = async () => {
        try {
            const res = await fetch(`${API_BASE}/chat/status`)
            if (res.ok) {
                const data = await res.json()
                setChatAvailable(data.available)
                
                if (data.available && messages.length === 0) {
                    setMessages([{
                        role: 'assistant',
                        content: `I am Arthur, King of the Britons — and your assistant in ExcaliSearch. The Lady of the Lake, her arm clad in the purest shimmering samite, held aloft Excalibur from the bosom of the water, signifying by divine providence that I should help you search, analyze documents, and answer your questions. That is why I am your assistant. Now then — what is your query?`
                    }])
                }
            }
        } catch (error) {
            console.error('Error checking chat status:', error)
            setChatAvailable(false)
        }
    }

    const sendMessage = async (e) => {
        e?.preventDefault()
        
        if (!input.trim() || loading) return

        const userMessage = input.trim()
        setInput('')
        
        // Add user message immediately
        const newMessages = [...messages, { role: 'user', content: userMessage }]
        setMessages(newMessages)
        setLoading(true)

        try {
            // Prepare request
            const requestBody = {
                message: userMessage,
                history: messages.slice(-10), // Last 10 messages for context
                stream: false,
                use_rag: useRAG && !documentContext // Use RAG only if no specific document context
            }

            // Add document context if available
            if (documentContext?.id) {
                requestBody.document_ids = [documentContext.id]
            }

            const res = await fetch(`${API_BASE}/chat/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            })

            if (res.ok) {
                const data = await res.json()
                setMessages([...newMessages, { 
                    role: 'assistant', 
                    content: data.response 
                }])
            } else {
                const error = await res.json()
                setMessages([...newMessages, { 
                    role: 'assistant', 
                    content: `Error: ${error.detail || 'Could not get response'}` 
                }])
            }
        } catch (error) {
            console.error('Error sending message:', error)
            setMessages([...newMessages, { 
                role: 'assistant', 
                content: 'Connection error. Please verify that Ollama is running.' 
            }])
        } finally {
            setLoading(false)
        }
    }

    const clearChat = () => {
        setMessages([{
            role: 'assistant',
            content: documentContext 
                ? `Chat restarted. What else would you like to know about "${documentContext.name}"?`
                : 'Chat restarted. How can I help you?'
        }])
    }

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            sendMessage()
        }
    }

    if (chatAvailable === null) {
        return (
            <div className="chat-panel">
                <div className="chat-panel__header">
                    <h3 className="flex items-center gap-2">
                        <FaRobot /> AI Chat
                    </h3>
                    <button className="btn btn--ghost btn--sm" onClick={onClose}>
                        <HiX />
                    </button>
                </div>
                <div className="chat-panel__messages">
                    <div className="chat-panel__loading">
                        Checking availability...
                    </div>
                </div>
            </div>
        )
    }

    if (chatAvailable === false) {
        return (
            <div className="chat-panel">
                <div className="chat-panel__header">
                    <h3 className="flex items-center gap-2">
                        <FaRobot /> AI Chat
                    </h3>
                    <button className="btn btn--ghost btn--sm" onClick={onClose}>
                        <HiX />
                    </button>
                </div>
                <div className="chat-panel__messages">
                    <div className="chat-panel__error">
                        <HiLightBulb size={48} />
                        <h4>Chat not available</h4>
                        <p>Make sure Ollama is installed and running.</p>
                        <p className="text-sm mt-2">
                            Run: <code>ollama run llama3.2:3b</code>
                        </p>
                        <button className="btn btn--primary mt-4" onClick={checkChatStatus}>
                            <HiRefresh /> Retry
                        </button>
                    </div>
                </div>
            </div>
        )
    }

    return (
        <div className="chat-panel">
            <div className="chat-panel__header">
                <div>
                    <h3 className="flex items-center gap-2">
                        <FaRobot /> AI Chat
                    </h3>
                    {documentContext ? (
                        <p className="text-xs opacity-70 flex items-center gap-1 mt-1">
                            <HiDocumentText size={12} />
                            Context: {documentContext.name}
                        </p>
                    ) : (
                        <div className="flex items-center gap-2 mt-1">
                            <label className="flex items-center gap-1 text-xs cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={useRAG}
                                    onChange={(e) => setUseRAG(e.target.checked)}
                                    className="chat-toggle"
                                />
                                <span className="opacity-70">
                                    🔍 Search in documents
                                </span>
                            </label>
                        </div>
                    )}
                </div>
                <div className="flex gap-2">
                    <button className="btn btn--ghost btn--sm" onClick={onClose}>
                        <HiX />
                    </button>
                </div>
            </div>

            <div className="chat-panel__messages">
                {messages.map((msg, idx) => (
                    <div 
                        key={idx} 
                        className={`chat-message chat-message--${msg.role}`}
                    >
                        <div className="chat-message__avatar">
                            {msg.role === 'user' ? <FaUser /> : <FaRobot />}
                        </div>
                        <div className="chat-message__content">
                            {msg.content}
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="chat-message chat-message--assistant">
                        <div className="chat-message__avatar">
                            <FaRobot />
                        </div>
                        <div className="chat-message__content">
                            <div className="chat-typing">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <form className="chat-panel__input" onSubmit={sendMessage}>
                <input
                    ref={inputRef}
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={documentContext ? "Ask about the document..." : "Type your message..."}
                    disabled={loading}
                    className="chat-input"
                />
                <button 
                    type="submit" 
                    disabled={!input.trim() || loading}
                    className="btn btn--primary"
                >
                    <HiPaperAirplane />
                </button>
            </form>
        </div>
    )
}

ChatPanel.propTypes = {
    onClose: PropTypes.func.isRequired,
    documentContext: PropTypes.shape({
        id: PropTypes.string,
        name: PropTypes.string
    })
}
