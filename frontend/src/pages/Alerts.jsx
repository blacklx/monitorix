import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import axios from 'axios'
import { formatShortDateTime, formatDateForFilename } from '../utils/dateFormat'
import { requestNotificationPermission, showAlertNotification, isNotificationSupported } from '../utils/notifications'
import { useWebSocket } from '../contexts/WebSocketContext'
import './Alerts.css'

const API_URL = import.meta.env.VITE_API_URL || import.meta.env.REACT_APP_API_URL || ''

const Alerts = () => {
  const { t } = useTranslation()
  const [alerts, setAlerts] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showResolved, setShowResolved] = useState(false)
  const [severityFilter, setSeverityFilter] = useState('all')
  const [typeFilter, setTypeFilter] = useState('all')
  const [selectedAlerts, setSelectedAlerts] = useState(new Set())

  useEffect(() => {
    fetchAlerts()
    fetchStats()
    const interval = setInterval(() => {
      fetchAlerts()
      fetchStats()
    }, 30000)
    return () => clearInterval(interval)
  }, [showResolved, severityFilter, typeFilter])

  const fetchAlerts = async () => {
    try {
      const params = new URLSearchParams()
      if (!showResolved) params.append('resolved', 'false')
      if (severityFilter !== 'all') params.append('severity', severityFilter)
      if (typeFilter !== 'all') params.append('alert_type', typeFilter)
      
      const response = await axios.get(`${API_URL}/api/alerts?${params}`)
      setAlerts(response.data)
    } catch (error) {
      console.error('Failed to fetch alerts:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/alerts/stats`)
      setStats(response.data)
    } catch (error) {
      console.error('Failed to fetch alert stats:', error)
    }
  }

  const handleExportCSV = async () => {
    try {
      const params = new URLSearchParams()
      if (!showResolved) params.append('resolved', 'false')
      if (severityFilter !== 'all') params.append('severity', severityFilter)
      if (typeFilter !== 'all') params.append('alert_type', typeFilter)
      
      const response = await axios.get(`${API_URL}/api/export/alerts/csv?${params}`, {
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `alerts_${formatDateForFilename()}.csv`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      console.error('Failed to export CSV:', error)
    }
  }

  const handleExportJSON = async () => {
    try {
      const params = new URLSearchParams()
      if (!showResolved) params.append('resolved', 'false')
      if (severityFilter !== 'all') params.append('severity', severityFilter)
      if (typeFilter !== 'all') params.append('alert_type', typeFilter)
      
      const response = await axios.get(`${API_URL}/api/export/alerts/json?${params}`, {
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `alerts_${formatDateForFilename()}.json`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      console.error('Failed to export JSON:', error)
    }
  }

  const handleResolve = async (alertId) => {
    try {
      await axios.post(`${API_URL}/api/alerts/${alertId}/resolve`)
      fetchAlerts()
      fetchStats()
    } catch (error) {
      console.error('Failed to resolve alert:', error)
    }
  }

  const handleBulkResolve = async () => {
    if (selectedAlerts.size === 0) return
    
    try {
      await axios.post(`${API_URL}/api/alerts/bulk-resolve`, {
        alert_ids: Array.from(selectedAlerts)
      })
      setSelectedAlerts(new Set())
      fetchAlerts()
      fetchStats()
    } catch (error) {
      console.error('Failed to bulk resolve alerts:', error)
    }
  }

  const handleDelete = async (alertId) => {
    try {
      await axios.delete(`${API_URL}/api/alerts/${alertId}`)
      fetchAlerts()
      fetchStats()
    } catch (error) {
      console.error('Failed to delete alert:', error)
    }
  }

  const toggleSelectAlert = (alertId) => {
    const newSelected = new Set(selectedAlerts)
    if (newSelected.has(alertId)) {
      newSelected.delete(alertId)
    } else {
      newSelected.add(alertId)
    }
    setSelectedAlerts(newSelected)
  }

  const toggleSelectAll = () => {
    if (selectedAlerts.size === alerts.filter(a => !a.is_resolved).length) {
      setSelectedAlerts(new Set())
    } else {
      setSelectedAlerts(new Set(alerts.filter(a => !a.is_resolved).map(a => a.id)))
    }
  }

  if (loading) {
    return <div className="loading">{t('common.loading')}</div>
  }

  return (
    <div className="alerts">
      <div className="page-header">
        <h1>{t('alerts.title')}</h1>
        <div>
          <button className="export-button" onClick={handleExportCSV} style={{ marginRight: '10px' }}>
            {t('common.exportCSV')}
          </button>
          <button className="export-button" onClick={handleExportJSON}>
            {t('common.exportJSON')}
          </button>
        </div>
        <div className="header-actions">
          {stats && (
            <div className="alert-stats">
              <span className="stat-item critical">{stats.critical} {t('alerts.critical')}</span>
              <span className="stat-item warning">{stats.warning} {t('alerts.warning')}</span>
              <span className="stat-item total">{stats.unresolved} {t('alerts.unresolved')}</span>
            </div>
          )}
          {isNotificationSupported() && (
            <label className="toggle-notifications" title={notificationsEnabled ? t('alerts.notificationsEnabled') : t('alerts.notificationsDisabled')}>
              <input
                type="checkbox"
                checked={notificationsEnabled}
                onChange={async (e) => {
                  if (e.target.checked) {
                    const enabled = await requestNotificationPermission()
                    setNotificationsEnabled(enabled)
                  } else {
                    setNotificationsEnabled(false)
                  }
                }}
              />
              🔔 {notificationsEnabled ? t('alerts.notificationsEnabled') : t('alerts.enableNotifications')}
            </label>
          )}
          <label className="toggle-resolved">
            <input
              type="checkbox"
              checked={showResolved}
              onChange={(e) => setShowResolved(e.target.checked)}
            />
            {t('alerts.showResolved')}
          </label>
        </div>
      </div>

      <div className="alerts-filters">
        <div className="filter-group">
          <label>{t('alerts.severity')}</label>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
          >
            <option value="all">{t('common.all')}</option>
            <option value="critical">{t('alerts.severity.critical')}</option>
            <option value="warning">{t('alerts.severity.warning')}</option>
            <option value="info">{t('alerts.severity.info')}</option>
          </select>
        </div>
        <div className="filter-group">
          <label>{t('alerts.type')}</label>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          >
            <option value="all">{t('common.all')}</option>
            <option value="node_down">{t('alerts.type.node_down')}</option>
            <option value="service_down">{t('alerts.type.service_down')}</option>
            <option value="vm_down">{t('alerts.type.vm_down')}</option>
            <option value="high_usage">{t('alerts.type.high_usage')}</option>
          </select>
        </div>
        {selectedAlerts.size > 0 && (
          <button className="bulk-resolve-button" onClick={handleBulkResolve}>
            {t('alerts.resolveSelected')} ({selectedAlerts.size})
          </button>
        )}
      </div>
      <div className="alerts-list">
        {alerts.length === 0 ? (
          <div className="no-alerts">{t('alerts.noAlerts')}</div>
        ) : (
          <>
            {!showResolved && alerts.filter(a => !a.is_resolved).length > 0 && (
              <div className="bulk-select">
                <label>
                  <input
                    type="checkbox"
                    checked={selectedAlerts.size === alerts.filter(a => !a.is_resolved).length}
                    onChange={toggleSelectAll}
                  />
                  {t('alerts.selectAll')}
                </label>
              </div>
            )}
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className={`alert-card ${alert.severity} ${
                  alert.is_resolved ? 'resolved' : ''
                }`}
              >
                {!alert.is_resolved && (
                  <input
                    type="checkbox"
                    className="alert-checkbox"
                    checked={selectedAlerts.has(alert.id)}
                    onChange={() => toggleSelectAlert(alert.id)}
                  />
                )}
                <div className="alert-content">
                  <div className="alert-header">
                    <div>
                      <h2>{alert.title}</h2>
                      <span className={`severity-badge ${alert.severity}`}>
                        {t(`alerts.severity.${alert.severity}`)}
                      </span>
                    </div>
                    <div className="alert-actions">
                      {!alert.is_resolved && (
                        <button
                          className="resolve-button"
                          onClick={() => handleResolve(alert.id)}
                        >
                          {t('alerts.resolve')}
                        </button>
                      )}
                      <button
                        className="delete-button"
                        onClick={() => handleDelete(alert.id)}
                        title={t('common.delete')}
                      >
                        ×
                      </button>
                    </div>
                  </div>
                  <p className="alert-message">{alert.message}</p>
                  <div className="alert-footer">
                    <span className="alert-type">{t(`alerts.type.${alert.alert_type}`)}</span>
                    <span className="alert-time">
                      {formatShortDateTime(alert.created_at)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  )
}

export default Alerts

