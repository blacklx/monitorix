import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import axios from 'axios'
import { validateNode } from '../utils/validation'
import './Nodes.css'

const API_URL = import.meta.env.REACT_APP_API_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000'

const Nodes = () => {
  const { t } = useTranslation()
  const [nodes, setNodes] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingNode, setEditingNode] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    username: '',
    token: '',
    is_local: true,
    maintenance_mode: false
  })
  const [testingConnection, setTestingConnection] = useState(false)
  const [connectionResult, setConnectionResult] = useState(null)
  const [error, setError] = useState(null)
  const [deleteConfirm, setDeleteConfirm] = useState(null)
  const [validationErrors, setValidationErrors] = useState({})

  useEffect(() => {
    fetchNodes()
    const interval = setInterval(fetchNodes, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchNodes = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/nodes`)
      setNodes(response.data)
    } catch (error) {
      console.error('Failed to fetch nodes:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSync = async (nodeId) => {
    try {
      await axios.post(`${API_URL}/api/nodes/${nodeId}/sync`)
      fetchNodes()
    } catch (error) {
      console.error('Failed to sync node:', error)
    }
  }

  const handleToggleMaintenance = async (nodeId, maintenanceMode) => {
    try {
      await axios.post(
        `${API_URL}/api/nodes/${nodeId}/maintenance-mode?maintenance_mode=${maintenanceMode}`
      )
      fetchNodes()
    } catch (error) {
      console.error('Failed to toggle maintenance mode:', error)
      setError(error.response?.data?.detail || t('common.error'))
    }
  }

  const handleAdd = () => {
    setEditingNode(null)
    setFormData({
      name: '',
      url: '',
      username: '',
      token: '',
      is_local: true
    })
    setConnectionResult(null)
    setError(null)
    setShowModal(true)
  }

  const handleEdit = (node) => {
    setEditingNode(node)
    setFormData({
      name: node.name,
      url: node.url,
      username: node.username || '',
      token: '', // Don't show existing token for security
      is_local: node.is_local
    })
    setConnectionResult(null)
    setError(null)
    setShowModal(true)
  }

  const handleDelete = async (nodeId) => {
    try {
      await axios.delete(`${API_URL}/api/nodes/${nodeId}`)
      setDeleteConfirm(null)
      fetchNodes()
    } catch (error) {
      console.error('Failed to delete node:', error)
      setError(error.response?.data?.detail || t('nodes.connectionFailed'))
    }
  }

  const handleTestConnection = async () => {
    setTestingConnection(true)
    setConnectionResult(null)
    setError(null)
    
    try {
      const response = await axios.post(`${API_URL}/api/nodes/test-connection`, formData)
      if (response.data.success) {
        setConnectionResult({ success: true, message: t('nodes.connectionSuccess') })
      } else {
        setConnectionResult({ success: false, message: response.data.message || t('nodes.connectionFailed') })
      }
    } catch (error) {
      setConnectionResult({ 
        success: false, 
        message: error.response?.data?.detail || t('nodes.connectionFailed') 
      })
    } finally {
      setTestingConnection(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    
    try {
      if (editingNode) {
        // Update existing node
        const updateData = {}
        if (formData.name !== editingNode.name) updateData.name = formData.name
        if (formData.url !== editingNode.url) updateData.url = formData.url
        if (formData.username) updateData.username = formData.username
        if (formData.token) updateData.token = formData.token
        if (formData.is_local !== editingNode.is_local) updateData.is_local = formData.is_local
        
        await axios.put(`${API_URL}/api/nodes/${editingNode.id}`, updateData)
      } else {
        // Create new node
        await axios.post(`${API_URL}/api/nodes`, formData)
      }
      
      setShowModal(false)
      fetchNodes()
    } catch (error) {
      setError(error.response?.data?.detail || t('common.error'))
    }
  }

  if (loading) {
    return <div className="loading">{t('common.loading')}</div>
  }

  return (
    <div className="nodes">
      <div className="page-header">
        <h1>{t('nodes.title')}</h1>
        <button className="add-button" onClick={handleAdd}>
          {t('nodes.addNode')}
        </button>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="nodes-grid">
        {nodes.map((node) => (
          <div key={node.id} className="node-card">
            <div className="node-header">
              <h2>{node.name}</h2>
              <span className={`status-badge ${node.status}`}>
                {t(`nodes.status.${node.status}`)}
              </span>
            </div>
            <div className="node-info">
              <p>
                <strong>{t('nodes.url')}:</strong> {node.url}
              </p>
              <p>
                <strong>{t('common.type')}:</strong> {node.is_local ? t('nodes.local') : t('nodes.remote')}
              </p>
              <p>
                <strong>{t('common.lastCheck')}:</strong>{' '}
                {node.last_check
                  ? new Date(node.last_check).toLocaleString()
                  : t('common.never')}
              </p>
            </div>
            <div className="node-actions">
              <button
                className="action-button edit-button"
                onClick={() => handleEdit(node)}
              >
                {t('common.edit')}
              </button>
              <button
                className="action-button sync-button"
                onClick={() => handleSync(node.id)}
              >
                {t('nodes.syncNow')}
              </button>
              <button
                className={`action-button ${node.maintenance_mode ? 'maintenance-active' : 'maintenance-button'}`}
                onClick={() => handleToggleMaintenance(node.id, !node.maintenance_mode)}
                title={node.maintenance_mode ? t('nodes.disableMaintenance') : t('nodes.enableMaintenance')}
              >
                {node.maintenance_mode ? '🔧 ' + t('nodes.maintenance') : t('nodes.setMaintenance')}
              </button>
              <button
                className="action-button delete-button"
                onClick={() => setDeleteConfirm(node.id)}
              >
                {t('common.delete')}
              </button>
            </div>
          </div>
        ))}
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingNode ? t('nodes.editNode') : t('nodes.addNode')}</h2>
              <button className="close-button" onClick={() => setShowModal(false)}>
                {t('common.close')}
              </button>
            </div>
            
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>{t('common.name')}</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => {
                    setFormData({ ...formData, name: e.target.value })
                    if (validationErrors.name) {
                      setValidationErrors({ ...validationErrors, name: null })
                    }
                  }}
                  className={validationErrors.name ? 'error' : ''}
                  required
                />
                {validationErrors.name && (
                  <span className="field-error">{validationErrors.name}</span>
                )}
              </div>

              <div className="form-group">
                <label>{t('nodes.url')}</label>
                <input
                  type="url"
                  value={formData.url}
                  onChange={(e) => {
                    setFormData({ ...formData, url: e.target.value })
                    if (validationErrors.url) {
                      setValidationErrors({ ...validationErrors, url: null })
                    }
                  }}
                  placeholder="https://192.168.1.10:8006"
                  className={validationErrors.url ? 'error' : ''}
                  required
                />
                {validationErrors.url && (
                  <span className="field-error">{validationErrors.url}</span>
                )}
              </div>

              <div className="form-group">
                <label>{t('nodes.username')}</label>
                <input
                  type="text"
                  value={formData.username}
                  onChange={(e) => {
                    setFormData({ ...formData, username: e.target.value })
                    if (validationErrors.username) {
                      setValidationErrors({ ...validationErrors, username: null })
                    }
                  }}
                  placeholder="user@pam"
                  className={validationErrors.username ? 'error' : ''}
                  required
                />
                {validationErrors.username && (
                  <span className="field-error">{validationErrors.username}</span>
                )}
              </div>

              <div className="form-group">
                <label>{t('nodes.token')}</label>
                <input
                  type="password"
                  value={formData.token}
                  onChange={(e) => {
                    setFormData({ ...formData, token: e.target.value })
                    if (validationErrors.token) {
                      setValidationErrors({ ...validationErrors, token: null })
                    }
                  }}
                  placeholder={editingNode ? 'Leave empty to keep current token' : 'token_id=secret'}
                  className={validationErrors.token ? 'error' : ''}
                  required={!editingNode}
                />
                {editingNode && (
                  <small>Leave empty to keep the current token</small>
                )}
                {validationErrors.token && (
                  <span className="field-error">{validationErrors.token}</span>
                )}
              </div>

              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.is_local}
                    onChange={(e) => setFormData({ ...formData, is_local: e.target.checked })}
                  />
                  {formData.is_local ? t('nodes.isLocal') : t('nodes.isRemote')}
                </label>
              </div>

              {connectionResult && (
                <div className={`connection-result ${connectionResult.success ? 'success' : 'error'}`}>
                  {connectionResult.message}
                </div>
              )}

              {error && (
                <div className="error-message">
                  {error}
                </div>
              )}

              <div className="form-actions">
                <button
                  type="button"
                  className="test-button"
                  onClick={handleTestConnection}
                  disabled={testingConnection || !formData.url || !formData.username || !formData.token}
                >
                  {testingConnection ? t('common.loading') : t('nodes.testConnection')}
                </button>
                <div className="form-buttons">
                  <button type="button" onClick={() => setShowModal(false)}>
                    {t('common.cancel')}
                  </button>
                  <button type="submit">
                    {t('common.save')}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}

      {deleteConfirm && (
        <div className="modal-overlay" onClick={() => setDeleteConfirm(null)}>
          <div className="modal-content delete-confirm" onClick={(e) => e.stopPropagation()}>
            <h2>{t('nodes.deleteNode')}</h2>
            <p>{t('nodes.confirmDelete')}</p>
            <p className="warning-text">{t('nodes.deleteWarning')}</p>
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

export default Nodes
