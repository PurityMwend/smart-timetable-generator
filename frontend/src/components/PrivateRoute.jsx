import React from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

/**
 * PrivateRoute Component
 * Protects routes that require authentication
 */
const PrivateRoute = ({ children, requiredRole = null }) => {
    const { isAuthenticated, loading, isTimetabler, isLecturer } = useAuth()

    if (loading) {
        return (
            <div style={{ padding: '20px', textAlign: 'center' }}>
                <p>Loading...</p>
            </div>
        )
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />
    }

    // Check role-based access
    if (requiredRole === 'timetabler' && !isTimetabler) {
        return <Navigate to="/" replace />
    }

    if (requiredRole === 'lecturer' && !isLecturer && !isTimetabler) {
        return <Navigate to="/" replace />
    }

    return children
}

export default PrivateRoute
