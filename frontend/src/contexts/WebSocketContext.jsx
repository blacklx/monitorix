import { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react'

const WebSocketContext = createContext(null)

// Determine WebSocket URL
const getWebSocketURL = () => {
  const envUrl = import.meta.env.REACT_APP_WS_URL || import.meta.env.VITE_WS_URL
  if (envUrl) {
    return envUrl
  }
  
  // Use relative path - construct from current window location
  if (typeof window !== 'undefined' && window.location) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    return `${protocol}//${host}`
  }
  
  // Fallback for SSR or when window is not available
  return 'ws://localhost:8000'
}

const RECONNECT_INTERVAL = 3000 // 3 seconds
const MAX_RECONNECT_ATTEMPTS = 10
const RECONNECT_BACKOFF_MULTIPLIER = 1.5
const MAX_RECONNECT_DELAY = 30000 // 30 seconds max delay
const HEARTBEAT_INTERVAL = 30000 // 30 seconds
const HEARTBEAT_TIMEOUT = 10000 // 10 seconds to wait for pong

// WebSocket close codes that should trigger reconnection
const RECONNECTABLE_CLOSE_CODES = [1000, 1001, 1006, 1011, 1012, 1013, 1015]

export const WebSocketProvider = ({ children }) => {
  const wsRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)
  const reconnectAttemptsRef = useRef(0)
  const shouldReconnectRef = useRef(true)
  const heartbeatIntervalRef = useRef(null)
  const heartbeatTimeoutRef = useRef(null)
  const lastPongRef = useRef(Date.now())
  const messageHandlersRef = useRef(new Set())
  const [isConnected, setIsConnected] = useState(false)
  const [isReconnecting, setIsReconnecting] = useState(false)
  const [reconnectAttempt, setReconnectAttempt] = useState(0)
  const [connectionError, setConnectionError] = useState(null)

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
      const wsUrl = getWebSocketURL()
      const ws = new WebSocket(`${wsUrl}/ws`)
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
          
          // Call all registered message handlers
          messageHandlersRef.current.forEach(handler => {
            try {
              handler(data)
            } catch (error) {
              console.error('Error in WebSocket message handler:', error)
            }
          })
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
                                (RECONNECTABLE_CLOSE_CODES.includes(code) || code === 1006)

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
  }, [startHeartbeat, clearHeartbeat])

  // Register message handler
  const addMessageHandler = useCallback((handler) => {
    messageHandlersRef.current.add(handler)
    return () => {
      messageHandlersRef.current.delete(handler)
    }
  }, [])

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

  // Initialize connection on mount
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
        wsRef.current.close(1000, 'Provider unmounting')
      }
    }
  }, [connect, clearHeartbeat])

  const value = {
    isConnected,
    isReconnecting,
    reconnectAttempt,
    connectionError,
    send,
    reconnect,
    addMessageHandler
  }

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  )
}

export const useWebSocket = (onMessage) => {
  const context = useContext(WebSocketContext)
  if (!context) {
    throw new Error('useWebSocket must be used within WebSocketProvider')
  }

  // Register message handler if provided
  useEffect(() => {
    if (onMessage) {
      return context.addMessageHandler(onMessage)
    }
  }, [onMessage, context])

  return context
}

