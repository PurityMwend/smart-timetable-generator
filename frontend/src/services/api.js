/**
 * Axios instance pre-configured for the Django API.
 */
import axios from 'axios'

const api = axios.create({
    baseURL: '/api',
    headers: {
        'Content-Type': 'application/json',
    },
    withCredentials: true,
})

export default api
