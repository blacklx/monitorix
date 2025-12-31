import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../contexts/AuthContext'
import { validateLogin, validateRegister } from '../utils/validation'
import './Login.css'

const Login = () => {
  const { t } = useTranslation()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isRegistering, setIsRegistering] = useState(false)
  const [email, setEmail] = useState('')
  const [validationErrors, setValidationErrors] = useState({})
  const { login, register } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setValidationErrors({})

    // Validate form
    let validation
    if (isRegistering) {
      validation = validateRegister(username, email, password)
    } else {
      validation = validateLogin(username, password)
    }

    if (!validation.isValid) {
      setValidationErrors(validation.errors)
      return
    }

    try {
      if (isRegistering) {
        await register(username, email, password)
      } else {
        await login(username, password)
      }
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || t('auth.loginFailed'))
    }
  }

  return (
    <div className="login-container">
      <div className="login-box">
        <h1>Monitorix</h1>
        <form onSubmit={handleSubmit}>
          {isRegistering && (
            <div className="form-group">
              <label>{t('auth.email')}</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          )}
          <div className="form-group">
            <label>{t('auth.username')}</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label>{t('auth.password')}</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          {error && <div className="error">{error}</div>}
          <button type="submit">{isRegistering ? t('auth.registerButton') : t('auth.loginButton')}</button>
          <button
            type="button"
            className="toggle-button"
            onClick={() => setIsRegistering(!isRegistering)}
          >
            {isRegistering ? t('auth.haveAccount') : t('auth.needAccount')}
          </button>
        </form>
      </div>
    </div>
  )
}

export default Login

