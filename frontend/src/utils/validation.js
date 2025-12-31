/**
 * Form validation utilities
 */

export const validateNode = (data) => {
  const errors = {}

  if (!data.name || data.name.trim().length === 0) {
    errors.name = 'Name is required'
  } else if (data.name.length < 2) {
    errors.name = 'Name must be at least 2 characters'
  } else if (data.name.length > 100) {
    errors.name = 'Name must be less than 100 characters'
  }

  if (!data.url || data.url.trim().length === 0) {
    errors.url = 'URL is required'
  } else {
    try {
      const url = new URL(data.url)
      if (!['http:', 'https:'].includes(url.protocol)) {
        errors.url = 'URL must use http or https protocol'
      }
    } catch (e) {
      errors.url = 'Invalid URL format'
    }
  }

  if (!data.username || data.username.trim().length === 0) {
    errors.username = 'Username is required'
  } else if (data.username.length < 2) {
    errors.username = 'Username must be at least 2 characters'
  }

  if (!data.token || data.token.trim().length === 0) {
    errors.token = 'Token is required'
  } else if (data.token.length < 10) {
    errors.token = 'Token must be at least 10 characters'
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors
  }
}

export const validateService = (data) => {
  const errors = {}

  if (!data.name || data.name.trim().length === 0) {
    errors.name = 'Name is required'
  } else if (data.name.length < 2) {
    errors.name = 'Name must be at least 2 characters'
  } else if (data.name.length > 100) {
    errors.name = 'Name must be less than 100 characters'
  }

  if (!data.type) {
    errors.type = 'Service type is required'
  } else if (!['http', 'https', 'ping', 'port'].includes(data.type)) {
    errors.type = 'Invalid service type'
  }

  if (!data.target || data.target.trim().length === 0) {
    errors.target = 'Target is required'
  } else {
    if (data.type === 'http' || data.type === 'https') {
      try {
        new URL(data.target.startsWith('http') ? data.target : `${data.type}://${data.target}`)
      } catch (e) {
        errors.target = 'Invalid URL format'
      }
    } else if (data.type === 'ping' || data.type === 'port') {
      // Basic IP/hostname validation
      const hostnameRegex = /^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/
      const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/
      if (!hostnameRegex.test(data.target) && !ipRegex.test(data.target)) {
        errors.target = 'Invalid hostname or IP address'
      }
    }
  }

  if (data.type === 'port' && (!data.port || data.port < 1 || data.port > 65535)) {
    errors.port = 'Port must be between 1 and 65535'
  }

  if ((data.type === 'http' || data.type === 'https') && data.port) {
    if (data.port < 1 || data.port > 65535) {
      errors.port = 'Port must be between 1 and 65535'
    }
  }

  if ((data.type === 'http' || data.type === 'https') && data.expected_status) {
    if (data.expected_status < 100 || data.expected_status > 599) {
      errors.expected_status = 'Status code must be between 100 and 599'
    }
  }

  if (data.check_interval && (data.check_interval < 10 || data.check_interval > 3600)) {
    errors.check_interval = 'Check interval must be between 10 and 3600 seconds'
  }

  if (data.timeout && (data.timeout < 1 || data.timeout > 60)) {
    errors.timeout = 'Timeout must be between 1 and 60 seconds'
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors
  }
}

export const validateLogin = (username, password) => {
  const errors = {}

  if (!username || username.trim().length === 0) {
    errors.username = 'Username is required'
  } else if (username.length < 3) {
    errors.username = 'Username must be at least 3 characters'
  }

  if (!password || password.length === 0) {
    errors.password = 'Password is required'
  } else if (password.length < 6) {
    errors.password = 'Password must be at least 6 characters'
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors
  }
}

export const validateRegister = (username, email, password) => {
  const errors = {}

  if (!username || username.trim().length === 0) {
    errors.username = 'Username is required'
  } else if (username.length < 3) {
    errors.username = 'Username must be at least 3 characters'
  } else if (username.length > 50) {
    errors.username = 'Username must be less than 50 characters'
  } else if (!/^[a-zA-Z0-9_]+$/.test(username)) {
    errors.username = 'Username can only contain letters, numbers, and underscores'
  }

  if (!email || email.trim().length === 0) {
    errors.email = 'Email is required'
  } else {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(email)) {
      errors.email = 'Invalid email format'
    }
  }

  if (!password || password.length === 0) {
    errors.password = 'Password is required'
  } else if (password.length < 8) {
    errors.password = 'Password must be at least 8 characters'
  } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(password)) {
    errors.password = 'Password must contain at least one uppercase letter, one lowercase letter, and one number'
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors
  }
}

