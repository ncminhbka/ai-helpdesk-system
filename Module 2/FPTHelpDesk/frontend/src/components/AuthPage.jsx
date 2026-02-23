import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'

export default function AuthPage() {
    const [isLogin, setIsLogin] = useState(true)
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [name, setName] = useState('')
    const [isLoading, setIsLoading] = useState(false)

    const { login, register, error, clearError } = useAuth()

    const handleSubmit = async (e) => {
        e.preventDefault()
        setIsLoading(true)
        clearError()
        try {
            if (isLogin) {
                await login(email, password)
            } else {
                await register(email, password, name)
            }
        } finally {
            setIsLoading(false)
        }
    }

    const toggleMode = () => {
        setIsLogin(!isLogin)
        clearError()
        setEmail('')
        setPassword('')
        setName('')
    }

    return (
        <div className="min-h-screen flex items-center justify-center p-4">
            {/* Background decoration */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-fpt-orange/10 rounded-full blur-3xl"></div>
                <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-fpt-blue/10 rounded-full blur-3xl"></div>
            </div>

            <div className="w-full max-w-md relative">
                {/* Logo & Title */}
                <div className="text-center mb-8">
                    <img src="/logo.png" alt="FPT" className="w-20 h-20 mx-auto mb-4 object-contain" />
                    <h1 className="text-4xl font-bold text-white mb-2">FPT HelpDesk</h1>
                    <p className="text-gray-400">AI-powered customer support assistant</p>
                </div>

                {/* Auth Card */}
                <div className="glass rounded-2xl p-8">
                    <h2 className="text-xl font-semibold text-white mb-6">
                        {isLogin ? 'Welcome Back' : 'Create Account'}
                    </h2>

                    {error && (
                        <div className="mb-4 p-3 rounded-lg bg-red-500/20 border border-red-500/30 text-red-300 text-sm animate-fade-in">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-4">
                        {!isLogin && (
                            <div className="animate-slide-up">
                                <label className="block text-sm font-medium text-gray-300 mb-1">Name</label>
                                <input
                                    type="text"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    className="input-dark"
                                    placeholder="Your name"
                                />
                            </div>
                        )}

                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">Email</label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="input-dark"
                                placeholder="you@example.com"
                                required
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">Password</label>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="input-dark"
                                placeholder="••••••••"
                                required
                                minLength={6}
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full btn-primary py-3 text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isLoading ? (
                                <span className="loading-dots">
                                    <span></span><span></span><span></span>
                                </span>
                            ) : (
                                isLogin ? 'Sign In' : 'Create Account'
                            )}
                        </button>
                    </form>

                    <div className="mt-6 text-center">
                        <button
                            onClick={toggleMode}
                            className="text-gray-400 hover:text-white transition-colors text-sm"
                        >
                            {isLogin ? "Don't have an account? " : "Already have an account? "}
                            <span className="text-fpt-orange font-medium">
                                {isLogin ? 'Sign Up' : 'Sign In'}
                            </span>
                        </button>
                    </div>
                </div>

                <p className="text-center text-gray-500 text-sm mt-8">
                    © 2025 FPT Corporation. All rights reserved.
                </p>
            </div>
        </div>
    )
}
