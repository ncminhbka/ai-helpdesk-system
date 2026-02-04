import { useState, useRef, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import ConfirmationForm from './ConfirmationForm'

const API_BASE = 'http://localhost:8000'

export default function ChatInterface({ session, onSessionUpdate }) {
    const [messages, setMessages] = useState([])
    const [inputValue, setInputValue] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [pendingConfirm, setPendingConfirm] = useState(null)

    const messagesEndRef = useRef(null)
    const inputRef = useRef(null)
    const { token } = useAuth()

    // Load messages when session changes
    useEffect(() => {
        if (session) {
            loadMessages()
        } else {
            setMessages([])
        }
    }, [session?.session_id])

    // Scroll to bottom on new messages
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    // Focus input when ready
    useEffect(() => {
        if (!isLoading && !pendingConfirm) {
            inputRef.current?.focus()
        }
    }, [isLoading, pendingConfirm])

    const loadMessages = async () => {
        try {
            const response = await fetch(`${API_BASE}/sessions/${session.session_id}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            })

            if (response.ok) {
                const data = await response.json()
                setMessages(data.messages || [])

                // Check for pending confirmation in last message
                const lastMsg = data.messages?.[data.messages.length - 1]
                if (lastMsg?.message_type === 'confirm' && lastMsg?.metadata) {
                    setPendingConfirm({
                        actionId: lastMsg.metadata.action_id,
                        action: lastMsg.metadata.action,
                        data: lastMsg.metadata.data,
                        fields: lastMsg.metadata.fields
                    })
                }
            }
        } catch (err) {
            console.error('Failed to load messages:', err)
        }
    }

    const sendMessage = async (e) => {
        e.preventDefault()
        if (!inputValue.trim() || isLoading || !session) return

        const userMessage = inputValue.trim()
        setInputValue('')

        // Add user message immediately
        const newUserMsg = {
            role: 'user',
            content: userMessage,
            message_type: 'message',
            created_at: new Date().toISOString()
        }
        setMessages(prev => [...prev, newUserMsg])
        setIsLoading(true)

        try {
            const response = await fetch(`${API_BASE}/chat`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: session.session_id,
                    message: userMessage
                })
            })

            if (response.ok) {
                const data = await response.json()

                // Add assistant message
                const assistantMsg = {
                    role: 'assistant',
                    content: data.content,
                    message_type: data.type,
                    created_at: new Date().toISOString(),
                    metadata: data.action_id ? {
                        action_id: data.action_id,
                        action: data.action,
                        data: data.data,
                        fields: data.fields
                    } : null
                }
                setMessages(prev => [...prev, assistantMsg])

                // Handle confirmation request
                if (data.type === 'confirm') {
                    setPendingConfirm({
                        actionId: data.action_id,
                        action: data.action,
                        data: data.data,
                        fields: data.fields
                    })
                }

                // Update session title if first message
                if (onSessionUpdate && messages.length === 0) {
                    onSessionUpdate({
                        ...session,
                        title: userMessage.slice(0, 50) + (userMessage.length > 50 ? '...' : '')
                    })
                }
            }
        } catch (err) {
            console.error('Failed to send message:', err)
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại.',
                message_type: 'error',
                created_at: new Date().toISOString()
            }])
        } finally {
            setIsLoading(false)
        }
    }

    const handleConfirm = async (actionId, edits) => {
        setIsLoading(true)
        try {
            const response = await fetch(`${API_BASE}/confirm/${actionId}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ edits })
            })

            if (response.ok) {
                const data = await response.json()
                setMessages(prev => [...prev, {
                    role: 'assistant',
                    content: data.content,
                    message_type: 'message',
                    created_at: new Date().toISOString()
                }])
            }
        } catch (err) {
            console.error('Confirmation failed:', err)
        } finally {
            setPendingConfirm(null)
            setIsLoading(false)
        }
    }

    const handleCancel = async (actionId) => {
        try {
            await fetch(`${API_BASE}/cancel/${actionId}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            })

            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Đã hủy thao tác. / Action cancelled.',
                message_type: 'message',
                created_at: new Date().toISOString()
            }])
        } catch (err) {
            console.error('Cancel failed:', err)
        } finally {
            setPendingConfirm(null)
        }
    }

    // Empty state
    if (!session) {
        return (
            <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                    <div className="w-20 h-20 mx-auto mb-6 rounded-2xl gradient-orange flex items-center justify-center">
                        <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                        </svg>
                    </div>
                    <h2 className="text-2xl font-semibold text-white mb-2">FPT Support Assistant</h2>
                    <p className="text-gray-400 mb-6 max-w-md">
                        Start a new conversation to get help with tickets, bookings, policies, or IT support.
                    </p>
                    <div className="flex flex-wrap justify-center gap-3 text-sm">
                        <span className="px-3 py-1.5 rounded-full glass">📋 Support Tickets</span>
                        <span className="px-3 py-1.5 rounded-full glass">📅 Room Booking</span>
                        <span className="px-3 py-1.5 rounded-full glass">📖 FPT Policies</span>
                        <span className="px-3 py-1.5 rounded-full glass">🔧 IT Support</span>
                    </div>
                </div>
            </div>
        )
    }

    return (
        <div className="flex-1 flex flex-col h-full min-h-0 overflow-hidden">
            {/* Header */}
            <div className="px-6 py-4 border-b border-white/5 glass-dark">
                <h2 className="font-medium text-white truncate">{session.title}</h2>
            </div>

            {/* Messages */}
            <div className="flex-1 min-h-0 overflow-y-auto px-6 py-4">
                {messages.length === 0 ? (
                    <div className="h-full flex items-center justify-center">
                        <div className="text-center text-gray-400">
                            <p>Bắt đầu cuộc trò chuyện!</p>
                            <p className="text-sm mt-1">Hãy hỏi về chính sách, ticket, đặt phòng, hoặc vấn đề IT.</p>
                        </div>
                    </div>
                ) : (
                    <div className="space-y-4 max-w-3xl mx-auto">
                        {messages.map((msg, idx) => (
                            <div
                                key={idx}
                                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}
                            >
                                <div
                                    className={`max-w-[85%] px-4 py-3 ${msg.role === 'user'
                                        ? 'message-user text-white'
                                        : msg.message_type === 'error'
                                            ? 'message-assistant border-red-500/30 bg-red-500/10 text-red-300'
                                            : 'message-assistant text-gray-200'
                                        }`}
                                >
                                    <div className="markdown-content whitespace-pre-wrap">{msg.content}</div>
                                </div>
                            </div>
                        ))}

                        {isLoading && (
                            <div className="flex justify-start animate-fade-in">
                                <div className="message-assistant px-4 py-3">
                                    <div className="loading-dots">
                                        <span></span>
                                        <span></span>
                                        <span></span>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>
                )}
            </div>

            {/* Confirmation Form */}
            {pendingConfirm && (
                <ConfirmationForm
                    action={pendingConfirm.action}
                    data={pendingConfirm.data}
                    fields={pendingConfirm.fields}
                    onConfirm={(edits) => handleConfirm(pendingConfirm.actionId, edits)}
                    onCancel={() => handleCancel(pendingConfirm.actionId)}
                />
            )}

            {/* Input */}
            <div className="px-6 py-4 border-t border-white/5">
                <form onSubmit={sendMessage} className="max-w-3xl mx-auto">
                    <div className="flex gap-3">
                        <input
                            ref={inputRef}
                            type="text"
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            placeholder={pendingConfirm ? "Please confirm or cancel the action above..." : "Type your message..."}
                            disabled={isLoading || !!pendingConfirm}
                            className="flex-1 input-dark disabled:opacity-50"
                        />
                        <button
                            type="submit"
                            disabled={!inputValue.trim() || isLoading || !!pendingConfirm}
                            className="btn-primary px-6 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                            </svg>
                        </button>
                    </div>
                </form>
            </div>
        </div>
    )
}
