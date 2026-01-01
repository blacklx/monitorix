import { createContext, useState, useContext, useEffect } from 'react'
import axios from 'axios'

const AuthContext = createContext(null)

// Use relative path when running in production (nginx proxy), or full URL for development
// In production, nginx proxies /api to backend:8000
// In development, use full URL if VITE_API_URL is set, otherwise use relative path
// Ensure API_URL is always a string (not undefined)
const API_URL = (import.meta.env.VITE_API_URL || import.meta.env.REACT_APP_API_URL || '').toString()

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('token'))
  const [refreshToken, setRefreshToken] = useState(localStorage.getItem('refreshToken'))
  const [csrfToken, setCsrfToken] = useState(null)
  const [loading, setLoading] = useState(true)

  // Fetch CSRF token on mount
  useEffect(() => {
    fetchCsrfToken()
  }, [])

  const fetchCsrfToken = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/auth/csrf-token`)
      const token = response.data.csrf_token
      setCsrfToken(token)
      // Set default header for all requests
      axios.defaults.headers.common['X-CSRF-Token'] = token
    } catch (error) {
      console.error('Failed to fetch CSRF token:', error)
      // Continue without CSRF token (will fail if CSRF is enabled on backend)
    }
  }

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      fetchUser()
    } else {
      setLoading(false)
    }
  }, [token])

  // Setup axios interceptor for automatic token refresh and CSRF token handling
  useEffect(() => {
    // Request interceptor: Add CSRF token to state-changing requests
    const requestInterceptor = axios.interceptors.request.use(
      (config) => {
        // Add CSRF token to state-changing methods
        if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(config.method?.toUpperCase())) {
          if (csrfToken) {
            config.headers['X-CSRF-Token'] = csrfToken
          }
        }
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor: Handle token refresh and CSRF token errors
    const responseInterceptor = axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config

        // Handle CSRF token errors (403)
        if (error.response?.status === 403 && error.response?.data?.detail?.includes('CSRF')) {
          // Try to fetch new CSRF token and retry
          try {
            await fetchCsrfToken()
            // Get the updated token from axios defaults (set by fetchCsrfToken)
            const updatedToken = axios.defaults.headers.common['X-CSRF-Token']
            if (updatedToken) {
              originalRequest.headers['X-CSRF-Token'] = updatedToken
              return axios(originalRequest)
            }
          } catch (csrfError) {
            console.error('Failed to refresh CSRF token:', csrfError)
          }
        }

        // If error is 401 and we haven't already retried
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true

          // Try to refresh token
          if (refreshToken) {
            try {
              const response = await axios.post(`${API_URL}/api/auth/refresh`, {
                refresh_token: refreshToken
              })
              const { access_token, refresh_token: newRefreshToken } = response.data
              
              setToken(access_token)
              setRefreshToken(newRefreshToken)
              localStorage.setItem('token', access_token)
              localStorage.setItem('refreshToken', newRefreshToken)
              axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`

              // Retry original request with new token and CSRF token
              originalRequest.headers['Authorization'] = `Bearer ${access_token}`
              if (csrfToken) {
                originalRequest.headers['X-CSRF-Token'] = csrfToken
              }
              return axios(originalRequest)
            } catch (refreshError) {
              // Refresh failed, logout user
              logout()
              return Promise.reject(refreshError)
            }
          } else {
            // No refresh token, logout
            logout()
            return Promise.reject(error)
          }
        }

        return Promise.reject(error)
      }
    )

    return () => {
      axios.interceptors.request.eject(requestInterceptor)
      axios.interceptors.response.eject(responseInterceptor)
    }
  }, [refreshToken, csrfToken])

  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/auth/me`)
      setUser(response.data)
    } catch (error) {
      console.error('Failed to fetch user:', error)
      logout()
    } finally {
      setLoading(false)
    }
  }

      const login = async (username, password, totpToken = null) => {
        try {
          console.log(`[AuthContext] Attempting login for user: ${username}`)
          console.log(`[AuthContext] API_URL: ${API_URL}`)
          
          // If TOTP token is provided, use the verify-2fa endpoint
          if (totpToken) {
            console.log(`[AuthContext] Using 2FA login endpoint`)
            const response = await axios.post(`${API_URL}/api/auth/login/verify-2fa`, {
              username,
              password,
              totp_token: totpToken
            })
            const { access_token, refresh_token } = response.data
            setToken(access_token)
            setRefreshToken(refresh_token)
            localStorage.setItem('token', access_token)
            localStorage.setItem('refreshToken', refresh_token)
            axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
            await fetchUser()
            return true
          } else {
            // Regular login - use URLSearchParams for OAuth2PasswordRequestForm
            console.log(`[AuthContext] Using regular login endpoint: ${API_URL}/api/auth/login`)
            const params = new URLSearchParams()
            params.append('username', username)
            params.append('password', password)

            console.log(`[AuthContext] Sending login request...`)
            const response = await axios.post(`${API_URL}/api/auth/login`, params, {
              headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
              },
            })
            console.log(`[AuthContext] Login response received:`, response.status)

            // Check if 2FA is required
            if (response.data.requires_2fa) {
              return { requires_2fa: true }
            }

            const { access_token, refresh_token } = response.data
            setToken(access_token)
            setRefreshToken(refresh_token)
            localStorage.setItem('token', access_token)
            localStorage.setItem('refreshToken', refresh_token)
            axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
            await fetchUser()
            return true
          }
        } catch (error) {
          console.error(`[AuthContext] Login error:`, error)
          console.error(`[AuthContext] Error message:`, error.message)
          console.error(`[AuthContext] Error response:`, error.response)
          console.error(`[AuthContext] Error request:`, error.request)
          
          // Check if error indicates 2FA is required
          if (error.response?.status === 401 && error.response?.data?.detail?.includes('2FA')) {
            return { requires_2fa: true }
          }
          
          // Log network errors
          if (error.request && !error.response) {
            console.error(`[AuthContext] Network error - request did not reach server`)
            console.error(`[AuthContext] Request URL: ${error.config?.url}`)
            console.error(`[AuthContext] Request method: ${error.config?.method}`)
          }
          
          throw error
        }
      }

  const logout = async () => {
    // Call logout endpoint to invalidate refresh token
    if (token) {
      try {
        await axios.post(`${API_URL}/api/auth/logout`)
      } catch (error) {
        // Ignore errors on logout
        console.error('Logout error:', error)
      }
    }
    
    setToken(null)
    setRefreshToken(null)
    setUser(null)
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
    delete axios.defaults.headers.common['Authorization']
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

