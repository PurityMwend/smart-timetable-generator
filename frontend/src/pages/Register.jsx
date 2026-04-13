import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './Auth.css'

const Register = () => {
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
        passwordConfirm: '',
        firstName: '',
        lastName: '',
    })
    const [error, setError] = useState('')
    const [loading, setLoading] = useState(false)
    const navigate = useNavigate()
    const { register } = useAuth()

    const handleChange = (e) => {
        const { name, value } = e.target
        setFormData((prev) => ({
            ...prev,
            [name]: value,
        }))
    }

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')

        // Validate passwords match
        if (formData.password !== formData.passwordConfirm) {
            setError('Passwords do not match')
            return
        }

        setLoading(true)

        const result = await register(
            formData.username,
            formData.email,
            formData.password,
            formData.passwordConfirm,
            formData.firstName,
            formData.lastName
        )
        setLoading(false)

        if (result.success) {
            navigate('/')
        } else {
            setError(result.message)
        }
    }

    return (
        <div className="auth-container">
            <div className="auth-card">
                <h1>Register</h1>
                <form onSubmit={handleSubmit}>
                    <div className="form-row">
                        <div className="form-group">
                            <label htmlFor="firstName">First Name</label>
                            <input
                                type="text"
                                id="firstName"
                                name="firstName"
                                value={formData.firstName}
                                onChange={handleChange}
                                placeholder="First name"
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="lastName">Last Name</label>
                            <input
                                type="text"
                                id="lastName"
                                name="lastName"
                                value={formData.lastName}
                                onChange={handleChange}
                                placeholder="Last name"
                            />
                        </div>
                    </div>

                    <div className="form-group">
                        <label htmlFor="username">Username</label>
                        <input
                            type="text"
                            id="username"
                            name="username"
                            value={formData.username}
                            onChange={handleChange}
                            placeholder="Choose a username"
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="email">Email</label>
                        <input
                            type="email"
                            id="email"
                            name="email"
                            value={formData.email}
                            onChange={handleChange}
                            placeholder="your.email@cuk.ac.ke"
                            required
                        />
                        <small className="help-text">
                            Must be one of: @admin.cuk.ac.ke, @staff.cuk.ac.ke, or @student.cuk.ac.ke
                        </small>
                    </div>

                    <div className="form-group">
                        <label htmlFor="password">Password</label>
                        <input
                            type="password"
                            id="password"
                            name="password"
                            value={formData.password}
                            onChange={handleChange}
                            placeholder="At least 8 characters"
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label htmlFor="passwordConfirm">Confirm Password</label>
                        <input
                            type="password"
                            id="passwordConfirm"
                            name="passwordConfirm"
                            value={formData.passwordConfirm}
                            onChange={handleChange}
                            placeholder="Confirm your password"
                            required
                        />
                    </div>

                    {error && <div className="error-message">{error}</div>}

                    <button type="submit" className="auth-button" disabled={loading}>
                        {loading ? 'Registering...' : 'Register'}
                    </button>
                </form>

                <p className="auth-footer">
                    Already have an account? <Link to="/login">Login here</Link>
                </p>

                <div className="info-box">
                    <h4>Your Role Based On Email:</h4>
                    <ul>
                        <li><strong>@admin.cuk.ac.ke</strong> → Timetabler (Full Access)</li>
                        <li><strong>@staff.cuk.ac.ke</strong> → Lecturer (Can't edit timetables)</li>
                        <li><strong>@student.cuk.ac.ke</strong> → Student (Read-only access)</li>
                    </ul>
                </div>
            </div>
        </div>
    )
}

export default Register
