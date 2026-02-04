import { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'

const API_BASE = 'http://localhost:8000'

const STATUS_COLORS = {
    Pending: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
    Resolving: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
    Finished: 'bg-green-500/20 text-green-300 border-green-500/30',
    Canceled: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
    Scheduled: 'bg-blue-500/20 text-blue-300 border-blue-500/30'
}

export default function DatabaseViewer() {
    const [isOpen, setIsOpen] = useState(false)
    const [activeTab, setActiveTab] = useState('tickets')
    const [tickets, setTickets] = useState([])
    const [bookings, setBookings] = useState([])
    const [isLoading, setIsLoading] = useState(false)

    const { token } = useAuth()

    useEffect(() => {
        if (isOpen) {
            fetchData()
        }
    }, [isOpen, activeTab])

    const fetchData = async () => {
        setIsLoading(true)
        try {
            if (activeTab === 'tickets') {
                const response = await fetch(`${API_BASE}/tickets`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                })
                if (response.ok) {
                    setTickets(await response.json())
                }
            } else {
                const response = await fetch(`${API_BASE}/bookings`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                })
                if (response.ok) {
                    setBookings(await response.json())
                }
            }
        } catch (err) {
            console.error('Failed to fetch data:', err)
        } finally {
            setIsLoading(false)
        }
    }

    const formatDate = (dateStr) => {
        if (!dateStr) return '-'
        return new Date(dateStr).toLocaleString('vi-VN')
    }

    return (
        <>
            {/* Toggle Button */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className={`
          fixed right-4 bottom-4 z-50 w-14 h-14 rounded-full shadow-lg
          flex items-center justify-center transition-all duration-300
          ${isOpen
                        ? 'gradient-blue rotate-45'
                        : 'gradient-orange hover:scale-110'
                    }
        `}
            >
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d={isOpen
                            ? "M6 18L18 6M6 6l12 12"
                            : "M4 6h16M4 10h16M4 14h16M4 18h16"
                        }
                    />
                </svg>
            </button>

            {/* Panel */}
            <div className={`
        fixed right-0 top-0 h-screen w-96 z-40
        transform transition-transform duration-300 ease-out
        ${isOpen ? 'translate-x-0' : 'translate-x-full'}
        glass-dark border-l border-white/5
      `}>
                {/* Header */}
                <div className="p-4 border-b border-white/5">
                    <h2 className="font-semibold text-white text-lg">Database Viewer</h2>
                    <p className="text-sm text-gray-400 mt-1">View your tickets and bookings</p>
                </div>

                {/* Tabs */}
                <div className="flex border-b border-white/5">
                    <button
                        onClick={() => setActiveTab('tickets')}
                        className={`flex-1 py-3 text-sm font-medium transition-colors ${activeTab === 'tickets'
                                ? 'text-fpt-orange border-b-2 border-fpt-orange'
                                : 'text-gray-400 hover:text-white'
                            }`}
                    >
                        Tickets
                    </button>
                    <button
                        onClick={() => setActiveTab('bookings')}
                        className={`flex-1 py-3 text-sm font-medium transition-colors ${activeTab === 'bookings'
                                ? 'text-fpt-orange border-b-2 border-fpt-orange'
                                : 'text-gray-400 hover:text-white'
                            }`}
                    >
                        Bookings
                    </button>
                </div>

                {/* Content */}
                <div className="p-4 overflow-y-auto" style={{ height: 'calc(100vh - 140px)' }}>
                    {isLoading ? (
                        <div className="flex items-center justify-center py-12">
                            <div className="loading-dots">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                        </div>
                    ) : activeTab === 'tickets' ? (
                        <TicketsList tickets={tickets} formatDate={formatDate} />
                    ) : (
                        <BookingsList bookings={bookings} formatDate={formatDate} />
                    )}
                </div>

                {/* Refresh Button */}
                <div className="absolute bottom-4 left-4 right-4">
                    <button
                        onClick={fetchData}
                        disabled={isLoading}
                        className="w-full btn-secondary py-2 text-sm text-gray-300 disabled:opacity-50"
                    >
                        🔄 Refresh
                    </button>
                </div>
            </div>
        </>
    )
}

function TicketsList({ tickets, formatDate }) {
    if (tickets.length === 0) {
        return (
            <div className="text-center py-8 text-gray-500">
                <p>No tickets yet</p>
                <p className="text-sm mt-1">Create one via chat!</p>
            </div>
        )
    }

    return (
        <div className="space-y-3">
            {tickets.map((ticket) => (
                <div key={ticket.ticket_id} className="glass rounded-lg p-4">
                    <div className="flex items-start justify-between gap-2 mb-2">
                        <h3 className="font-medium text-white text-sm">#{ticket.ticket_id}</h3>
                        <span className={`px-2 py-0.5 text-xs rounded-full border ${STATUS_COLORS[ticket.status] || 'bg-gray-500/20'}`}>
                            {ticket.status}
                        </span>
                    </div>
                    <p className="text-sm text-gray-300 mb-2">{ticket.content}</p>
                    {ticket.description && (
                        <p className="text-xs text-gray-500 mb-2 line-clamp-2">{ticket.description}</p>
                    )}
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                        <span>📅 {formatDate(ticket.time)}</span>
                    </div>
                </div>
            ))}
        </div>
    )
}

function BookingsList({ bookings, formatDate }) {
    if (bookings.length === 0) {
        return (
            <div className="text-center py-8 text-gray-500">
                <p>No bookings yet</p>
                <p className="text-sm mt-1">Book a room via chat!</p>
            </div>
        )
    }

    return (
        <div className="space-y-3">
            {bookings.map((booking) => (
                <div key={booking.booking_id} className="glass rounded-lg p-4">
                    <div className="flex items-start justify-between gap-2 mb-2">
                        <h3 className="font-medium text-white text-sm">#{booking.booking_id}</h3>
                        <span className={`px-2 py-0.5 text-xs rounded-full border ${STATUS_COLORS[booking.status] || 'bg-gray-500/20'}`}>
                            {booking.status}
                        </span>
                    </div>
                    <p className="text-sm text-gray-300 mb-2">{booking.reason}</p>
                    <div className="flex flex-col gap-1 text-xs text-gray-500">
                        <span>📅 {formatDate(booking.time)}</span>
                        {booking.note && <span>📝 {booking.note}</span>}
                    </div>
                </div>
            ))}
        </div>
    )
}
