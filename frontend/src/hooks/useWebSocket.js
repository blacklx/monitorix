import { useEffect, useRef, useState, useCallback } from 'react'

// Determine WebSocket URL
// Use relative path when running in production (nginx proxy), or full URL for development
const getWebSocketURL = () => {
  const envUrl = import.meta.env.REACT_APP_WS_URL || import.meta.env.VITE_WS_URL
  if (envUrl) {
    return envUrl
  }
  
  // Use relative path - construct from current window location
  // This works when frontend is served by nginx proxy
  if (typeof window !== 'undefined') {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    return `${protocol}//${host}`
  }
  
  // Fallback for SSR or when window is not available
  return 'ws://localhost:8000'
}

const WS_URL = getWebSocketURL()

const RECONNECT_INTERVAL = 3000 // 3 seconds
const MAX_RECONNECT_ATTEMPTS = 10
const RECONNECT_BACKOFF_MULTIPLIER = 1.5
const MAX_RECONNECT_DELAY = 30000 // 30 seconds max delay
const HEARTBEAT_INTERVAL = 30000 // 30 seconds
const HEARTBEAT_TIMEOUT = 10000 // 10 seconds to wait for pong

// WebSocket close codes that should trigger reconnection
const RECONNECTABLE_CLOSE_CODES = [1000, 1001, 1006, 1011, 1012, 1013, 1015]

// Singleton WebSocket manager
class WebSocketManager {
  constructor() {
    this.ws = null
    this.subscribers = new Set()
    this.reconnectTimeout = null
    this.reconnectAttempts = 0
    this.shouldReconnect = true
    this.heartbeatInterval = null
    this.heartbeatTimeout = null
    this.lastPong = Date.now()
    this.connectionState = {
      isConnected: false,
      isReconnecting: false,
      reconnectAttempt: 0,
      connectionError: null
    }
    this.stateListeners = new Set()
  }

  subscribe(callback) {
    this.subscribers.add(callback)
    // If already connected, return immediately
    if (this.ws?.readyState === WebSocket.OPEN) {
      return
    }
    // Start connection if not already connecting/connected
    if (!this.ws || this.ws.readyState === WebSocket.CLOSED) {
      this.connect()
    }
    return () => {
      this.subscribers.delete(callback)
    }
  }

  subscribeToState(listener) {
    this.stateListeners.add(listener)
    // Immediately notify of current state
    listener(this.connectionState)
    return () => {
      this.stateListeners.delete(listener)
    }
  }

  updateState(updates) {
    this.connectionState = { ...this.connectionState, ...updates }
    this.stateListeners.forEach(listener => listener(this.connectionState))
  }

  clearHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
    if (this.heartbeatTimeout) {
      clearTimeout(this.heartbeatTimeout)
      this.heartbeatTimeout = null
    }
  }

  startHeartbeat() {
    this.clearHeartbeat()
    
    this.heartbeatInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        const now = Date.now()
        if (now - this.lastPong > HEARTBEAT_TIMEOUT) {
          console.warn('WebSocket heartbeat timeout - connection may be dead')
          if (this.ws) {
            this.ws.close(1006, 'Heartbeat timeout')
          }
          return
        }
        
        try {
          this.ws.send(JSON.stringify({ type: 'ping', timestamp: now }))
          
          this.heartbeatTimeout = setTimeout(() => {
            const timeSinceLastPong = Date.now() - this.lastPong
            if (timeSinceLastPong > HEARTBEAT_TIMEOUT) {
              console.warn('WebSocket pong timeout - closing connection')
              if (this.ws) {
                this.ws.close(1006, 'Pong timeout')
              }
            }
          }, HEARTBEAT_TIMEOUT)
        } catch (error) {
          console.error('Failed to send WebSocket heartbeat:', error)
        }
      }
    }, HEARTBEAT_INTERVAL)
  }

  connect() {
    if (!this.shouldReconnect) return
    if (this.ws?.readyState === WebSocket.CONNECTING || this.ws?.readyState === WebSocket.OPEN) {
      return // Already connecting or connected
    }

    try {
      this.ws = new WebSocket(`${WS_URL}/ws`)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.updateState({
          isConnected: true,
          isReconnecting: false,
          connectionError: null,
          reconnectAttempt: 0
        })
        this.reconnectAttempts = 0
        this.lastPong = Date.now()
        this.startHeartbeat()
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          if (data.type === 'pong') {
            this.lastPong = Date.now()
            if (this.heartbeatTimeout) {
              clearTimeout(this.heartbeatTimeout)
              this.heartbeatTimeout = null
            }
            return
          }
          
          // Notify all subscribers
          this.subscribers.forEach(callback => {
            try {
              callback(data)
            } catch (error) {
              console.error('Error in WebSocket subscriber callback:', error)
            }
          })
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.updateState({
          isConnected: false,
          connectionError: 'Connection error occurred'
        })
      }

      this.ws.onclose = (event) => {
        const { code, reason } = event
        console.log(`WebSocket disconnected: code=${code}, reason=${reason || 'none'}`)
        this.updateState({ isConnected: false })
        this.clearHeartbeat()

        const shouldReconnect = this.shouldReconnect && 
                                this.reconnectAttempts < MAX_RECONNECT_ATTEMPTS &&
                                (RECONNECTABLE_CLOSE_CODES.includes(code) || code === 1006)

        if (shouldReconnect) {
          const baseDelay = RECONNECT_INTERVAL * Math.pow(RECONNECT_BACKOFF_MULTIPLIER, this.reconnectAttempts)
          const delay = Math.min(baseDelay, MAX_RECONNECT_DELAY)
          this.reconnectAttempts++
          this.updateState({
            isReconnecting: true,
            reconnectAttempt: this.reconnectAttempts,
            connectionError: `Disconnected: ${reason || `Code ${code}`}. Reconnecting...`
          })
          
          console.log(`Attempting to reconnect in ${Math.round(delay / 1000)} seconds (attempt ${this.reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`)
          
          this.reconnectTimeout = setTimeout(() => {
            this.connect()
          }, delay)
        } else if (this.reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
          this.updateState({
            isReconnecting: false,
            connectionError: 'Max reconnection attempts reached. Please refresh the page.'
          })
          console.error('Max reconnection attempts reached. Please refresh the page.')
        } else {
          this.updateState({
            isReconnecting: false,
            connectionError: 'Connection closed'
          })
        }
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      this.updateState({
        isConnected: false,
        connectionError: `Connection failed: ${error.message}`
      })
      
      if (this.shouldReconnect && this.reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        const baseDelay = RECONNECT_INTERVAL * Math.pow(RECONNECT_BACKOFF_MULTIPLIER, this.reconnectAttempts)
        const delay = Math.min(baseDelay, MAX_RECONNECT_DELAY)
        this.reconnectAttempts++
        this.updateState({
          isReconnecting: true,
          reconnectAttempt: this.reconnectAttempts
        })
        
        this.reconnectTimeout = setTimeout(() => {
          this.connect()
        }, delay)
      }
    }
  }

  send(message) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(message))
        return true
      } catch (error) {
        console.error('Failed to send WebSocket message:', error)
        return false
      }
    } else {
      console.warn('WebSocket is not connected. Message not sent:', message)
      return false
    }
  }

  reconnect() {
    this.reconnectAttempts = 0
    this.updateState({
      reconnectAttempt: 0,
      connectionError: null
    })
    if (this.ws) {
      this.ws.close(1000, 'Manual reconnect')
    } else {
      this.connect()
    }
  }

  disconnect() {
    this.shouldReconnect = false
    this.clearHeartbeat()
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout)
      this.reconnectTimeout = null
    }
    if (this.ws) {
      this.ws.close(1000, 'Disconnecting')
      this.ws = null
    }
  }
}

// Global singleton instance
const wsManager = new WebSocketManager()

