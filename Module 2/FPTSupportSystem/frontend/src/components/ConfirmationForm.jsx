import { useState, useEffect } from 'react'

const ACTION_LABELS = {
    create_ticket: {
        vi: 'Tạo Ticket Hỗ Trợ',
        en: 'Create Support Ticket',
        icon: '📋',
        color: 'from-blue-500 to-blue-600',
        bgColor: 'bg-blue-500/10',
        borderColor: 'border-blue-500/30'
    },
    update_ticket: {
        vi: 'Cập nhật Ticket',
        en: 'Update Ticket',
        icon: '✏️',
        color: 'from-amber-500 to-amber-600',
        bgColor: 'bg-amber-500/10',
        borderColor: 'border-amber-500/30'
    },
    create_booking: {
        vi: 'Đặt Phòng Họp',
        en: 'Book Meeting Room',
        icon: '📅',
        color: 'from-green-500 to-green-600',
        bgColor: 'bg-green-500/10',
        borderColor: 'border-green-500/30'
    },
    update_booking: {
        vi: 'Cập nhật Đặt Phòng',
        en: 'Update Booking',
        icon: '✏️',
        color: 'from-amber-500 to-amber-600',
        bgColor: 'bg-amber-500/10',
        borderColor: 'border-amber-500/30'
    },
    cancel_booking: {
        vi: 'Hủy Đặt Phòng',
        en: 'Cancel Booking',
        icon: '❌',
        color: 'from-red-500 to-red-600',
        bgColor: 'bg-red-500/10',
        borderColor: 'border-red-500/30'
    }
}

const FIELD_ICONS = {
    content: '📝',
    description: '📄',
    customer_name: '👤',
    customer_phone: '📞',
    email: '✉️',
    time: '🕐',
    reason: '💡',
    note: '📌'
}

