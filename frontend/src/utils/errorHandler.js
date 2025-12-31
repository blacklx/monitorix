/**
 * Centralized error handling utilities for the frontend
 */

/**
 * Extract user-friendly error message from API error response
 * @param {Error} error - The error object from axios
 * @returns {string} - User-friendly error message
 */
export const getErrorMessage = (error) => {
  // Network errors
  if (!error.response) {
    if (error.message === 'Network Error') {
      return 'Unable to connect to server. Please check your connection.'
    }
    return error.message || 'An unexpected error occurred'
  }

  const response = error.response
  const status = response.status

  // Handle structured error responses from backend
  if (response.data?.error) {
    const errorData = response.data.error
    if (errorData.message) {
      return errorData.message
    }
  }

  // Handle legacy format (detail field)
  if (response.data?.detail) {
    return response.data.detail
  }

  // Handle validation errors
  if (response.data?.error?.details?.validation_errors) {
    const validationErrors = response.data.error.details.validation_errors
    if (validationErrors.length > 0) {
      return validationErrors.map(err => `${err.field}: ${err.message}`).join(', ')
    }
  }

  // Status code based messages
  switch (status) {
    case 400:
      return 'Invalid request. Please check your input.'
    case 401:
      return 'Authentication required. Please log in.'
    case 403:
      return 'You do not have permission to perform this action.'
    case 404:
      return 'The requested resource was not found.'
    case 409:
      return 'A conflict occurred. The resource may already exist.'
    case 422:
      return 'Validation error. Please check your input.'
    case 429:
      return 'Too many requests. Please try again later.'
    case 500:
      return 'An internal server error occurred. Please try again later.'
    case 503:
      return 'Service temporarily unavailable. Please try again later.'
    default:
      return `An error occurred (${status}). Please try again.`
  }
}

/**
 * Log error to console with context
 * @param {Error} error - The error object
 * @param {string} context - Context where the error occurred
 */
export const logError = (error, context = 'Unknown') => {
  console.error(`[${context}] Error:`, {
    message: error.message,
    response: error.response?.data,
    status: error.response?.status,
    stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
  })
}

/**
 * Handle API error with user feedback
 * @param {Error} error - The error object from axios
 * @param {Function} setError - State setter for error message
 * @param {string} context - Context where the error occurred
 */
export const handleApiError = (error, setError, context = 'Unknown') => {
  logError(error, context)
  const message = getErrorMessage(error)
  setError(message)
}

/**
 * Check if error is a network error
 * @param {Error} error - The error object
 * @returns {boolean}
 */
export const isNetworkError = (error) => {
  return !error.response && (error.message === 'Network Error' || error.code === 'ECONNABORTED')
}

/**
 * Check if error is an authentication error
 * @param {Error} error - The error object
 * @returns {boolean}
 */
export const isAuthError = (error) => {
  return error.response?.status === 401 || error.response?.status === 403
}

/**
 * Check if error is a validation error
 * @param {Error} error - The error object
 * @returns {boolean}
 */
export const isValidationError = (error) => {
  return error.response?.status === 422 || error.response?.status === 400
}

