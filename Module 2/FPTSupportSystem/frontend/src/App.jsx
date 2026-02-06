import { useState } from 'react'
import { useAuth } from './contexts/AuthContext'
import AuthPage from './components/AuthPage'
import SessionSidebar from './components/SessionSidebar'
import ChatInterface from './components/ChatInterface'


export default function App() {
    const { isAuthenticated, loading } = useAuth()
    const [currentSession, setCurrentSession] = useState(null)

    // Loading state
    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <div className="w-16 h-16 mx-auto mb-4 rounded-2xl gradient-orange flex items-center justify-center animate-pulse">
                        <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                        </svg>
                    </div>
                    <div className="loading-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </div>
        )
    }

    // Not authenticated - show auth page
    if (!isAuthenticated) {
        return <AuthPage />
    }

    // Authenticated - show main app
    return (
        <div className="h-screen flex overflow-hidden">
            {/* Sidebar */}
            <SessionSidebar
                currentSession={currentSession}
                onSessionChange={setCurrentSession}
                onNewSession={(session) => setCurrentSession(session)}
            />

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
                <ChatInterface
                    session={currentSession}
                    onSessionUpdate={(updatedSession) => {
                        setCurrentSession(updatedSession)
                    }}
                />
            </div>
        </div>
    )
}
