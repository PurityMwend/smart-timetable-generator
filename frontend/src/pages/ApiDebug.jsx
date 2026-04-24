import React, { useState } from 'react'
import api from '../services/api'

/**
 * Debug page for testing API endpoints
 * Remove this in production!
 */
const ApiDebug = () => {
    const [testEmail, setTestEmail] = useState('test@admin.cuk.ac.ke')
    const [testPassword, setTestPassword] = useState('testpass123')
    const [response, setResponse] = useState(null)
    const [error, setError] = useState(null)
    const [loading, setLoading] = useState(false)

    const testRegister = async () => {
        setLoading(true)
        setResponse(null)
        setError(null)

        try {
            const res = await api.post('/auth/register/', {
                username: `user_${Date.now()}`,
                email: testEmail,
                password: testPassword,
                password_confirm: testPassword,
                first_name: 'Test',
                last_name: 'User',
            })
            console.log('Register response:', res)
            setResponse(res.data)
        } catch (err) {
            console.error('Register error:', err)
            setError({
                status: err.response?.status,
                data: err.response?.data,
                message: err.message,
            })
        } finally {
            setLoading(false)
        }
    }

    const testLogin = async () => {
        setLoading(true)
        setResponse(null)
        setError(null)

        try {
            const res = await api.post('/auth/login/', {
                username: 'testadmin',
                password: testPassword,
            })
            console.log('Login response:', res)
            setResponse(res.data)
        } catch (err) {
            console.error('Login error:', err)
            setError({
                status: err.response?.status,
                data: err.response?.data,
                message: err.message,
            })
        } finally {
            setLoading(false)
        }
    }

    return (
        <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
            <h2>API Debug Console</h2>

            <div style={{ marginBottom: '20px', padding: '10px', backgroundColor: '#f5f5f5', borderRadius: '5px' }}>
                <h3>Test Registration</h3>
                <div style={{ marginBottom: '10px' }}>
                    <label>
                        Email:
                        <input
                            type="email"
                            value={testEmail}
                            onChange={(e) => setTestEmail(e.target.value)}
                            style={{ marginLeft: '10px', padding: '5px' }}
                        />
                    </label>
                </div>
                <div style={{ marginBottom: '10px' }}>
                    <label>
                        Password:
                        <input
                            type="password"
                            value={testPassword}
                            onChange={(e) => setTestPassword(e.target.value)}
                            style={{ marginLeft: '10px', padding: '5px' }}
                        />
                    </label>
                </div>
                <button onClick={testRegister} disabled={loading}>
                    {loading ? 'Testing...' : 'Test Register'}
                </button>
                <button onClick={testLogin} disabled={loading} style={{ marginLeft: '10px' }}>
                    {loading ? 'Testing...' : 'Test Login'}
                </button>
            </div>

            {error && (
                <div style={{ marginBottom: '20px', padding: '10px', backgroundColor: '#fee', borderRadius: '5px', border: '1px solid #f00' }}>
                    <h4 style={{ color: '#f00' }}>Error</h4>
                    <pre style={{ overflow: 'auto', maxHeight: '300px' }}>
                        {JSON.stringify(error, null, 2)}
                    </pre>
                </div>
            )}

            {response && (
                <div style={{ marginBottom: '20px', padding: '10px', backgroundColor: '#efe', borderRadius: '5px', border: '1px solid #0f0' }}>
                    <h4 style={{ color: '#0f0' }}>Response</h4>
                    <pre style={{ overflow: 'auto', maxHeight: '300px' }}>
                        {JSON.stringify(response, null, 2)}
                    </pre>
                </div>
            )}
        </div>
    )
}

export default ApiDebug
