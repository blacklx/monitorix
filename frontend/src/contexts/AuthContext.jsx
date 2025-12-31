import { createContext, useState, useContext, useEffect } from 'react'
import axios from 'axios'

const AuthContext = createContext(null)

const API_URL = import.meta.env.REACT_APP_API_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('token'))
  const [refreshToken, setRefreshToken] = useState(localStorage.getItem('refreshToken'))
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      fetchUser()
    } else {
      setLoading(false)
    }
  }, [token])

  // Setup axios interceptor for automatic token refresh
  useEffect(() => {
    const interceptor = axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config

        // If error is 401 and we haven't already retried
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true

          // Try to refresh token
          if (refreshToken) {
            try {
              const response = await axios.post(`${API_URL}/api/auth/refresh`, null, {
                params: { refresh_token: refreshToken }
              })
              const { access_token, refresh_token: newRefreshToken } = response.data
              
              setToken(access_token)
              setRefreshToken(newRefreshToken)
              localStorage.setItem('token', access_token)
              localStorage.setItem('refreshToken', newRefreshToken)
              axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`

              // Retry original request
              originalRequest.headers['Authorization'] = `Bearer ${access_token}`
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
      axios.interceptors.response.eject(interceptor)
    }
  }, [refreshToken])

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

  const login = async (username, password) => {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)

    const response = await axios.post(`${API_URL}/api/auth/login`, formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })

    const { access_token, refresh_token } = response.data
    setToken(access_token)
    setRefreshToken(refresh_token)
    localStorage.setItem('token', access_token)
    localStorage.setItem('refreshToken', refresh_token)
    axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
    await fetchUser()
    return true
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

