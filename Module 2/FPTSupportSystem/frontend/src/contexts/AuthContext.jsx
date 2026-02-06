import { createContext, useContext, useState, useEffect } from 'react'

const API_BASE = 'http://localhost:8000/api/v1'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null)
    const [token, setToken] = useState(localStorage.getItem('token'))
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    // Fetch user info on mount if token exists
    useEffect(() => {
        if (token) {
            fetchUser()
        } else {
            setLoading(false)
        }
    }, [token])

    const fetchUser = async () => {
        try {
            const response = await fetch(`${API_BASE}/users/me`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            })

            if (response.ok) {
                const userData = await response.json()
                setUser(userData)
            } else {
                // Token invalid
                logout()
            }
        } catch (err) {
            console.error('Failed to fetch user:', err)
            logout()
        } finally {
            setLoading(false)
        }
    }

    const login = async (email, password) => {
        setError(null)
        try {
            const formData = new URLSearchParams()
            formData.append('username', email)
            formData.append('password', password)

            const response = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: formData
            })

            if (!response.ok) {
                const data = await response.json()
                throw new Error(data.detail || 'Login failed')
            }

            const data = await response.json()
            localStorage.setItem('token', data.access_token)
            setToken(data.access_token)

            return true
        } catch (err) {
            setError(err.message)
            return false
        }
    }

    const register = async (email, password, name) => {
        setError(null)
        try {
            const response = await fetch(`${API_BASE}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password, name })
            })

            if (!response.ok) {
                const data = await response.json()
                throw new Error(data.detail || 'Registration failed')
            }

            const data = await response.json()
            localStorage.setItem('token', data.access_token)
            setToken(data.access_token)

            return true
        } catch (err) {
            setError(err.message)
            return false
        }
    }

    const logout = () => {
        localStorage.removeItem('token')
        setToken(null)
        setUser(null)
    }

    const value = {
        user,
        token,
        loading,
        error,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        clearError: () => setError(null)
    }

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    )
}

export function useAuth() {
    const context = useContext(AuthContext)
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider')
    }
    return context
}
