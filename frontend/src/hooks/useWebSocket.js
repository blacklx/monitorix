import { useEffect, useRef, useState, useCallback } from 'react'

const WS_URL = import.meta.env.REACT_APP_WS_URL || import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

const RECONNECT_INTERVAL = 3000 // 3 seconds
const MAX_RECONNECT_ATTEMPTS = 10
const RECONNECT_BACKOFF_MULTIPLIER = 1.5

export const useWebSocket = (onMessage) => {
  const wsRef = useRef(null)
  const reconnectTimeoutRef = useRef(null)
  const reconnectAttemptsRef = useRef(0)
  const shouldReconnectRef = useRef(true)
  const [isConnected, setIsConnected] = useState(false)

  const connect = useCallback(() => {
    if (!shouldReconnectRef.current) return

    try {
      const ws = new WebSocket(`${WS_URL}/ws`)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('WebSocket connected')
        setIsConnected(true)
        reconnectAttemptsRef.current = 0
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
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
      }

      ws.onclose = (event) => {
        console.log('WebSocket disconnected', event.code, event.reason)
        setIsConnected(false)

        // Only reconnect if it wasn't a manual close
        if (shouldReconnectRef.current && reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
          const delay = RECONNECT_INTERVAL * Math.pow(RECONNECT_BACKOFF_MULTIPLIER, reconnectAttemptsRef.current)
          reconnectAttemptsRef.current++
          
          console.log(`Attempting to reconnect in ${Math.round(delay / 1000)} seconds (attempt ${reconnectAttemptsRef.current}/${MAX_RECONNECT_ATTEMPTS})`)
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, delay)
        } else if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
          console.error('Max reconnection attempts reached. Please refresh the page.')
        }
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      setIsConnected(false)
      
      // Retry connection after delay
      if (shouldReconnectRef.current && reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
        const delay = RECONNECT_INTERVAL * Math.pow(RECONNECT_BACKOFF_MULTIPLIER, reconnectAttemptsRef.current)
        reconnectAttemptsRef.current++
        reconnectTimeoutRef.current = setTimeout(() => {
          connect()
        }, delay)
      }
    }
  }, [onMessage])

  useEffect(() => {
    shouldReconnectRef.current = true
    connect()

    return () => {
      shouldReconnectRef.current = false
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [connect])

  const send = useCallback((message) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket is not connected. Message not sent:', message)
    }
  }, [])

  const reconnect = useCallback(() => {
    reconnectAttemptsRef.current = 0
    if (wsRef.current) {
      wsRef.current.close()
    }
    connect()
  }, [connect])

  return { send, isConnected, reconnect }
}

