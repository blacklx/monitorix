import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import axios from 'axios'
import { formatShortDateTime } from '../utils/dateFormat'
import './Backup.css'

const API_URL = import.meta.env.REACT_APP_API_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000'

const Backup = () => {
  const { t } = useTranslation()
  const [backups, setBackups] = useState([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [restoring, setRestoring] = useState(null)
  const [deleting, setDeleting] = useState(null)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  useEffect(() => {
    fetchBackups()
    const interval = setInterval(fetchBackups, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const fetchBackups = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/backup/list`)
      setBackups(response.data)
    } catch (error) {
      console.error('Failed to fetch backups:', error)
      setError(error.response?.data?.detail || t('backup.fetchError'))
    } finally {
      setLoading(false)
    }
  }

  const handleCreateBackup = async () => {
    setCreating(true)
    setError(null)
    setSuccess(null)
    try {
      const response = await axios.post(`${API_URL}/api/backup/create`)
      setSuccess(t('backup.createSuccess', { filename: response.data.filename }))
      fetchBackups()
    } catch (error) {
      console.error('Failed to create backup:', error)
      setError(error.response?.data?.detail || t('backup.createError'))
    } finally {
      setCreating(false)
    }
  }

  const handleRestore = async (filename) => {
    if (!window.confirm(t('backup.restoreConfirm', { filename }))) {
      return
    }
    
    setRestoring(filename)
    setError(null)
    setSuccess(null)
    try {
      const response = await axios.post(`${API_URL}/api/backup/restore/${filename}`)
      setSuccess(t('backup.restoreSuccess', { filename }))
      // Refresh page after a delay to show updated data
      setTimeout(() => {
        window.location.reload()
      }, 2000)
    } catch (error) {
      console.error('Failed to restore backup:', error)
      setError(error.response?.data?.detail || t('backup.restoreError'))
    } finally {
      setRestoring(null)
    }
  }

  const handleDownload = async (filename) => {
    try {
      const response = await axios.get(`${API_URL}/api/backup/download/${filename}`, {
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      console.error('Failed to download backup:', error)
      setError(error.response?.data?.detail || t('backup.downloadError'))
    }
  }

  const handleDelete = async (filename) => {
    if (!window.confirm(t('backup.deleteConfirm', { filename }))) {
      return
    }
    
    setDeleting(filename)
    setError(null)
    setSuccess(null)
    try {
      await axios.delete(`${API_URL}/api/backup/${filename}`)
      setSuccess(t('backup.deleteSuccess', { filename }))
      fetchBackups()
    } catch (error) {
      console.error('Failed to delete backup:', error)
      setError(error.response?.data?.detail || t('backup.deleteError'))
    } finally {
      setDeleting(null)
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  const formatDate = (dateString) => {
    return formatShortDateTime(dateString)
  }

  if (loading) {
    return <div className="loading">{t('common.loading')}</div>
  }

  return (
    <div className="backup">
      <div className="page-header">
        <h1>{t('backup.title')}</h1>
        <button 
          className="add-button" 
          onClick={handleCreateBackup}
          disabled={creating}
        >
          {creating ? t('backup.creating') : t('backup.createBackup')}
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

      <div className="backup-info">
        <p>{t('backup.description')}</p>
        <p className="backup-warning">{t('backup.warning')}</p>
      </div>

      <div className="backups-list">
        <h2>{t('backup.availableBackups')}</h2>
        {backups.length === 0 ? (
          <div className="no-backups">
            <p>{t('backup.noBackups')}</p>
          </div>
        ) : (
          <table className="backups-table">
            <thead>
              <tr>
                <th>{t('backup.filename')}</th>
                <th>{t('backup.size')}</th>
                <th>{t('backup.createdAt')}</th>
                <th>{t('common.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {backups.map((backup) => (
                <tr key={backup.filename}>
                  <td>{backup.filename}</td>
                  <td>{formatFileSize(backup.size)}</td>
                  <td>{formatDate(backup.created_at)}</td>
                  <td>
                    <div className="backup-actions">
                      <button
                        className="action-button download-button"
                        onClick={() => handleDownload(backup.filename)}
                        title={t('backup.download')}
                      >
                        {t('backup.download')}
                      </button>
                      <button
                        className="action-button restore-button"
                        onClick={() => handleRestore(backup.filename)}
                        disabled={restoring === backup.filename}
                        title={t('backup.restore')}
                      >
                        {restoring === backup.filename ? t('backup.restoring') : t('backup.restore')}
                      </button>
                      <button
                        className="action-button delete-button"
                        onClick={() => handleDelete(backup.filename)}
                        disabled={deleting === backup.filename}
                        title={t('common.delete')}
                      >
                        {deleting === backup.filename ? t('common.deleting') : t('common.delete')}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

export default Backup

