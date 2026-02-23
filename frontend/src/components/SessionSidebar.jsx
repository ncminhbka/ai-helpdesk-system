import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'

const API_BASE = 'http://localhost:8000/api/v1'

export default function SessionSidebar({ currentSession, onSessionChange, onNewSession }) {
    const [sessions, setSessions] = useState([])
    const [isLoading, setIsLoading] = useState(true)
    const [hoveredSession, setHoveredSession] = useState(null)
    const { token, user, logout } = useAuth()

    useEffect(() => { fetchSessions() }, [token])

    const fetchSessions = async () => {
        try {
            const response = await fetch(`${API_BASE}/chat/sessions`, {
                headers: { 'Authorization': `Bearer ${token}` }
            })
            if (response.ok) setSessions(await response.json())
        } catch (err) {
            console.error('Failed to fetch sessions:', err)
        } finally {
            setIsLoading(false)
        }
    }

    const createNewSession = async () => {
        try {
            const response = await fetch(`${API_BASE}/chat/sessions`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ title: 'New Chat' })
            })
            if (response.ok) {
                const newSession = await response.json()
                setSessions([newSession, ...sessions])
                onNewSession(newSession)
            }
        } catch (err) {
            console.error('Failed to create session:', err)
        }
    }

    const deleteSession = async (sessionId, e) => {
        e.stopPropagation()
        if (!confirm('Delete this chat?')) return
        try {
            const response = await fetch(`${API_BASE}/chat/sessions/${sessionId}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${token}` }
            })
            if (response.ok) {
                setSessions(sessions.filter(s => s.session_id !== sessionId))
                if (currentSession?.session_id === sessionId) onSessionChange(null)
            }
        } catch (err) {
            console.error('Failed to delete session:', err)
        }
    }

    const formatDate = (dateStr) => {
        const date = new Date(dateStr)
        const now = new Date()
        const diff = now - date
        if (diff < 24 * 60 * 60 * 1000) return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        if (diff < 7 * 24 * 60 * 60 * 1000) return date.toLocaleDateString([], { weekday: 'short' })
        return date.toLocaleDateString([], { month: 'short', day: 'numeric' })
    }

    return (
        <div className="w-72 h-screen flex flex-col glass-dark border-r border-white/5">
            {/* Header */}
            <div className="p-4 border-b border-white/5">
                <div className="flex items-center gap-3 mb-4 pl-2">
                    <img src="/logo.png" alt="FPT" className="w-10 h-10 object-contain" />
                    <div>
                        <h1 className="font-bold text-white text-lg tracking-tight">FPT HelpDesk</h1>
                        <p className="text-xs text-gray-400 font-medium">AI Assistant</p>
                    </div>
                </div>

                <button
                    onClick={createNewSession}
                    className="w-full flex items-center gap-2 px-4 py-3 rounded-xl btn-secondary text-white hover:bg-white/15 transition-all"
                >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    <span>New Chat</span>
                </button>
            </div>

            {/* Sessions List */}
            <div className="flex-1 overflow-y-auto p-2">
                {isLoading ? (
                    <div className="flex items-center justify-center py-8">
                        <div className="loading-dots"><span></span><span></span><span></span></div>
                    </div>
                ) : sessions.length === 0 ? (
                    <div className="text-center py-8 text-gray-500 text-sm">
                        <p>No conversations yet</p>
                        <p className="mt-1">Start a new chat!</p>
                    </div>
                ) : (
                    <div className="space-y-1">
                        {sessions.map((session) => (
                            <div
                                key={session.session_id}
                                onClick={() => onSessionChange(session)}
                                onMouseEnter={() => setHoveredSession(session.session_id)}
                                onMouseLeave={() => setHoveredSession(null)}
                                className={`relative group px-3 py-3 rounded-xl cursor-pointer transition-all ${currentSession?.session_id === session.session_id
                                    ? 'bg-fpt-orange/20 border border-fpt-orange/30'
                                    : 'hover:bg-white/5'
                                    }`}
                            >
                                <div className="flex items-center gap-3">
                                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${currentSession?.session_id === session.session_id
                                        ? 'bg-fpt-orange/30'
                                        : 'bg-white/5'
                                        }`}>
                                        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                                        </svg>
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm text-white truncate">{session.title}</p>
                                        <p className="text-xs text-gray-500">{formatDate(session.updated_at)}</p>
                                    </div>
                                    {hoveredSession === session.session_id && (
                                        <button
                                            onClick={(e) => deleteSession(session.session_id, e)}
                                            className="p-1.5 rounded-lg hover:bg-red-500/20 text-gray-400 hover:text-red-400 transition-colors"
                                        >
                                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                            </svg>
                                        </button>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* User Section */}
            <div className="p-4 border-t border-white/5">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-fpt-blue to-blue-400 flex items-center justify-center text-white font-medium">
                        {user?.name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || 'U'}
                    </div>
                    <div className="flex-1 min-w-0">
                        <p className="text-sm text-white truncate">{user?.name || user?.email}</p>
                        <p className="text-xs text-gray-500 truncate">{user?.email}</p>
                    </div>
                    <button
                        onClick={logout}
                        className="p-2 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
                        title="Sign out"
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    )
}
