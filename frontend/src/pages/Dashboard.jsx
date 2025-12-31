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

  useEffect(() => {
    fetchStats()
    const interval = setInterval(fetchStats, 30000) // Refresh every 30 seconds
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

