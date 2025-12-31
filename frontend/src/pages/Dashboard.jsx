import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import axios from 'axios'
import { useWebSocket } from '../hooks/useWebSocket'
import LoadingSpinner from '../components/LoadingSpinner'
import { handleApiError, getErrorMessage } from '../utils/errorHandler'
import './Dashboard.css'

const API_URL = import.meta.env.REACT_APP_API_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000'

const Dashboard = () => {
  const { t } = useTranslation()
  const [stats, setStats] = useState(null)
  const [systemMetrics, setSystemMetrics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useWebSocket((data) => {
    if (data.type === 'stats_update') {
      fetchStats()
    }
  })

  const fetchStats = async () => {
    try {
      setError(null)
      const response = await axios.get(`${API_URL}/api/dashboard/stats`)
      setStats(response.data)
    } catch (err) {
      handleApiError(err, setError, 'Dashboard.fetchStats')
    } finally {
      setLoading(false)
    }
  }

  const fetchSystemMetrics = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/system-metrics/summary`)
      setSystemMetrics(response.data)
    } catch (err) {
      // System metrics are optional, don't show error
      console.error('Failed to fetch system metrics:', err)
    }
  }

  useEffect(() => {
    fetchStats()
    fetchSystemMetrics()
    const interval = setInterval(() => {
      fetchStats()
      fetchSystemMetrics()
    }, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return <LoadingSpinner message={t('common.loading')} />
  }

  if (error) {
    return <div className="error">{error}</div>
  }

  if (!stats) {
    return <div className="error">{t('common.error')}</div>
  }

  const formatUptime = (seconds) => {
    if (!seconds) return '0 ' + t('dashboard.minutes')
    const days = Math.floor(seconds / 86400)
    const hours = Math.floor((seconds % 86400) / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    
    if (days > 0) {
      return `${days} ${t('dashboard.days')} ${hours} ${t('dashboard.hours')}`
    } else if (hours > 0) {
      return `${hours} ${t('dashboard.hours')} ${minutes} ${t('dashboard.minutes')}`
    } else {
      return `${minutes} ${t('dashboard.minutes')}`
    }
  }

  return (
    <div className="dashboard">
      <h1>{t('dashboard.title')}</h1>
      <div className="stats-grid">
        <StatCard
          title={t('dashboard.nodes')}
          value={`${stats.online_nodes}/${stats.total_nodes}`}
          subtitle={t('dashboard.online')}
          color="#3498db"
        />
        <StatCard
          title={t('dashboard.vms')}
          value={`${stats.running_vms}/${stats.total_vms}`}
          subtitle={t('dashboard.running')}
          color="#2ecc71"
        />
        <StatCard
          title={t('dashboard.services')}
          value={`${stats.healthy_services}/${stats.total_services}`}
          subtitle={t('dashboard.healthy')}
          color="#27ae60"
        />
        <StatCard
          title={t('dashboard.alerts')}
          value={stats.active_alerts}
          subtitle={t('dashboard.active')}
          color={stats.active_alerts > 0 ? '#e74c3c' : '#95a5a6'}
        />
      </div>
      
      {systemMetrics && !systemMetrics.error && (
        <div className="system-metrics-section">
          <h2>{t('dashboard.systemMetrics')}</h2>
          <div className="stats-grid">
            <StatCard
              title={t('dashboard.cpu')}
              value={`${systemMetrics.cpu_percent?.toFixed(1) || 0}%`}
              subtitle={t('dashboard.usage')}
              color={systemMetrics.cpu_percent > 80 ? '#e74c3c' : systemMetrics.cpu_percent > 60 ? '#f39c12' : '#2ecc71'}
            />
            <StatCard
              title={t('dashboard.memory')}
              value={`${systemMetrics.memory_percent?.toFixed(1) || 0}%`}
              subtitle={`${systemMetrics.memory_used_gb || 0} / ${systemMetrics.memory_total_gb || 0} ${t('dashboard.gb')}`}
              color={systemMetrics.memory_percent > 80 ? '#e74c3c' : systemMetrics.memory_percent > 60 ? '#f39c12' : '#2ecc71'}
            />
            <StatCard
              title={t('dashboard.disk')}
              value={`${systemMetrics.disk_percent?.toFixed(1) || 0}%`}
              subtitle={`${systemMetrics.disk_used_gb || 0} / ${systemMetrics.disk_total_gb || 0} ${t('dashboard.gb')}`}
              color={systemMetrics.disk_percent > 80 ? '#e74c3c' : systemMetrics.disk_percent > 60 ? '#f39c12' : '#2ecc71'}
            />
            <StatCard
              title={t('dashboard.uptime')}
              value={formatUptime(systemMetrics.uptime_seconds)}
              subtitle={t('dashboard.system')}
              color="#3498db"
            />
          </div>
        </div>
      )}
    </div>
  )
}

const StatCard = ({ title, value, subtitle, color }) => {
  return (
    <div className="stat-card" style={{ borderTopColor: color }}>
      <h3>{title}</h3>
      <div className="stat-value" style={{ color }}>
        {value}
      </div>
      <div className="stat-subtitle">{subtitle}</div>
    </div>
  )
}

export default Dashboard

