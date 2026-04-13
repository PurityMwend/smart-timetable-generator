/**
 * Axios instance pre-configured for the Django API.
 * Handles authentication, error handling, request/response transformation, and CSRF tokens.
 */
import axios from 'axios'

// Helper function to get CSRF token from cookies
function getCsrfToken() {
    const name = 'csrftoken'
    let cookieValue = null
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';')
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim()
            if (cookie.substring(0, name.length + 1) === name + '=') {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
                break
            }
        }
    }
    return cookieValue
}

const api = axios.create({
    baseURL: '/api',
    headers: {
        'Content-Type': 'application/json',
    },
    withCredentials: true,
    timeout: 30000,
})

// Request interceptor to add CSRF token
api.interceptors.request.use(
    (config) => {
        const csrfToken = getCsrfToken()
        if (csrfToken) {
            config.headers['X-CSRFToken'] = csrfToken
        }
        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// Response interceptor for error handling
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // Unauthorized - redirect to login
            window.location.href = '/login'
        }
        if (error.response?.status === 403) {
            // Forbidden - might be CSRF token issue
            console.error('403 Forbidden:', error.response?.data)
        }
        return Promise.reject(error)
    }
)

export default api
