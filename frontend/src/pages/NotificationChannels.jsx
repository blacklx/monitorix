import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import axios from 'axios'
import './NotificationChannels.css'

const API_URL = import.meta.env.VITE_API_URL || import.meta.env.REACT_APP_API_URL || ''

const NotificationChannels = () => {
  const { t } = useTranslation()
  const [channels, setChannels] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingChannel, setEditingChannel] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    type: 'slack',
    webhook_url: '',
    alert_types: [],
    severity_filter: [],
    is_active: true
  })
  const [error, setError] = useState(null)
  const [deleteConfirm, setDeleteConfirm] = useState(null)
  const [testingChannel, setTestingChannel] = useState(null)

  const alertTypes = ['node_down', 'vm_down', 'service_down', 'high_usage', 'test']
  const severities = ['info', 'warning', 'critical']

  useEffect(() => {
    fetchChannels()
  }, [])

  const fetchChannels = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/notification-channels`)
      setChannels(response.data)
    } catch (error) {
      console.error('Failed to fetch notification channels:', error)
      setError(error.response?.data?.detail || t('common.error'))
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    setEditingChannel(null)
    setFormData({
      name: '',
      type: 'slack',
      webhook_url: '',
      alert_types: [],
      severity_filter: [],
      is_active: true
    })
    setError(null)
    setShowModal(true)
  }

  const handleEdit = (channel) => {
    setEditingChannel(channel)
    setFormData({
      name: channel.name,
      type: channel.type,
      webhook_url: channel.webhook_url,
      alert_types: channel.alert_types || [],
      severity_filter: channel.severity_filter || [],
      is_active: channel.is_active
    })
    setError(null)
    setShowModal(true)
  }

  const handleDelete = async (channelId) => {
    try {
      await axios.delete(`${API_URL}/api/notification-channels/${channelId}`)
      setDeleteConfirm(null)
      fetchChannels()
    } catch (error) {
      console.error('Failed to delete channel:', error)
      setError(error.response?.data?.detail || t('common.error'))
    }
  }

  const handleTest = async (channelId) => {
    setTestingChannel(channelId)
    try {
      await axios.post(`${API_URL}/api/notification-channels/${channelId}/test`)
      alert(t('notificationChannels.testSuccess'))
    } catch (error) {
      console.error('Failed to test channel:', error)
      alert(error.response?.data?.detail || t('notificationChannels.testFailed'))
    } finally {
      setTestingChannel(null)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    try {
      if (editingChannel) {
        await axios.put(`${API_URL}/api/notification-channels/${editingChannel.id}`, formData)
      } else {
        await axios.post(`${API_URL}/api/notification-channels`, formData)
      }
      setShowModal(false)
      fetchChannels()
    } catch (error) {
      setError(error.response?.data?.detail || t('common.error'))
    }
  }

  const toggleAlertType = (type) => {
    const current = formData.alert_types || []
    if (current.includes(type)) {
      setFormData({ ...formData, alert_types: current.filter(t => t !== type) })
    } else {
      setFormData({ ...formData, alert_types: [...current, type] })
    }
  }

  const toggleSeverity = (severity) => {
    const current = formData.severity_filter || []
    if (current.includes(severity)) {
      setFormData({ ...formData, severity_filter: current.filter(s => s !== severity) })
    } else {
      setFormData({ ...formData, severity_filter: [...current, severity] })
    }
  }

  if (loading) {
    return <div className="loading">{t('common.loading')}</div>
  }

  return (
    <div className="notification-channels">
      <div className="page-header">
        <h1>{t('notificationChannels.title')}</h1>
        <button className="add-button" onClick={handleAdd}>
          {t('notificationChannels.addChannel')}
        </button>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="channels-grid">
        {channels.map((channel) => (
          <div key={channel.id} className="channel-card">
            <div className="channel-header">
              <h2>{channel.name}</h2>
              <span className={`status-badge ${channel.is_active ? 'active' : 'inactive'}`}>
                {channel.is_active ? t('notificationChannels.active') : t('notificationChannels.inactive')}
              </span>
            </div>
            <div className="channel-info">
              <p>
                <strong>{t('notificationChannels.type')}:</strong> {channel.type === 'slack' ? 'Slack' : 'Discord'}
              </p>
              <p>
                <strong>{t('notificationChannels.webhookUrl')}:</strong> {channel.webhook_url.substring(0, 50)}...
              </p>
              {channel.alert_types && channel.alert_types.length > 0 && (
                <p>
                  <strong>{t('notificationChannels.alertTypes')}:</strong> {channel.alert_types.join(', ')}
                </p>
              )}
              {channel.severity_filter && channel.severity_filter.length > 0 && (
                <p>
                  <strong>{t('notificationChannels.severityFilter')}:</strong> {channel.severity_filter.join(', ')}
                </p>
              )}
            </div>
            <div className="channel-actions">
              <button
                className="action-button test-button"
                onClick={() => handleTest(channel.id)}
                disabled={testingChannel === channel.id}
              >
                {testingChannel === channel.id ? t('common.loading') : t('notificationChannels.test')}
              </button>
              <button
                className="action-button edit-button"
                onClick={() => handleEdit(channel)}
              >
                {t('common.edit')}
              </button>
              <button
                className="action-button delete-button"
                onClick={() => setDeleteConfirm(channel.id)}
              >
                {t('common.delete')}
              </button>
            </div>
          </div>
        ))}
        {channels.length === 0 && (
          <div className="no-channels">
            <p>{t('notificationChannels.noChannels')}</p>
          </div>
        )}
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingChannel ? t('notificationChannels.editChannel') : t('notificationChannels.addChannel')}</h2>
              <button className="close-button" onClick={() => setShowModal(false)}>
                {t('common.close')}
              </button>
            </div>
            
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>{t('notificationChannels.name')}</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label>{t('notificationChannels.type')}</label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  disabled={!!editingChannel}
                  required
                >
                  <option value="slack">Slack</option>
                  <option value="discord">Discord</option>
                </select>
                {editingChannel && (
                  <small>{t('notificationChannels.typeCannotChange')}</small>
                )}
              </div>

              <div className="form-group">
                <label>{t('notificationChannels.webhookUrl')}</label>
                <input
                  type="url"
                  value={formData.webhook_url}
                  onChange={(e) => setFormData({ ...formData, webhook_url: e.target.value })}
                  placeholder="https://hooks.slack.com/services/..."
                  required
                />
              </div>

              <div className="form-group">
                <label>{t('notificationChannels.alertTypes')}</label>
                <div className="checkbox-group">
                  {alertTypes.map((type) => (
                    <label key={type} className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={(formData.alert_types || []).includes(type)}
                        onChange={() => toggleAlertType(type)}
                      />
                      {t(`notificationChannels.alertType.${type}`)}
                    </label>
                  ))}
                </div>
                <small>{t('notificationChannels.alertTypesHint')}</small>
              </div>

              <div className="form-group">
                <label>{t('notificationChannels.severityFilter')}</label>
                <div className="checkbox-group">
                  {severities.map((severity) => (
                    <label key={severity} className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={(formData.severity_filter || []).includes(severity)}
                        onChange={() => toggleSeverity(severity)}
                      />
                      {t(`notificationChannels.severity.${severity}`)}
                    </label>
                  ))}
                </div>
                <small>{t('notificationChannels.severityFilterHint')}</small>
              </div>

              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  />
                  {t('notificationChannels.active')}
                </label>
              </div>

              {error && (
                <div className="error-message">
                  {error}
                </div>
              )}

              <div className="form-actions">
                <button type="button" onClick={() => setShowModal(false)}>
                  {t('common.cancel')}
                </button>
                <button type="submit">
                  {t('common.save')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {deleteConfirm && (
        <div className="modal-overlay" onClick={() => setDeleteConfirm(null)}>
          <div className="modal-content delete-confirm" onClick={(e) => e.stopPropagation()}>
            <h2>{t('notificationChannels.deleteChannel')}</h2>
            <p>{t('notificationChannels.confirmDelete')}</p>
            <div className="form-actions">
              <button onClick={() => setDeleteConfirm(null)}>
                {t('common.cancel')}
              </button>
              <button className="delete-button" onClick={() => handleDelete(deleteConfirm)}>
                {t('common.delete')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default NotificationChannels

