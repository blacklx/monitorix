import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import axios from 'axios'
import { useAuth } from '../contexts/AuthContext'
import './Profile.css'

const API_URL = import.meta.env.REACT_APP_API_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000'

const Profile = () => {
  const { t } = useTranslation()
  const { user, logout } = useAuth()
  const [formData, setFormData] = useState({
    username: '',
    email: ''
  })
  const [passwordData, setPasswordData] = useState({
    old_password: '',
    new_password: '',
    confirm_password: ''
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [activeTab, setActiveTab] = useState('profile')

  useEffect(() => {
    if (user) {
      setFormData({
        username: user.username || '',
        email: user.email || ''
      })
      setLoading(false)
    }
  }, [user])

  const handleProfileUpdate = async (e) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)

    try {
      await axios.put(`${API_URL}/api/auth/me`, formData)
      setSuccess(t('profile.profileUpdated'))
      // Refresh user data
      window.location.reload()
    } catch (error) {
      setError(error.response?.data?.detail || t('common.error'))
    }
  }

  const handlePasswordChange = async (e) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)

    if (passwordData.new_password !== passwordData.confirm_password) {
      setError(t('profile.passwordsDoNotMatch'))
      return
    }

    if (passwordData.new_password.length < 8) {
      setError(t('profile.passwordTooShort'))
      return
    }

    try {
      await axios.put(`${API_URL}/api/auth/change-password`, {
        old_password: passwordData.old_password,
        new_password: passwordData.new_password
      })
      setSuccess(t('profile.passwordChanged'))
      setPasswordData({
        old_password: '',
        new_password: '',
        confirm_password: ''
      })
    } catch (error) {
      setError(error.response?.data?.detail || t('common.error'))
    }
  }

  if (loading) {
    return <div className="loading">{t('common.loading')}</div>
  }

  return (
    <div className="profile">
      <div className="page-header">
        <h1>{t('profile.title')}</h1>
      </div>

      <div className="profile-tabs">
        <button
          className={`tab-button ${activeTab === 'profile' ? 'active' : ''}`}
          onClick={() => setActiveTab('profile')}
        >
          {t('profile.profileInfo')}
        </button>
        <button
          className={`tab-button ${activeTab === 'password' ? 'active' : ''}`}
          onClick={() => setActiveTab('password')}
        >
          {t('profile.changePassword')}
        </button>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {success && (
        <div className="success-message">
          {success}
        </div>
      )}

      {activeTab === 'profile' && (
        <div className="profile-section">
          <form onSubmit={handleProfileUpdate}>
            <div className="form-group">
              <label>{t('profile.username')}</label>
              <input
                type="text"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                required
              />
            </div>

            <div className="form-group">
              <label>{t('profile.email')}</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
              />
            </div>

            <div className="form-group">
              <label>{t('profile.role')}</label>
              <div className="role-info">
                {user?.is_admin ? (
                  <span className="admin-badge">{t('profile.admin')}</span>
                ) : (
                  <span>{t('profile.user')}</span>
                )}
              </div>
            </div>

            <div className="form-actions">
              <button type="submit">
                {t('common.save')}
              </button>
            </div>
          </form>
        </div>
      )}

      {activeTab === 'password' && (
        <div className="profile-section">
          <form onSubmit={handlePasswordChange}>
            <div className="form-group">
              <label>{t('profile.currentPassword')}</label>
              <input
                type="password"
                value={passwordData.old_password}
                onChange={(e) => setPasswordData({ ...passwordData, old_password: e.target.value })}
                required
              />
            </div>

            <div className="form-group">
              <label>{t('profile.newPassword')}</label>
              <input
                type="password"
                value={passwordData.new_password}
                onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                required
                minLength={8}
              />
              <small>{t('profile.passwordMinLength')}</small>
            </div>

            <div className="form-group">
              <label>{t('profile.confirmPassword')}</label>
              <input
                type="password"
                value={passwordData.confirm_password}
                onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                required
                minLength={8}
              />
            </div>

            <div className="form-actions">
              <button type="submit">
                {t('profile.changePassword')}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}

export default Profile

