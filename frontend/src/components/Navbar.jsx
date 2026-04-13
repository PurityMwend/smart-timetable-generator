import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './Navbar.css'

const Navbar = () => {
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
    const [userMenuOpen, setUserMenuOpen] = useState(false)
    const { user, logout, isAuthenticated, isTimetabler, isLecturer, isStudent } = useAuth()
    const navigate = useNavigate()

    const handleLogout = async () => {
        await logout()
        setUserMenuOpen(false)
        navigate('/login')
    }

    return (
        <nav className="navbar">
            <div className="navbar-container">
                {/* Logo */}
                <Link to="/" className="navbar-logo">
                    <span className="logo-icon">📅</span>
                    <span className="logo-text">Smart Timetable</span>
                </Link>

                {/* Mobile menu toggle */}
                <button
                    className="navbar-toggle"
                    onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                    aria-label="Toggle menu"
                >
                    <span></span>
                    <span></span>
                    <span></span>
                </button>

                {/* Navigation items */}
                <div className={`navbar-menu ${mobileMenuOpen ? 'active' : ''}`}>
                    {isAuthenticated && (
                        <>
                            <Link to="/" className="nav-link">
                                Dashboard
                            </Link>

                            {/* Students see course information and timetable */}
                            {isStudent && (
                                <Link to="/student-info" className="nav-link">
                                    Course Info
                                </Link>
                            )}

                            {/* Lecturers and timetablers can access data management */}
                            {(isTimetabler || isLecturer) && (
                                <Link to="/data" className="nav-link">
                                    Data Manager
                                </Link>
                            )}

                            {/* Only timetablers can access training data and generation */}
                            {isTimetabler && (
                                <>
                                    <Link to="/training-data" className="nav-link">
                                        Training Data
                                    </Link>
                                    <Link to="/generate" className="nav-link">
                                        Generate
                                    </Link>
                                </>
                            )}

                            {/* All authenticated users can view timetables */}
                            <Link to="/view" className="nav-link">
                                Timetable
                            </Link>
                        </>
                    )}
                </div>

                {/* User menu */}
                <div className="navbar-user">
                    {isAuthenticated ? (
                        <div className="user-menu-wrapper">
                            <button
                                className="user-button"
                                onClick={() => setUserMenuOpen(!userMenuOpen)}
                            >
                                <span className="user-avatar">
                                    {user?.first_name?.charAt(0) || user?.username?.charAt(0) || '👤'}
                                </span>
                                <span className="user-info">
                                    <span className="user-name">
                                        {user?.first_name || user?.username}
                                    </span>
                                    <span className="user-role">{user?.role_display}</span>
                                </span>
                            </button>

                            {userMenuOpen && (
                                <div className="user-dropdown">
                                    <div className="dropdown-header">
                                        <strong>{user?.username}</strong>
                                        <small>{user?.email}</small>
                                    </div>
                                    <hr />
                                    <button className="dropdown-item" onClick={() => {
                                        navigate('/profile')
                                        setUserMenuOpen(false)
                                    }}>
                                        👤 Profile
                                    </button>
                                    <button className="dropdown-item" onClick={() => {
                                        navigate('/settings')
                                        setUserMenuOpen(false)
                                    }}>
                                        ⚙️ Settings
                                    </button>
                                    <hr />
                                    <button className="dropdown-item logout" onClick={handleLogout}>
                                        🚪 Logout
                                    </button>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="auth-links">
                            <Link to="/login" className="btn btn-sm btn-outline">
                                Login
                            </Link>
                            <Link to="/register" className="btn btn-sm btn-primary">
                                Register
                            </Link>
                        </div>
                    )}
                </div>
            </div>
        </nav>
    )
}

export default Navbar