export const useWebSocket = (onMessage) => {
  const onMessageRef = useRef(onMessage)
  const [state, setState] = useState(wsManager.connectionState)

  // Update ref when onMessage changes (without triggering reconnection)
  useEffect(() => {
    onMessageRef.current = onMessage
  }, [onMessage])

  useEffect(() => {
    // Subscribe to messages
    const unsubscribe = wsManager.subscribe((data) => {
      if (onMessageRef.current) {
        onMessageRef.current(data)
      }
    })

    // Subscribe to state changes
    const unsubscribeState = wsManager.subscribeToState((newState) => {
      setState(newState)
    })

    return () => {
      unsubscribe()
      unsubscribeState()
    }
  }, []) // Empty deps - only run once per component mount

  const send = useCallback((message) => {
    return wsManager.send(message)
  }, [])

  const reconnect = useCallback(() => {
    wsManager.reconnect()
  }, [])

  return { 
    send, 
    isConnected: state.isConnected, 
    isReconnecting: state.isReconnecting,
    reconnectAttempt: state.reconnectAttempt,
    connectionError: state.connectionError,
    reconnect 
  }
}

  const clearHeartbeat = useCallback(() => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current)
      heartbeatIntervalRef.current = null
    }
    if (heartbeatTimeoutRef.current) {
      clearTimeout(heartbeatTimeoutRef.current)
      heartbeatTimeoutRef.current = null
    }
  }, [])

  const startHeartbeat = useCallback(() => {
    clearHeartbeat()
    
    heartbeatIntervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        const now = Date.now()
        // Check if we received a pong recently
        if (now - lastPongRef.current > HEARTBEAT_TIMEOUT) {
          console.warn('WebSocket heartbeat timeout - connection may be dead')
          if (wsRef.current) {
            wsRef.current.close(1006, 'Heartbeat timeout')
          }
          return
        }
        
        try {
          wsRef.current.send(JSON.stringify({ type: 'ping', timestamp: now }))
          
          // Set timeout for pong response
          heartbeatTimeoutRef.current = setTimeout(() => {
            const timeSinceLastPong = Date.now() - lastPongRef.current
            if (timeSinceLastPong > HEARTBEAT_TIMEOUT) {
              console.warn('WebSocket pong timeout - closing connection')
              if (wsRef.current) {
                wsRef.current.close(1006, 'Pong timeout')
              }
            }
          }, HEARTBEAT_TIMEOUT)
        } catch (error) {
          console.error('Failed to send WebSocket heartbeat:', error)
        }
      }
    }, HEARTBEAT_INTERVAL)
  }, [clearHeartbeat])

  const connect = useCallback(() => {
    if (!shouldReconnectRef.current) return

    try {
      const ws = new WebSocket(`${WS_URL}/ws`)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('WebSocket connected')
        setIsConnected(true)
        setIsReconnecting(false)
        setConnectionError(null)
        reconnectAttemptsRef.current = 0
        setReconnectAttempt(0)
        lastPongRef.current = Date.now()
        startHeartbeat()
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          
          // Handle heartbeat pong
          if (data.type === 'pong') {
            lastPongRef.current = Date.now()
            if (heartbeatTimeoutRef.current) {
              clearTimeout(heartbeatTimeoutRef.current)
              heartbeatTimeoutRef.current = null
            }
            return
          }
          
          if (onMessage) {
            onMessage(data)
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setIsConnected(false)
        setConnectionError('Connection error occurred')
      }

      ws.onclose = (event) => {
        const { code, reason } = event
        console.log(`WebSocket disconnected: code=${code}, reason=${reason || 'none'}`)
        setIsConnected(false)
        clearHeartbeat()

        // Determine if we should reconnect
        const shouldReconnect = shouldReconnectRef.current && 
                                reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS &&
                                (RECONNECTABLE_CLOSE_CODES.includes(code) || code === 1006) // 1006 = abnormal closure

        if (shouldReconnect) {
          const baseDelay = RECONNECT_INTERVAL * Math.pow(RECONNECT_BACKOFF_MULTIPLIER, reconnectAttemptsRef.current)
          const delay = Math.min(baseDelay, MAX_RECONNECT_DELAY)
          reconnectAttemptsRef.current++
          setReconnectAttempt(reconnectAttemptsRef.current)
          setIsReconnecting(true)
          
          const reasonText = reason || `Code ${code}`
          setConnectionError(`Disconnected: ${reasonText}. Reconnecting...`)
          
          console.log(`Attempting to reconnect in ${Math.round(delay / 1000)} seconds (attempt ${reconnectAttemptsRef.current}/${MAX_RECONNECT_ATTEMPTS})`)
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, delay)
        } else if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
          setIsReconnecting(false)
          setConnectionError('Max reconnection attempts reached. Please refresh the page.')
          console.error('Max reconnection attempts reached. Please refresh the page.')
        } else {
          setIsReconnecting(false)
          setConnectionError('Connection closed')
        }
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      setIsConnected(false)
      setConnectionError(`Connection failed: ${error.message}`)
      
      // Retry connection after delay
      if (shouldReconnectRef.current && reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
        const baseDelay = RECONNECT_INTERVAL * Math.pow(RECONNECT_BACKOFF_MULTIPLIER, reconnectAttemptsRef.current)
        const delay = Math.min(baseDelay, MAX_RECONNECT_DELAY)
        reconnectAttemptsRef.current++
        setReconnectAttempt(reconnectAttemptsRef.current)
        setIsReconnecting(true)
        
        reconnectTimeoutRef.current = setTimeout(() => {
          connect()
        }, delay)
      }
    }
  }, [onMessage, startHeartbeat, clearHeartbeat])

  useEffect(() => {
    shouldReconnectRef.current = true
    connect()

    return () => {
      shouldReconnectRef.current = false
      clearHeartbeat()
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounting')
      }
    }
  }, [connect, clearHeartbeat])

  const send = useCallback((message) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      try {
        wsRef.current.send(JSON.stringify(message))
        return true
      } catch (error) {
        console.error('Failed to send WebSocket message:', error)
        return false
      }
    } else {
      console.warn('WebSocket is not connected. Message not sent:', message)
      return false
    }
  }, [])

  const reconnect = useCallback(() => {
    reconnectAttemptsRef.current = 0
    setReconnectAttempt(0)
    setConnectionError(null)
    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual reconnect')
    } else {
      connect()
    }
  }, [connect])

  return { 
    send, 
    isConnected, 
    isReconnecting,
    reconnectAttempt,
    connectionError,
    reconnect 
  }
}

