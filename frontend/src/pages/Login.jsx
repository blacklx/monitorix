import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../contexts/AuthContext'
import { validateLogin } from '../utils/validation'
import axios from 'axios'
import './Login.css'

const API_URL = import.meta.env.REACT_APP_API_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000'

const Login = () => {
  const { t } = useTranslation()
  const [searchParams] = useSearchParams()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [validationErrors, setValidationErrors] = useState({})
  const [showForgotPassword, setShowForgotPassword] = useState(false)
  const [forgotEmail, setForgotEmail] = useState('')
  const [forgotMessage, setForgotMessage] = useState('')
  const [showResetPassword, setShowResetPassword] = useState(false)
  const [resetToken, setResetToken] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const { login } = useAuth()
  const navigate = useNavigate()

  // Check if reset token is in URL
  useEffect(() => {
    const token = searchParams.get('token')
    if (token) {
      setResetToken(token)
      setShowResetPassword(true)
    }
  }, [searchParams])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setValidationErrors({})

    const validation = validateLogin(username, password)
    if (!validation.isValid) {
      setValidationErrors(validation.errors)
      return
    }

    try {
      await login(username, password)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || t('auth.loginFailed'))
    }
  }

  const handleForgotPassword = async (e) => {
    e.preventDefault()
    setForgotMessage('')
    setError('')

    if (!forgotEmail) {
      setError(t('auth.emailRequired'))
      return
    }
    
    // Validate email format
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(forgotEmail)) {
      setError(t('auth.invalidEmail'))
      return
    }

    try {
      const response = await axios.post(`${API_URL}/api/auth/forgot-password`, null, {
        params: { email: forgotEmail }
      })
      setForgotMessage(response.data.message)
      // Email has been sent (or will be sent if email is configured)
      // User should check their email for the reset link
    } catch (err) {
      setError(err.response?.data?.detail || t('auth.forgotPasswordFailed'))
    }
  }

  const handleResetPassword = async (e) => {
    e.preventDefault()
    setError('')
    setForgotMessage('')

    if (!newPassword || newPassword.length < 8) {
      setError(t('auth.passwordTooShort'))
      return
    }

    if (newPassword !== confirmPassword) {
      setError(t('auth.passwordsDoNotMatch'))
      return
    }

    try {
      await axios.post(`${API_URL}/api/auth/reset-password`, null, {
        params: {
          token: resetToken,
          new_password: newPassword
        }
      })
      setForgotMessage(t('auth.passwordResetSuccess'))
      setShowResetPassword(false)
      setShowForgotPassword(false)
      setResetToken('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (err) {
      setError(err.response?.data?.detail || t('auth.resetPasswordFailed'))
    }
  }

  return (
    <div className="login-container">
      <div className="login-box">
        <h1>Monitorix</h1>
        {!showForgotPassword && !showResetPassword && (
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>{t('auth.username')}</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
              {validationErrors.username && <span className="error-text">{validationErrors.username}</span>}
            </div>
            <div className="form-group">
              <label>{t('auth.password')}</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              {validationErrors.password && <span className="error-text">{validationErrors.password}</span>}
            </div>
            {error && <div className="error">{error}</div>}
            <button type="submit">{t('auth.loginButton')}</button>
            <button
              type="button"
              className="link-button"
              onClick={() => setShowForgotPassword(true)}
            >
              {t('auth.forgotPassword')}
            </button>
          </form>
        )}
        {showForgotPassword && !showResetPassword && (
          <div>
            <h2>{t('auth.forgotPassword')}</h2>
            <form onSubmit={handleForgotPassword}>
              <div className="form-group">
                <label>{t('auth.email')}</label>
                <input
                  type="email"
                  value={forgotEmail}
                  onChange={(e) => setForgotEmail(e.target.value)}
                  required
                />
              </div>
              {error && <div className="error">{error}</div>}
              {forgotMessage && (
                <div className="success">
                  {forgotMessage.split('\n').map((line, i) => (
                    <p key={i}>{line}</p>
                  ))}
                </div>
              )}
              <button type="submit">{t('auth.sendResetLink')}</button>
              <button
                type="button"
                className="link-button"
                onClick={() => {
                  setShowForgotPassword(false)
                  setForgotEmail('')
                  setForgotMessage('')
                  setError('')
                }}
              >
                {t('auth.backToLogin')}
              </button>
            </form>
          </div>
        )}
        {showResetPassword && (
          <div>
            <h2>{t('auth.resetPassword')}</h2>
            <form onSubmit={handleResetPassword}>
              <div className="form-group">
                <label>{t('auth.newPassword')}</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  minLength={8}
                />
              </div>
              <div className="form-group">
                <label>{t('auth.confirmPassword')}</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  minLength={8}
                />
              </div>
              {error && <div className="error">{error}</div>}
              {forgotMessage && <div className="success">{forgotMessage}</div>}
              <button type="submit">{t('auth.resetPassword')}</button>
              <button
                type="button"
                className="link-button"
                onClick={() => {
                  setShowResetPassword(false)
                  setResetToken('')
                  setNewPassword('')
                  setConfirmPassword('')
                  setError('')
                  setForgotMessage('')
                }}
              >
                {t('auth.cancel')}
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  )
}

export default Login

