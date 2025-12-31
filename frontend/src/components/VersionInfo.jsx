import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import axios from 'axios'
import { formatDate as formatDateUtil } from '../utils/dateFormat'
import './VersionInfo.css'

const API_URL = import.meta.env.REACT_APP_API_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000'

const VersionInfo = () => {
  const { t } = useTranslation()
  const [version, setVersion] = useState(null)
  const [updateInfo, setUpdateInfo] = useState(null)
  const [checking, setChecking] = useState(false)
  const [showUpdateInfo, setShowUpdateInfo] = useState(false)

  useEffect(() => {
    fetchVersion()
    // Check for updates on mount (only once per session)
    const hasChecked = sessionStorage.getItem('versionChecked')
    if (!hasChecked) {
      // Delay check slightly to avoid blocking initial render
      setTimeout(() => {
        checkForUpdates()
      }, 2000)
      sessionStorage.setItem('versionChecked', 'true')
    }
  }, [])

  const fetchVersion = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/version`)
      setVersion(response.data.version)
    } catch (error) {
      console.error('Failed to fetch version:', error)
    }
  }

  const checkForUpdates = async () => {
    setChecking(true)
    try {
      const token = localStorage.getItem('token')
      const headers = token ? { Authorization: `Bearer ${token}` } : {}
      const response = await axios.get(`${API_URL}/api/version/check`, { headers })
      setUpdateInfo(response.data)
      if (response.data.update_available) {
        setShowUpdateInfo(true)
      }
    } catch (error) {
      // Silently fail - version check is not critical
      console.debug('Failed to check for updates:', error)
    } finally {
      setChecking(false)
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return null
    return formatDateUtil(dateString)
  }

  return (
    <div className="version-info">
      {version && (
        <span className="version-text" title={t('version.currentVersion')}>
          v{version}
        </span>
      )}
      {updateInfo?.update_available && showUpdateInfo && (
        <div className="update-notification">
          <span className="update-badge">🆕</span>
          <span className="update-text">
            {t('version.updateAvailable', { version: updateInfo.latest_version })}
          </span>
          <button 
            className="update-dismiss"
            onClick={() => setShowUpdateInfo(false)}
            title={t('version.dismiss')}
          >
            ×
          </button>
          {updateInfo.release_url && (
            <a 
              href={updateInfo.release_url} 
              target="_blank" 
              rel="noopener noreferrer"
              className="update-link"
            >
              {t('version.viewRelease')}
            </a>
          )}
        </div>
      )}
      {updateInfo && !updateInfo.update_available && !updateInfo.error && (
        <span className="version-status" title={t('version.upToDate')}>
          ✓
        </span>
      )}
    </div>
  )
}

export default VersionInfo

