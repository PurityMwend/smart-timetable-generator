import React, { createContext, useContext, useState, useEffect } from 'react'
import api from '../services/api'

/**
 * Authentication Context
 * Manages user authentication state, login, register, and logout
 */
const AuthContext = createContext(null)

const ROLE_DISPLAY = {
    timetabler: 'Timetabler',
}

const getRoleFromEmail = (email = '') => {
    return 'timetabler'
}

const normalizeUserPayload = (payload) => {
    if (!payload || typeof payload !== 'object') {
        return null
    }

    const rawUser = payload.user && typeof payload.user === 'object'
        ? payload.user
        : payload

    if (!rawUser || typeof rawUser !== 'object') {
        return null
    }

    const role = 'timetabler'

    return {
        ...rawUser,
        role,
        role_display: ROLE_DISPLAY[role],
    }
}

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    // Check if user is already logged in and fetch CSRF token on mount
    useEffect(() => {
        const initializeAuth = async () => {
            try {
                // First, fetch CSRF token
                try {
                    await api.get('/auth/csrf-token/')
                    console.log('CSRF token fetched successfully')
                } catch (err) {
                    console.warn('Could not fetch CSRF token:', err.message)
                }

                // Then check if user is logged in
                const response = await api.get('/auth/current-user/')
                setUser(normalizeUserPayload(response.data))
            } catch (err) {
                // User not logged in
                setUser(null)
            } finally {
                setLoading(false)
            }
        }

        initializeAuth()
    }, [])

    const register = async (username, email, password, passwordConfirm, firstName = '', lastName = '') => {
        setError(null)
        try {
            await api.post('/auth/register/', {
                username,
                email,
                password,
                password_confirm: passwordConfirm,
                first_name: firstName,
                last_name: lastName,
            })
            return {
                success: true,
                message: 'Account created successfully. Please log in with your credentials.',
            }
        } catch (err) {
            console.error('Registration error:', err)
            let message = 'Registration failed'

            // Handle different error response formats
            if (err.response?.data) {
                const data = err.response.data

                // Check for 'error' field
                if (data.error) {
                    message = data.error
                }
                // Check for field-specific errors (dict of field -> list of errors)
                else if (typeof data === 'object') {
                    const errorMessages = []
                    for (const [field, errors] of Object.entries(data)) {
                        if (Array.isArray(errors)) {
                            errorMessages.push(`${field}: ${errors.join(', ')}`)
                        } else if (typeof errors === 'string') {
                            errorMessages.push(`${field}: ${errors}`)
                        }
                    }
                    if (errorMessages.length > 0) {
                        message = errorMessages.join(' | ')
                    }
                }
            } else if (err.message) {
                message = err.message
            }

            setError(message)
            return { success: false, message }
        }
    }

    const login = async (username, password) => {
        setError(null)
        try {
            const response = await api.post('/auth/login/', {
                username,
                password,
            })
            const normalizedUser = normalizeUserPayload(response.data)

            if (!normalizedUser) {
                throw new Error('Login succeeded but user data was missing')
            }

            setUser(normalizedUser)
            return { success: true, message: response.data.message }
        } catch (err) {
            console.error('Login error:', err)
            let message = 'Login failed'

            if (err.response?.data) {
                const data = err.response.data
                if (data.error) {
                    message = data.error
                } else if (typeof data === 'object') {
                    const errorMessages = []
                    for (const [field, errors] of Object.entries(data)) {
                        if (Array.isArray(errors)) {
                            errorMessages.push(errors.join(', '))
                        } else if (typeof errors === 'string') {
                            errorMessages.push(errors)
                        }
                    }
                    if (errorMessages.length > 0) {
                        message = errorMessages.join(' | ')
                    }
                }
            } else if (err.message) {
                message = err.message
            }

            setError(message)
            return { success: false, message }
        }
    }

    const logout = async () => {
        setError(null)
        try {
            await api.post('/auth/logout/')
        } catch (err) {
            console.error('Logout error:', err)
        } finally {
            setUser(null)
        }
    }

    const updateProfile = async (firstName, lastName, newPassword = null, currentPassword = null) => {
        setError(null)
        try {
            const data = {
                first_name: firstName,
                last_name: lastName,
            }
            if (newPassword && currentPassword) {
                data.new_password = newPassword
                data.current_password = currentPassword
            }
            const response = await api.put('/auth/profile/', data)
            setUser(normalizeUserPayload(response.data))
            return { success: true, message: response.data.message }
        } catch (err) {
            const message = err.response?.data?.error || 'Profile update failed'
            setError(message)
            return { success: false, message }
        }
    }

    const value = {
        user,
        loading,
        error,
        register,
        login,
        logout,
        updateProfile,
        isAuthenticated: !!user,
        isTimetabler: !!user,
        isLecturer: false,
        isStudent: false,
    }

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    )
}

export const useAuth = () => {
    const context = useContext(AuthContext)
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider')
    }
    return context
}
