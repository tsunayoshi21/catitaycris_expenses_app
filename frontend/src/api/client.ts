import axios from 'axios'
import { useAuthStore } from '../store/authStore'

const apiClient = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

// Request interceptor — attach access token
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor — refresh token on 401
let isRefreshing = false
let refreshSubscribers: ((token: string) => void)[] = []

function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb)
}

function onRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token))
  refreshSubscribers = []
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      const refreshToken = useAuthStore.getState().refreshToken
      if (!refreshToken) {
        useAuthStore.getState().logout()
        window.location.href = '/login'
        return Promise.reject(error)
      }
      if (!isRefreshing) {
        isRefreshing = true
        try {
          const { data } = await axios.post('/api/auth/token/refresh/', { refresh: refreshToken })
          useAuthStore.getState().setTokens(data.access, data.refresh || refreshToken)
          onRefreshed(data.access)
        } catch {
          useAuthStore.getState().logout()
          window.location.href = '/login'
          return Promise.reject(error)
        } finally {
          isRefreshing = false
        }
      }
      return new Promise((resolve) => {
        subscribeTokenRefresh((token) => {
          original.headers.Authorization = `Bearer ${token}`
          resolve(apiClient(original))
        })
      })
    }
    return Promise.reject(error)
  }
)

export default apiClient
