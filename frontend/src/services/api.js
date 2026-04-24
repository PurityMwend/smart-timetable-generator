/**
 * Axios instance pre-configured for the Django API.
 * Handles authentication, error handling, request/response transformation, and CSRF tokens.
 */
import axios from 'axios'

const AUTH_ENDPOINTS_THAT_CAN_RETURN_401 = [
    '/auth/login/',
    '/auth/register/',
    '/auth/current-user/',
    '/auth/me/',
    '/auth/csrf-token/',
]

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
        const statusCode = error.response?.status
        const requestUrl = error.config?.url || ''
        const isExpectedAuth401 = AUTH_ENDPOINTS_THAT_CAN_RETURN_401.some((endpoint) =>
            requestUrl.includes(endpoint)
        )

        if (statusCode === 401 && !isExpectedAuth401) {
            // Unauthorized on protected endpoints - redirect to login.
            if (window.location.pathname !== '/login') {
                window.location.href = '/login'
            }
        }
        if (statusCode === 403) {
            // Forbidden - might be CSRF token issue
            console.error('403 Forbidden:', error.response?.data)
        }
        return Promise.reject(error)
    }
)

export default api
