import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import axios from 'axios'
import './AuditLogs.css'

const API_URL = import.meta.env.REACT_APP_API_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000'

const AuditLogs = () => {
  const { t } = useTranslation()
  const [logs, setLogs] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({
    action: '',
    resource_type: '',
    success: '',
    days: 7
  })

  useEffect(() => {
    fetchLogs()
    fetchStats()
    const interval = setInterval(() => {
      fetchLogs()
      fetchStats()
    }, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [filters])

  const fetchLogs = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (filters.action) params.append('action', filters.action)
      if (filters.resource_type) params.append('resource_type', filters.resource_type)
      if (filters.success !== '') params.append('success', filters.success)
      params.append('days', filters.days)
      params.append('limit', '200')

      const response = await axios.get(`${API_URL}/api/audit-logs?${params}`)
      setLogs(response.data)
    } catch (error) {
      console.error('Failed to fetch audit logs:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const params = new URLSearchParams()
      params.append('days', filters.days)
      const response = await axios.get(`${API_URL}/api/audit-logs/stats?${params}`)
      setStats(response.data)
    } catch (error) {
      console.error('Failed to fetch audit stats:', error)
    }
  }

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  const formatDate = (dateString) => {
    return formatShortDateTime(dateString)
  }

  const formatChanges = (changes) => {
    if (!changes) return null
    try {
      return JSON.stringify(changes, null, 2)
    } catch {
      return String(changes)
    }
  }

  if (loading && logs.length === 0) {
    return <div className="loading">{t('common.loading')}</div>
  }

  return (
    <div className="audit-logs">
      <div className="page-header">
        <h1>{t('auditLogs.title')}</h1>
      </div>

      {stats && (
        <div className="audit-stats">
          <div className="stat-card">
            <div className="stat-value">{stats.total}</div>
            <div className="stat-label">{t('auditLogs.totalLogs')}</div>
          </div>
          <div className="stat-card success">
            <div className="stat-value">{stats.successful}</div>
            <div className="stat-label">{t('auditLogs.successful')}</div>
          </div>
          <div className="stat-card error">
            <div className="stat-value">{stats.failed}</div>
            <div className="stat-label">{t('auditLogs.failed')}</div>
          </div>
        </div>
      )}

      <div className="audit-filters">
        <div className="filter-group">
          <label>{t('auditLogs.action')}</label>
          <select
            value={filters.action}
            onChange={(e) => handleFilterChange('action', e.target.value)}
          >
            <option value="">{t('common.all')}</option>
            <option value="create">Create</option>
            <option value="update">Update</option>
            <option value="delete">Delete</option>
            <option value="login">Login</option>
            <option value="logout">Logout</option>
            <option value="restore">Restore</option>
            <option value="backup">Backup</option>
          </select>
        </div>

        <div className="filter-group">
          <label>{t('auditLogs.resourceType')}</label>
          <select
            value={filters.resource_type}
            onChange={(e) => handleFilterChange('resource_type', e.target.value)}
          >
            <option value="">{t('common.all')}</option>
            <option value="user">User</option>
            <option value="node">Node</option>
            <option value="vm">VM</option>
            <option value="service">Service</option>
            <option value="alert">Alert</option>
            <option value="backup">Backup</option>
            <option value="auth">Auth</option>
          </select>
        </div>

        <div className="filter-group">
          <label>{t('auditLogs.status')}</label>
          <select
            value={filters.success}
            onChange={(e) => handleFilterChange('success', e.target.value)}
          >
            <option value="">{t('common.all')}</option>
            <option value="true">{t('auditLogs.successful')}</option>
            <option value="false">{t('auditLogs.failed')}</option>
          </select>
        </div>

        <div className="filter-group">
          <label>{t('auditLogs.timeRange')}</label>
          <select
            value={filters.days}
            onChange={(e) => handleFilterChange('days', parseInt(e.target.value))}
          >
            <option value="1">1 {t('auditLogs.day')}</option>
            <option value="7">7 {t('auditLogs.days')}</option>
            <option value="30">30 {t('auditLogs.days')}</option>
            <option value="90">90 {t('auditLogs.days')}</option>
          </select>
        </div>
      </div>

      <div className="audit-logs-list">
        {logs.length === 0 ? (
          <div className="no-logs">
            <p>{t('auditLogs.noLogs')}</p>
          </div>
        ) : (
          <table className="audit-logs-table">
            <thead>
              <tr>
                <th>{t('auditLogs.timestamp')}</th>
                <th>{t('auditLogs.user')}</th>
                <th>{t('auditLogs.action')}</th>
                <th>{t('auditLogs.resourceType')}</th>
                <th>{t('auditLogs.resource')}</th>
                <th>{t('auditLogs.status')}</th>
                <th>{t('auditLogs.ipAddress')}</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} className={log.success ? '' : 'error-row'}>
                  <td>{formatDate(log.created_at)}</td>
                  <td>{log.username || t('auditLogs.system')}</td>
                  <td>
                    <span className={`action-badge action-${log.action}`}>
                      {log.action}
                    </span>
                  </td>
                  <td>{log.resource_type}</td>
                  <td>
                    {log.resource_name || (log.resource_id ? `ID: ${log.resource_id}` : '-')}
                  </td>
                  <td>
                    <span className={`status-badge ${log.success ? 'success' : 'error'}`}>
                      {log.success ? t('auditLogs.success') : t('auditLogs.failure')}
                    </span>
                  </td>
                  <td>{log.ip_address || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

export default AuditLogs

