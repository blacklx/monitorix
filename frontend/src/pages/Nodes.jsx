import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import axios from 'axios'
import { validateNode } from '../utils/validation'
import './Nodes.css'

const API_URL = import.meta.env.VITE_API_URL || import.meta.env.REACT_APP_API_URL || ''

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
    maintenance_mode: false,
    tags: []
  })
  const [tagInput, setTagInput] = useState('')
  const [testingConnection, setTestingConnection] = useState(false)
  const [connectionResult, setConnectionResult] = useState(null)
  const [error, setError] = useState(null)
  const [deleteConfirm, setDeleteConfirm] = useState(null)
  const [validationErrors, setValidationErrors] = useState({})
  const [showBulkModal, setShowBulkModal] = useState(false)
  const [bulkInput, setBulkInput] = useState('')
  const [bulkError, setBulkError] = useState(null)
  const [bulkResult, setBulkResult] = useState(null)
  const [tagFilter, setTagFilter] = useState(null)

  const fetchNodes = async () => {
    try {
      const params = tagFilter ? `?tag=${encodeURIComponent(tagFilter)}` : ''
      const response = await axios.get(`${API_URL}/api/nodes${params}`)
      setNodes(response.data)
    } catch (error) {
      console.error('Failed to fetch nodes:', error)
    } finally {
      setLoading(false)
    }
  }

  // Get all unique tags from nodes
  const allTags = Array.from(new Set(nodes.flatMap(node => node.tags || []))).sort()

  useEffect(() => {
    fetchNodes()
    const interval = setInterval(fetchNodes, 30000)
    return () => clearInterval(interval)
  }, [tagFilter])

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
      is_local: true,
      maintenance_mode: false,
      tags: []
    })
    setTagInput('')
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
      is_local: node.is_local,
      maintenance_mode: node.maintenance_mode || false,
      tags: node.tags || []
    })
    setTagInput('')
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

  const handleExportCSV = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/export/nodes/csv`, {
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `nodes_${formatDateForFilename()}.csv`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      console.error('Failed to export CSV:', error)
      setError(error.response?.data?.detail || t('common.error'))
    }
  }

  const handleExportJSON = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/export/nodes/json`, {
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `nodes_${formatDateForFilename()}.json`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      console.error('Failed to export JSON:', error)
      setError(error.response?.data?.detail || t('common.error'))
    }
  }

  const handleBulkImport = async () => {
    setBulkError(null)
    setBulkResult(null)
    
    if (!bulkInput.trim()) {
      setBulkError(t('common.fieldRequired'))
      return
    }
    
    try {
      // Parse bulk input
      const lines = bulkInput.trim().split('\n').filter(line => line.trim())
      const nodes = []
      
      for (const line of lines) {
        const parts = line.split(',').map(p => p.trim())
        if (parts.length < 4) {
          throw new Error(`Invalid format: ${line}. Expected: name,url,username,token[,is_local]`)
        }
        
        const [name, url, username, token, is_local_str] = parts
        const is_local = is_local_str ? is_local_str.toLowerCase() === 'true' : true
        
        // Validate node data
        const validation = validateNode({ name, url, username, token, is_local })
        if (!validation.isValid) {
          throw new Error(`Invalid node data for ${name}: ${Object.values(validation.errors).join(', ')}`)
        }
        
        nodes.push({ name, url, username, token, is_local })
      }
      
      if (nodes.length === 0) {
        setBulkError('No valid nodes found')
        return
      }
      
      // Send bulk create request
      const response = await axios.post(`${API_URL}/api/nodes/bulk`, { nodes })
      
      setBulkResult({
        created: response.data.created.length,
        failed: response.data.failed.length,
        failedDetails: response.data.failed
      })
      
      if (response.data.created.length > 0) {
        fetchNodes()
        setBulkInput('')
        setTimeout(() => {
          setShowBulkModal(false)
          setBulkResult(null)
        }, 3000)
      }
    } catch (error) {
      setBulkError(error.response?.data?.detail || error.message || t('common.error'))
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setValidationErrors({})
    
    // Validate form data
    // For edit mode, create a complete data object for validation (use existing values if not changed)
    const dataToValidate = editingNode ? {
      name: formData.name,
      url: formData.url,
      username: formData.username || editingNode.username,
      token: formData.token || 'placeholder-for-validation' // Token is optional in edit mode
    } : formData
    
    const validation = validateNode(dataToValidate)
    if (!validation.isValid) {
      setValidationErrors(validation.errors)
      return
    }
    
    if (editingNode) {
      // Update existing node - only send changed fields
      const updateData = {}
      if (formData.name !== editingNode.name) updateData.name = formData.name
      if (formData.url !== editingNode.url) updateData.url = formData.url
      if (formData.username && formData.username !== editingNode.username) updateData.username = formData.username
      if (formData.token && formData.token.trim().length > 0) updateData.token = formData.token
      if (formData.is_local !== editingNode.is_local) updateData.is_local = formData.is_local
      
      try {
        await axios.put(`${API_URL}/api/nodes/${editingNode.id}`, updateData)
        setShowModal(false)
        fetchNodes()
        return
      } catch (error) {
        handleApiError(error, setError, 'Nodes.updateNode')
        return
      }
    }
    
    try {
      // Create new node
      await axios.post(`${API_URL}/api/nodes`, formData)
      setShowModal(false)
      fetchNodes()
    } catch (error) {
      handleApiError(error, setError, 'Nodes.createNode')
    }
  }

  if (loading) {
    return <div className="loading">{t('common.loading')}</div>
  }

  return (
    <div className="nodes">
      <div className="page-header">
        <h1>{t('nodes.title')}</h1>
        <div>
          <button className="export-button" onClick={handleExportCSV} style={{ marginRight: '10px' }}>
            {t('common.exportCSV')}
          </button>
          <button className="export-button" onClick={handleExportJSON} style={{ marginRight: '10px' }}>
            {t('common.exportJSON')}
          </button>
          <button className="add-button" onClick={() => setShowBulkModal(true)} style={{ marginRight: '10px' }}>
            {t('nodes.bulkImport')}
          </button>
          <button className="add-button" onClick={handleAdd}>
            {t('nodes.addNode')}
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="nodes-filters" style={{ marginBottom: '1rem' }}>
        <div className="filter-group">
          <label>{t('nodes.filterByTag')}</label>
          <select
            value={tagFilter || ''}
            onChange={(e) => setTagFilter(e.target.value || null)}
          >
            <option value="">{t('common.all')}</option>
            {allTags.map(tag => (
              <option key={tag} value={tag}>{tag}</option>
            ))}
          </select>
        </div>
      </div>

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
              {node.tags && node.tags.length > 0 && (
                <p>
                  <strong>{t('nodes.tags')}:</strong>{' '}
                  {node.tags.map((tag, idx) => (
                    <span key={idx} className="tag-badge">
                      {tag}
                    </span>
                  ))}
                </p>
              )}
              <p>
                <strong>{t('common.lastCheck')}:</strong>{' '}
                {node.last_check
                  ? formatShortDateTime(node.last_check)
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

              <div className="form-group">
                <label>{t('nodes.tags')}</label>
                <div className="tags-input">
                  <div className="tags-list">
                    {formData.tags.map((tag, index) => (
                      <span key={index} className="tag">
                        {tag}
                        <button
                          type="button"
                          className="tag-remove"
                          onClick={() => {
                            setFormData({
                              ...formData,
                              tags: formData.tags.filter((_, i) => i !== index)
                            })
                          }}
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                  <div className="tag-input-group">
                    <input
                      type="text"
                      value={tagInput}
                      onChange={(e) => setTagInput(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault()
                          const tag = tagInput.trim()
                          if (tag && !formData.tags.includes(tag)) {
                            setFormData({
                              ...formData,
                              tags: [...formData.tags, tag]
                            })
                            setTagInput('')
                          }
                        }
                      }}
                      placeholder={t('nodes.addTagPlaceholder')}
                    />
                    <button
                      type="button"
                      onClick={() => {
                        const tag = tagInput.trim()
                        if (tag && !formData.tags.includes(tag)) {
                          setFormData({
                            ...formData,
                            tags: [...formData.tags, tag]
                          })
                          setTagInput('')
                        }
                      }}
                    >
                      {t('nodes.addTag')}
                    </button>
                  </div>
                </div>
                <small>{t('nodes.tagsDescription')}</small>
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

      {showBulkModal && (
        <div className="modal-overlay" onClick={() => setShowBulkModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{t('nodes.bulkImportTitle')}</h2>
              <button className="close-button" onClick={() => setShowBulkModal(false)}>
                {t('common.close')}
              </button>
            </div>
            
            <div style={{ padding: '20px' }}>
              <p style={{ marginBottom: '15px', color: '#666' }}>
                {t('nodes.bulkImportDescription')}
              </p>
              
              <div className="form-group">
                <label>{t('nodes.bulkImportExample')}</label>
                <textarea
                  value={bulkInput}
                  onChange={(e) => {
                    setBulkInput(e.target.value)
                    setBulkError(null)
                    setBulkResult(null)
                  }}
                  placeholder="node1,https://192.168.1.10:8006,user@pam,token123,true&#10;node2,https://192.168.1.11:8006,user@pam,token456,false"
                  rows={10}
                  style={{ 
                    width: '100%', 
                    fontFamily: 'monospace',
                    padding: '10px',
                    border: '1px solid #ddd',
                    borderRadius: '4px'
                  }}
                />
              </div>

              {bulkError && (
                <div className="error-message" style={{ marginBottom: '15px' }}>
                  {bulkError}
                </div>
              )}

              {bulkResult && (
                <div style={{ marginBottom: '15px', padding: '15px', backgroundColor: '#f0f0f0', borderRadius: '4px' }}>
                  <h3>{t('nodes.bulkImportResults')}</h3>
                  <p style={{ color: '#27ae60' }}>
                    {t('nodes.bulkImportSuccess', { count: bulkResult.created })}
                  </p>
                  {bulkResult.failed > 0 && (
                    <>
                      <p style={{ color: '#e74c3c' }}>
                        {t('nodes.bulkImportFailed', { count: bulkResult.failed })}
                      </p>
                      <details style={{ marginTop: '10px' }}>
                        <summary style={{ cursor: 'pointer' }}>Failed nodes:</summary>
                        <ul style={{ marginTop: '10px', paddingLeft: '20px' }}>
                          {bulkResult.failedDetails.map((item, idx) => (
                            <li key={idx} style={{ marginBottom: '5px' }}>
                              <strong>{item.node.name}:</strong> {item.error}
                            </li>
                          ))}
                        </ul>
                      </details>
                    </>
                  )}
                </div>
              )}

              <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
                <button 
                  className="add-button" 
                  onClick={handleBulkImport}
                  disabled={!bulkInput.trim()}
                >
                  {t('nodes.bulkImport')}
                </button>
                <button 
                  className="link-button" 
                  onClick={() => {
                    setShowBulkModal(false)
                    setBulkInput('')
                    setBulkError(null)
                    setBulkResult(null)
                  }}
                >
                  {t('common.cancel')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Nodes