export default function ConfirmationForm({ action, data, fields, onConfirm, onCancel }) {
    const [formData, setFormData] = useState({})
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [isVisible, setIsVisible] = useState(false)

    useEffect(() => {
        setFormData({ ...data })
        // Trigger entrance animation
        setTimeout(() => setIsVisible(true), 50)
    }, [data])

    const handleChange = (name, value) => {
        setFormData(prev => ({
            ...prev,
            [name]: value
        }))
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setIsSubmitting(true)

        const edits = {}
        Object.keys(formData).forEach(key => {
            if (formData[key] !== data[key]) {
                edits[key] = formData[key]
            }
        })

        await onConfirm(Object.keys(edits).length > 0 ? edits : null)
        setIsSubmitting(false)
    }

    const handleCancel = () => {
        setIsVisible(false)
        setTimeout(onCancel, 200)
    }

    const actionInfo = ACTION_LABELS[action] || {
        vi: action,
        en: action,
        icon: '📝',
        color: 'from-fpt-orange to-orange-500',
        bgColor: 'bg-fpt-orange/10',
        borderColor: 'border-fpt-orange/30'
    }

    const isCancelAction = action === 'cancel_booking'

    return (
        <>
            {/* Backdrop overlay */}
            <div
                className={`fixed inset-0 z-40 bg-black/60 backdrop-blur-sm transition-opacity duration-300 ${isVisible ? 'opacity-100' : 'opacity-0'
                    }`}
                onClick={handleCancel}
            />

            {/* Modal */}
            <div className={`fixed inset-0 z-50 flex items-center justify-center p-4 transition-all duration-300 ${isVisible ? 'opacity-100 scale-100' : 'opacity-0 scale-95'
                }`}>
                <div
                    className="w-full max-w-lg bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl shadow-2xl border border-white/10 overflow-hidden"
                    onClick={(e) => e.stopPropagation()}
                >
                    {/* Header */}
                    <div className={`relative px-6 py-5 bg-gradient-to-r ${actionInfo.color}`}>
                        {/* Decorative circles */}
                        <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2" />
                        <div className="absolute bottom-0 left-0 w-20 h-20 bg-white/5 rounded-full translate-y-1/2 -translate-x-1/2" />

                        <div className="relative flex items-center gap-4">
                            <div className="w-14 h-14 rounded-xl bg-white/20 backdrop-blur flex items-center justify-center shadow-lg">
                                <span className="text-3xl">{actionInfo.icon}</span>
                            </div>
                            <div>
                                <h3 className="text-xl font-bold text-white">{actionInfo.vi}</h3>
                                <p className="text-white/80 text-sm">{actionInfo.en}</p>
                            </div>
                        </div>
                    </div>

                    {/* Content */}
                    <div className="p-6">
                        {/* Info banner */}
                        <div className={`mb-5 p-3 rounded-lg ${actionInfo.bgColor} border ${actionInfo.borderColor} flex items-center gap-3`}>
                            <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center flex-shrink-0">
                                <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </div>
                            <p className="text-sm text-gray-300">
                                {isCancelAction
                                    ? 'Hành động này không thể hoàn tác. Vui lòng xác nhận.'
                                    : 'Vui lòng kiểm tra và chỉnh sửa thông tin nếu cần.'
                                }
                            </p>
                        </div>

                        <form onSubmit={handleSubmit}>
                            {isCancelAction ? (
                                <div className="p-5 rounded-xl bg-red-500/10 border border-red-500/20 mb-5">
                                    <div className="flex items-start gap-4">
                                        <div className="w-12 h-12 rounded-full bg-red-500/20 flex items-center justify-center flex-shrink-0">
                                            <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                            </svg>
                                        </div>
                                        <div>
                                            <h4 className="font-semibold text-red-300 mb-1">Xác nhận hủy đặt phòng</h4>
                                            <p className="text-gray-400 text-sm">
                                                Bạn có chắc chắn muốn hủy đặt phòng <span className="text-white font-medium">#{data.booking_id}</span>?
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="space-y-4 mb-5">
                                    {fields?.map((field, index) => (
                                        <div
                                            key={field.name}
                                            className="group"
                                            style={{ animationDelay: `${index * 50}ms` }}
                                        >
                                            <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
                                                <span className="text-base">{FIELD_ICONS[field.name] || '📝'}</span>
                                                {field.label}
                                                {field.required && (
                                                    <span className="text-red-400 text-xs px-1.5 py-0.5 rounded bg-red-500/10">Bắt buộc</span>
                                                )}
                                            </label>

                                            <div className="relative">
                                                {field.type === 'textarea' ? (
                                                    <textarea
                                                        value={formData[field.name] || ''}
                                                        onChange={(e) => handleChange(field.name, e.target.value)}
                                                        required={field.required}
                                                        rows={3}
                                                        placeholder={`Nhập ${field.label.toLowerCase()}...`}
                                                        className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:border-fpt-orange focus:ring-2 focus:ring-fpt-orange/20 focus:outline-none transition-all duration-200 resize-none"
                                                    />
                                                ) : field.type === 'datetime-local' ? (
                                                    <input
                                                        type="datetime-local"
                                                        value={formData[field.name]?.replace(' ', 'T') || ''}
                                                        onChange={(e) => handleChange(field.name, e.target.value.replace('T', ' '))}
                                                        required={field.required}
                                                        className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white focus:border-fpt-orange focus:ring-2 focus:ring-fpt-orange/20 focus:outline-none transition-all duration-200"
                                                    />
                                                ) : (
                                                    <input
                                                        type={field.type || 'text'}
                                                        value={formData[field.name] || ''}
                                                        onChange={(e) => handleChange(field.name, e.target.value)}
                                                        required={field.required}
                                                        placeholder={`Nhập ${field.label.toLowerCase()}...`}
                                                        className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:border-fpt-orange focus:ring-2 focus:ring-fpt-orange/20 focus:outline-none transition-all duration-200"
                                                    />
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* Action Buttons */}
                            <div className="flex gap-3">
                                <button
                                    type="button"
                                    onClick={handleCancel}
                                    disabled={isSubmitting}
                                    className="flex-1 px-5 py-3.5 rounded-xl font-medium text-gray-300 bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all duration-200 disabled:opacity-50"
                                >
                                    <span className="flex items-center justify-center gap-2">
                                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                        </svg>
                                        Hủy bỏ
                                    </span>
                                </button>

                                <button
                                    type="submit"
                                    disabled={isSubmitting}
                                    className={`flex-1 px-5 py-3.5 rounded-xl font-medium text-white bg-gradient-to-r ${isCancelAction ? 'from-red-500 to-red-600 hover:from-red-600 hover:to-red-700' : actionInfo.color
                                        } shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-200 disabled:opacity-50 disabled:transform-none`}
                                >
                                    {isSubmitting ? (
                                        <span className="flex items-center justify-center gap-2">
                                            <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                            </svg>
                                            Đang xử lý...
                                        </span>
                                    ) : (
                                        <span className="flex items-center justify-center gap-2">
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                            </svg>
                                            {isCancelAction ? 'Xác nhận hủy' : 'Xác nhận'}
                                        </span>
                                    )}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </>
    )
}
