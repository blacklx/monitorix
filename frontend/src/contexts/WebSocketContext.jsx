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

  // Helper function to safely close WebSocket
  const safeCloseWebSocket = useCallback((ws, code = 1000, reason = '') => {
    if (!ws || !(ws instanceof WebSocket)) {
      return
    }
    
    // Only close if WebSocket is in a state where it can be closed
    // OPEN (1) or CONNECTING (0) states can be closed
    // CLOSING (2) or CLOSED (3) states should not be closed again
    if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
      try {
        ws.close(code, reason)
      } catch (error) {
        // Ignore errors when closing - WebSocket might already be closed
        // Only log if it's not a DOMException (which is expected when already closed)
        if (!(error instanceof DOMException)) {
          console.error('Error closing WebSocket:', error)
        }
      }
    }
  }, [])

  const startHeartbeat = useCallback(() => {
    clearHeartbeat()
    
    heartbeatIntervalRef.current = setInterval(() => {
      const ws = wsRef.current
      
      // Check if WebSocket exists and is in a valid state
      if (!ws || !(ws instanceof WebSocket)) {
        clearHeartbeat()
        return
      }
      
      // Only send heartbeat if WebSocket is open
      if (ws.readyState === WebSocket.OPEN) {
        const now = Date.now()
        const timeSinceLastPong = now - lastPongRef.current
        
        // Only check timeout if we've sent at least one ping
        // We check if it's been more than HEARTBEAT_INTERVAL + HEARTBEAT_TIMEOUT since last pong
        // This gives us time to send ping and receive pong
        if (timeSinceLastPong > (HEARTBEAT_INTERVAL + HEARTBEAT_TIMEOUT)) {
          console.warn('WebSocket heartbeat timeout - connection may be dead')
          safeCloseWebSocket(ws, 1006, 'Heartbeat timeout')
          clearHeartbeat()
          return
        }
        
        try {
          // Double-check that WebSocket is still open before sending
          if (ws.readyState === WebSocket.OPEN && typeof ws.send === 'function') {
            ws.send(JSON.stringify({ type: 'ping', timestamp: now }))
            
            // Set timeout for pong response
            heartbeatTimeoutRef.current = setTimeout(() => {
              const timeSinceLastPong = Date.now() - lastPongRef.current
              if (timeSinceLastPong > HEARTBEAT_TIMEOUT) {
                console.warn('WebSocket pong timeout - closing connection')
                const currentWs = wsRef.current
                safeCloseWebSocket(currentWs, 1006, 'Pong timeout')
                clearHeartbeat()
              }
            }, HEARTBEAT_TIMEOUT)
          }
        } catch (error) {
          console.error('Failed to send WebSocket heartbeat:', error)
          // If send fails, clear heartbeat and let reconnection handle it
          clearHeartbeat()
        }
      } else if (ws.readyState === WebSocket.CLOSED || ws.readyState === WebSocket.CLOSING) {
        // WebSocket is closed or closing, clear heartbeat
        clearHeartbeat()
      }
    }, HEARTBEAT_INTERVAL)
  }, [clearHeartbeat, safeCloseWebSocket])

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
        // Set lastPong to now so we don't timeout immediately
        // This will be updated when we receive the first pong
        lastPongRef.current = Date.now()
        // Send initial ping immediately to establish heartbeat
        try {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }))
          }
        } catch (error) {
          console.error('Failed to send initial ping:', error)
        }
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
      safeCloseWebSocket(wsRef.current, 1000, 'Manual reconnect')
    } else {
      connect()
    }
  }, [connect, safeCloseWebSocket])

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
      safeCloseWebSocket(wsRef.current, 1000, 'Provider unmounting')
    }
  }, [connect, clearHeartbeat, safeCloseWebSocket])

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

