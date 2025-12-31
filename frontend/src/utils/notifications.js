/**
 * Copyright 2024 Monitorix Contributors
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *     http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * Request browser notification permission
 * @returns {Promise<boolean>} True if permission granted
 */
export const requestNotificationPermission = async () => {
  if (!('Notification' in window)) {
    console.warn('This browser does not support notifications')
    return false
  }

  if (Notification.permission === 'granted') {
    return true
  }

  if (Notification.permission === 'denied') {
    console.warn('Notification permission denied')
    return false
  }

  // Request permission
  const permission = await Notification.requestPermission()
  return permission === 'granted'
}

/**
 * Show a browser notification
 * @param {string} title - Notification title
 * @param {object} options - Notification options
 * @returns {Notification|null} Notification object or null if not supported/permitted
 */
export const showNotification = (title, options = {}) => {
  if (!('Notification' in window)) {
    return null
  }

  if (Notification.permission !== 'granted') {
    return null
  }

  const defaultOptions = {
    icon: '/favicon.ico',
    badge: '/favicon.ico',
    tag: 'monitorix-notification',
    requireInteraction: false,
    ...options
  }

  try {
    const notification = new Notification(title, defaultOptions)
    
    // Auto-close after 5 seconds if not requireInteraction
    if (!defaultOptions.requireInteraction) {
      setTimeout(() => {
        notification.close()
      }, 5000)
    }

    // Handle click
    notification.onclick = () => {
      window.focus()
      notification.close()
    }

    return notification
  } catch (error) {
    console.error('Failed to show notification:', error)
    return null
  }
}

/**
 * Show alert notification
 * @param {object} alert - Alert object
 * @param {function} t - Translation function
 */
export const showAlertNotification = (alert, t) => {
  const severityEmoji = {
    critical: '🔴',
    warning: '⚠️',
    info: 'ℹ️'
  }

  const emoji = severityEmoji[alert.severity] || '📢'
  const title = `${emoji} ${t('alerts.title')}`
  
  const body = alert.message || alert.title || 'New alert'
  
  showNotification(title, {
    body,
    tag: `alert-${alert.id}`,
    requireInteraction: alert.severity === 'critical',
    data: {
      type: 'alert',
      alertId: alert.id,
      severity: alert.severity
    }
  })
}

/**
 * Check if notifications are supported and enabled
 * @returns {boolean}
 */
export const isNotificationSupported = () => {
  return 'Notification' in window
}

/**
 * Check if notifications are permitted
 * @returns {boolean}
 */
export const isNotificationPermitted = () => {
  return Notification.permission === 'granted'
}

