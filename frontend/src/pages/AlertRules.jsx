import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import axios from 'axios'
import './AlertRules.css'

const API_URL = import.meta.env.REACT_APP_API_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000'

const AlertRules = () => {
  const { t } = useTranslation()
  const [rules, setRules] = useState([])
  const [nodes, setNodes] = useState([])
  const [vms, setVms] = useState([])
  const [services, setServices] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingRule, setEditingRule] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    metric_type: 'cpu',
    operator: '>',
    threshold: 80,
    severity: 'warning',
    node_id: null,
    vm_id: null,
    service_id: null,
    cooldown_minutes: 5,
    is_active: true
  })
  const [error, setError] = useState(null)
  const [deleteConfirm, setDeleteConfirm] = useState(null)

  useEffect(() => {
    fetchRules()
    fetchNodes()
    fetchVMs()
    fetchServices()
  }, [])

  const fetchRules = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/alert-rules`)
      setRules(response.data)
    } catch (error) {
      console.error('Failed to fetch alert rules:', error)
      setError(error.response?.data?.detail || t('common.error'))
    } finally {
      setLoading(false)
    }
  }

  const fetchNodes = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/nodes`)
      setNodes(response.data)
    } catch (error) {
      console.error('Failed to fetch nodes:', error)
    }
  }

  const fetchVMs = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/vms`)
      setVms(response.data)
    } catch (error) {
      console.error('Failed to fetch VMs:', error)
    }
  }

  const fetchServices = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/services`)
      setServices(response.data)
    } catch (error) {
      console.error('Failed to fetch services:', error)
    }
  }

  const handleAdd = () => {
    setEditingRule(null)
    setFormData({
      name: '',
      metric_type: 'cpu',
      operator: '>',
      threshold: 80,
      severity: 'warning',
      node_id: null,
      vm_id: null,
      service_id: null,
      cooldown_minutes: 5,
      is_active: true
    })
    setError(null)
    setShowModal(true)
  }

  const handleEdit = (rule) => {
    setEditingRule(rule)
    setFormData({
      name: rule.name,
      metric_type: rule.metric_type,
      operator: rule.operator,
      threshold: rule.threshold,
      severity: rule.severity,
      node_id: rule.node_id || null,
      vm_id: rule.vm_id || null,
      service_id: rule.service_id || null,
      cooldown_minutes: rule.cooldown_minutes,
      is_active: rule.is_active
    })
    setError(null)
    setShowModal(true)
  }

  const handleDelete = async (ruleId) => {
    try {
      await axios.delete(`${API_URL}/api/alert-rules/${ruleId}`)
      setDeleteConfirm(null)
      fetchRules()
    } catch (error) {
      console.error('Failed to delete alert rule:', error)
      setError(error.response?.data?.detail || t('common.error'))
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    const submitData = {
      ...formData,
      node_id: formData.node_id || undefined,
      vm_id: formData.vm_id || undefined,
      service_id: formData.service_id || undefined
    }

    try {
      if (editingRule) {
        await axios.put(`${API_URL}/api/alert-rules/${editingRule.id}`, submitData)
      } else {
        await axios.post(`${API_URL}/api/alert-rules`, submitData)
      }
      setShowModal(false)
      fetchRules()
    } catch (error) {
      setError(error.response?.data?.detail || t('common.error'))
    }
  }

  const getScopeLabel = (rule) => {
    if (rule.service_id) {
      const service = services.find(s => s.id === rule.service_id)
      return service ? `Service: ${service.name}` : 'Service'
    }
    if (rule.vm_id) {
      const vm = vms.find(v => v.id === rule.vm_id)
      return vm ? `VM: ${vm.name}` : 'VM'
    }
    if (rule.node_id) {
      const node = nodes.find(n => n.id === rule.node_id)
      return node ? `Node: ${node.name}` : 'Node'
    }
    return t('alertRules.global')
  }

  if (loading) {
    return <div className="loading">{t('common.loading')}</div>
  }

  return (
    <div className="alert-rules">
      <div className="page-header">
        <h1>{t('alertRules.title')}</h1>
        <button className="add-button" onClick={handleAdd}>
          {t('alertRules.addRule')}
        </button>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="rules-list">
        {rules.map((rule) => (
          <div key={rule.id} className="rule-card">
            <div className="rule-header">
              <h2>{rule.name}</h2>
              <span className={`status-badge ${rule.is_active ? 'active' : 'inactive'}`}>
                {rule.is_active ? t('alertRules.active') : t('alertRules.inactive')}
              </span>
            </div>
            <div className="rule-info">
              <p>
                <strong>{t('alertRules.condition')}:</strong>{' '}
                {t(`alertRules.metricType.${rule.metric_type}`)} {rule.operator} {rule.threshold}%
              </p>
              <p>
                <strong>{t('alertRules.severity')}:</strong>{' '}
                <span className={`severity-badge ${rule.severity}`}>
                  {t(`alertRules.severity.${rule.severity}`)}
                </span>
              </p>
              <p>
                <strong>{t('alertRules.scope')}:</strong> {getScopeLabel(rule)}
              </p>
              <p>
                <strong>{t('alertRules.cooldown')}:</strong> {rule.cooldown_minutes} {t('alertRules.minutes')}
              </p>
              {rule.last_triggered && (
                <p>
                  <strong>{t('alertRules.lastTriggered')}:</strong>{' '}
                  {new Date(rule.last_triggered).toLocaleString()}
                </p>
              )}
            </div>
            <div className="rule-actions">
              <button
                className="action-button edit-button"
                onClick={() => handleEdit(rule)}
              >
                {t('common.edit')}
              </button>
              <button
                className="action-button delete-button"
                onClick={() => setDeleteConfirm(rule.id)}
              >
                {t('common.delete')}
              </button>
            </div>
          </div>
        ))}
        {rules.length === 0 && (
          <div className="no-rules">
            <p>{t('alertRules.noRules')}</p>
          </div>
        )}
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingRule ? t('alertRules.editRule') : t('alertRules.addRule')}</h2>
              <button className="close-button" onClick={() => setShowModal(false)}>
                {t('common.close')}
              </button>
            </div>
            
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>{t('alertRules.name')}</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label>{t('alertRules.metricType')}</label>
                <select
                  value={formData.metric_type}
                  onChange={(e) => setFormData({ ...formData, metric_type: e.target.value })}
                  required
                >
                  <option value="cpu">{t('alertRules.metricType.cpu')}</option>
                  <option value="memory">{t('alertRules.metricType.memory')}</option>
                  <option value="disk">{t('alertRules.metricType.disk')}</option>
                  <option value="response_time">{t('alertRules.metricType.response_time')}</option>
                </select>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>{t('alertRules.operator')}</label>
                  <select
                    value={formData.operator}
                    onChange={(e) => setFormData({ ...formData, operator: e.target.value })}
                    required
                  >
                    <option value=">">&gt; (Greater than)</option>
                    <option value="<">&lt; (Less than)</option>
                    <option value=">=">&gt;= (Greater or equal)</option>
                    <option value="<=">&lt;= (Less or equal)</option>
                    <option value="==">== (Equal)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>{t('alertRules.threshold')} (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="100"
                    value={formData.threshold}
                    onChange={(e) => setFormData({ ...formData, threshold: parseFloat(e.target.value) })}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label>{t('alertRules.severity')}</label>
                <select
                  value={formData.severity}
                  onChange={(e) => setFormData({ ...formData, severity: e.target.value })}
                  required
                >
                  <option value="info">{t('alertRules.severity.info')}</option>
                  <option value="warning">{t('alertRules.severity.warning')}</option>
                  <option value="critical">{t('alertRules.severity.critical')}</option>
                </select>
              </div>

              <div className="form-group">
                <label>{t('alertRules.scope')}</label>
                <select
                  value={formData.node_id || ''}
                  onChange={(e) => setFormData({ 
                    ...formData, 
                    node_id: e.target.value ? parseInt(e.target.value) : null,
                    vm_id: null,
                    service_id: null
                  })}
                >
                  <option value="">{t('alertRules.global')}</option>
                  {nodes.map(node => (
                    <option key={node.id} value={node.id}>{node.name}</option>
                  ))}
                </select>
              </div>

              {formData.node_id && (
                <div className="form-group">
                  <label>{t('alertRules.vm')} ({t('alertRules.optional')})</label>
                  <select
                    value={formData.vm_id || ''}
                    onChange={(e) => setFormData({ 
                      ...formData, 
                      vm_id: e.target.value ? parseInt(e.target.value) : null,
                      service_id: null
                    })}
                  >
                    <option value="">{t('alertRules.allVMs')}</option>
                    {vms.filter(vm => vm.node_id === formData.node_id).map(vm => (
                      <option key={vm.id} value={vm.id}>{vm.name}</option>
                    ))}
                  </select>
                </div>
              )}

              {formData.metric_type === 'response_time' && (
                <div className="form-group">
                  <label>{t('alertRules.service')} ({t('alertRules.optional')})</label>
                  <select
                    value={formData.service_id || ''}
                    onChange={(e) => setFormData({ 
                      ...formData, 
                      service_id: e.target.value ? parseInt(e.target.value) : null
                    })}
                  >
                    <option value="">{t('alertRules.allServices')}</option>
                    {services.map(service => (
                      <option key={service.id} value={service.id}>{service.name}</option>
                    ))}
                  </select>
                </div>
              )}

              <div className="form-group">
                <label>{t('alertRules.cooldown')} ({t('alertRules.minutes')})</label>
                <input
                  type="number"
                  min="1"
                  value={formData.cooldown_minutes}
                  onChange={(e) => setFormData({ ...formData, cooldown_minutes: parseInt(e.target.value) })}
                  required
                />
                <small>{t('alertRules.cooldownHint')}</small>
              </div>

              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  />
                  {t('alertRules.active')}
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
            <h2>{t('alertRules.deleteRule')}</h2>
            <p>{t('alertRules.confirmDelete')}</p>
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

export default AlertRules

