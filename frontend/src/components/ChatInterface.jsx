import { useState, useRef, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'

const API_BASE = 'http://localhost:8000/api/v1'

// Vietnamese labels for common field names
const FIELD_LABELS = {
    room_name: 'Phòng', reason: 'Lý do', time: 'Thời gian',
    customer_name: 'Tên KH', customer_phone: 'SĐT',
    email: 'Email', note: 'Ghi chú',
    booking_id: 'Mã đặt phòng', ticket_id: 'Mã ticket',
    status: 'Trạng thái', content: 'Nội dung', description: 'Mô tả',
}

/**
 * ConfirmCard — Inline confirmation widget for HITL actions.
 * Shows tool args as editable fields + Approve / Reject buttons.
 */
function ConfirmCard({ data, fieldLabels, onRespond, disabled }) {
    const [editMode, setEditMode] = useState(false)
    const [edits, setEdits] = useState({})

    // Merge server-provided labels with our defaults
    const labels = { ...FIELD_LABELS, ...(fieldLabels || {}) }

    const handleFieldChange = (key, value) => {
        setEdits(prev => ({ ...prev, [key]: value }))
    }

    const handleApprove = () => {
        const hasEdits = Object.keys(edits).length > 0
        onRespond(JSON.stringify({
            action: 'approve',
            ...(hasEdits ? { edits } : {}),
        }))
    }

    const handleReject = () => {
        onRespond(JSON.stringify({ action: 'reject' }))
    }

    if (!data || Object.keys(data).length === 0) {
        return (
            <div className="mt-3 flex gap-2">
                <button onClick={handleApprove} disabled={disabled}
                    className="btn-primary px-4 py-1.5 text-sm disabled:opacity-50">
                    ✅ Xác nhận
                </button>
                <button onClick={handleReject} disabled={disabled}
                    className="px-4 py-1.5 text-sm rounded-lg bg-red-500/20 text-red-300 hover:bg-red-500/30 transition disabled:opacity-50">
                    ❌ Hủy
                </button>
            </div>
        )
    }

    return (
        <div className="mt-3">
            {/* Data fields */}
            <div className="space-y-2 mb-4">
                {Object.entries(data).map(([key, value]) => (
                    <div key={key} className="flex items-center gap-2 text-sm">
                        <span className="text-gray-400 min-w-[80px] text-right">
                            {labels[key] || key}:
                        </span>
                        {editMode ? (
                            <input
                                type="text"
                                defaultValue={value}
                                onChange={(e) => handleFieldChange(key, e.target.value)}
                                className="flex-1 px-2 py-1 rounded bg-white/5 border border-white/10 text-gray-200 text-sm focus:border-blue-500/50 focus:outline-none"
                            />
                        ) : (
                            <span className="text-gray-200">{String(value)}</span>
                        )}
                    </div>
                ))}
            </div>

            {/* Action buttons */}
            <div className="flex gap-2 flex-wrap">
                <button onClick={handleApprove} disabled={disabled}
                    className="btn-primary px-4 py-1.5 text-sm disabled:opacity-50">
                    ✅ Xác nhận
                </button>
                {!editMode && (
                    <button onClick={() => setEditMode(true)} disabled={disabled}
                        className="px-4 py-1.5 text-sm rounded-lg bg-blue-500/20 text-blue-300 hover:bg-blue-500/30 transition disabled:opacity-50">
                        ✏️ Sửa
                    </button>
                )}
                {editMode && (
                    <button onClick={() => { setEditMode(false); setEdits({}) }} disabled={disabled}
                        className="px-4 py-1.5 text-sm rounded-lg bg-gray-500/20 text-gray-300 hover:bg-gray-500/30 transition disabled:opacity-50">
                        ↩️ Hủy sửa
                    </button>
                )}
                <button onClick={handleReject} disabled={disabled}
                    className="px-4 py-1.5 text-sm rounded-lg bg-red-500/20 text-red-300 hover:bg-red-500/30 transition disabled:opacity-50">
                    ❌ Hủy
                </button>
            </div>
        </div>
    )
}


function renderUserContent(content) {
    try {
        const parsed = JSON.parse(content)
        if (parsed.action === 'approve') {
            const hasEdits = parsed.edits && Object.keys(parsed.edits).length > 0
            return hasEdits ? '✅ Đã xác nhận (có chỉnh sửa)' : '✅ Đã xác nhận'
        }
        if (parsed.action === 'reject') {
            return '❌ Đã hủy thao tác'
        }
    } catch {
        // not JSON — render bình thường
    }
    return content
}

export default function ChatInterface({ session, onSessionUpdate }) {
    const [messages, setMessages] = useState([])
    const [inputValue, setInputValue] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [pendingConfirm, setPendingConfirm] = useState(null) // {index, data, fieldLabels}
    const messagesEndRef = useRef(null)
    const inputRef = useRef(null)
    const { token } = useAuth()

    // Load messages when session changes
    useEffect(() => {
        if (session) {
            loadMessages()
        } else {
            setMessages([])
            setPendingConfirm(null)
        }
    }, [session?.session_id])

    // Scroll to bottom on new messages
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    // Focus input when ready
    useEffect(() => {
        if (!isLoading && !pendingConfirm) inputRef.current?.focus()
    }, [isLoading, pendingConfirm])

    const loadMessages = async () => {
        try {
            const response = await fetch(`${API_BASE}/chat/sessions/${session.session_id}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            })
            if (response.ok) {
                const data = await response.json()
                const msgs = data.messages || []
                setMessages(msgs)

                // Check if last message is an unresolved confirm
                const lastMsg = msgs[msgs.length - 1]
                if (lastMsg?.message_type === 'confirm' && lastMsg?.role === 'assistant') {
                    // Try to parse metadata for structured data
                    const meta = lastMsg.metadata || {}
                    setPendingConfirm({
                        index: msgs.length - 1,
                        data: meta.args || {},
                        fieldLabels: meta.field_labels || {},
                    })
                } else {
                    setPendingConfirm(null)
                }
            }
        } catch (err) {
            console.error('Failed to load messages:', err)
        }
    }

    /**
     * Send a message to the backend. Can be called from:
     * 1. Normal text input (form submit)
     * 2. ConfirmCard buttons (structured JSON payload)
     */
    const sendMessage = async (e, overrideMessage = null) => {
        if (e) e.preventDefault()
        const messageToSend = overrideMessage || inputValue.trim()
        if (!messageToSend || isLoading || !session) return

        if (!overrideMessage) setInputValue('')

        // Clear pending confirm when responding
        setPendingConfirm(null)

        // Add user message immediately (don't show raw JSON for confirm responses)
        const isStructuredResponse = overrideMessage && overrideMessage.startsWith('{')
        if (!isStructuredResponse) {
            const newUserMsg = {
                role: 'user',
                content: messageToSend,
                message_type: 'message',
                created_at: new Date().toISOString()
            }
            setMessages(prev => [...prev, newUserMsg])
        }

        setIsLoading(true)

        try {
            const response = await fetch(`${API_BASE}/chat/chat`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: session.session_id,
                    message: messageToSend
                })
            })

            if (response.ok) {
                const data = await response.json()
                const assistantMsg = {
                    role: 'assistant',
                    content: data.content,
                    message_type: data.type,
                    metadata: data.data ? { args: data.data, field_labels: {} } : null,
                    created_at: new Date().toISOString()
                }
                setMessages(prev => [...prev, assistantMsg])

                // If this is a confirm response, set pending confirm
                if (data.type === 'confirm' && data.data) {
                    setMessages(prev => {
                        const idx = prev.length - 1
                        setPendingConfirm({
                            index: idx,
                            data: data.data,
                            fieldLabels: {},
                        })
                        return prev
                    })
                }

                // Update session title if first message
                if (onSessionUpdate && messages.length === 0 && !isStructuredResponse) {
                    onSessionUpdate({
                        ...session,
                        title: messageToSend.slice(0, 50) + (messageToSend.length > 50 ? '...' : '')
                    })
                }
            } else {
                throw new Error('Request failed')
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

    /** Called by ConfirmCard buttons */
    const handleConfirmRespond = (payload) => {
        sendMessage(null, payload)
    }

    // Empty state
    if (!session) {
        return (
            <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                    <img src="/logo.png" alt="FPT" className="w-24 h-24 mx-auto mb-6 object-contain" />
                    <h2 className="text-3xl font-bold text-white mb-3">FPT HelpDesk</h2>
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
                                            : msg.message_type === 'confirm'
                                                ? 'message-assistant border-amber-500/40 bg-amber-500/10 text-gray-200'
                                                : 'message-assistant text-gray-200'
                                        }`}
                                >
                                    {msg.message_type === 'confirm' && msg.role === 'assistant' && (
                                        <div className="flex items-center gap-2 mb-2 pb-2 border-b border-amber-500/20">
                                            <span className="text-amber-400 text-lg">⚠️</span>
                                            <span className="text-amber-300 text-sm font-medium">Cần xác nhận</span>
                                        </div>
                                    )}
                                    <div className="markdown-content whitespace-pre-wrap">
                                        {msg.role === 'user' ? renderUserContent(msg.content) : msg.content}
                                    </div>

                                    {/* Render ConfirmCard for the pending confirm message */}
                                    {pendingConfirm && pendingConfirm.index === idx && (
                                        <ConfirmCard
                                            data={pendingConfirm.data}
                                            fieldLabels={pendingConfirm.fieldLabels}
                                            onRespond={handleConfirmRespond}
                                            disabled={isLoading}
                                        />
                                    )}
                                </div>
                            </div>
                        ))}

                        {isLoading && (
                            <div className="flex justify-start animate-fade-in">
                                <div className="message-assistant px-4 py-3">
                                    <div className="loading-dots">
                                        <span></span><span></span><span></span>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>
                )}
            </div>

            {/* Input */}
            <div className="px-6 py-4 border-t border-white/5">
                <form onSubmit={sendMessage} className="max-w-3xl mx-auto">
                    <div className="flex gap-3">
                        <input
                            ref={inputRef}
                            type="text"
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            placeholder={pendingConfirm ? "Đang chờ xác nhận..." : "Type your message..."}
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
