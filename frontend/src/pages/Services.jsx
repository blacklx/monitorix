import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import axios from 'axios'
import { validateService } from '../utils/validation'
import './Services.css'

const API_URL = import.meta.env.REACT_APP_API_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000'

const Services = () => {
  const { t } = useTranslation()
  const [services, setServices] = useState([])
  const [filteredServices, setFilteredServices] = useState([])
  const [vms, setVms] = useState([])
  const [loading, setLoading] = useState(true)
  const [healthChecks, setHealthChecks] = useState({})
  const [searchQuery, setSearchQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')
  const [showModal, setShowModal] = useState(false)
  const [editingService, setEditingService] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    type: 'http',
    target: '',
    port: null,
    vm_id: null,
    check_interval: 60,
    timeout: 5,
    expected_status: 200,
    is_active: true,
    maintenance_mode: false,
    custom_command: '',
    custom_script: ''
  })
  const [testingService, setTestingService] = useState(false)
  const [testResult, setTestResult] = useState(null)
  const [error, setError] = useState(null)
  const [deleteConfirm, setDeleteConfirm] = useState(null)
  const [validationErrors, setValidationErrors] = useState({})

  useEffect(() => {
    fetchVMs()
    fetchServices()
    const interval = setInterval(fetchServices, 30000)
    return () => clearInterval(interval)
  }, [])

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
      applyFilters(response.data)
      
      // Fetch latest health check for each service
      for (const service of response.data) {
        try {
          const checksResponse = await axios.get(
            `${API_URL}/api/health-checks?service_id=${service.id}&limit=1`
          )
          if (checksResponse.data && checksResponse.data.length > 0) {
            setHealthChecks((prev) => ({
              ...prev,
              [service.id]: checksResponse.data[0],
            }))
          }
        } catch (error) {
          // Health checks might not exist yet, which is fine
          console.debug(`No health checks found for service ${service.id}`)
        }
      }
    } catch (error) {
      console.error('Failed to fetch services:', error)
    } finally {
      setLoading(false)
    }
  }

  const applyFilters = (serviceList = services) => {
    let filtered = [...serviceList]

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(service =>
        service.name.toLowerCase().includes(query) ||
        service.target.toLowerCase().includes(query) ||
        service.type.toLowerCase().includes(query)
      )
    }

    // Apply type filter
    if (typeFilter !== 'all') {
      filtered = filtered.filter(service => service.type === typeFilter)
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(service => {
        const check = healthChecks[service.id]
        if (!check) return statusFilter === 'unknown'
        return check.status === statusFilter
      })
    }

    setFilteredServices(filtered)
  }

  useEffect(() => {
    applyFilters()
  }, [searchQuery, typeFilter, statusFilter, services, healthChecks])

  const handleCheck = async (serviceId) => {
    try {
      await axios.post(`${API_URL}/api/services/${serviceId}/check`)
      fetchServices()
    } catch (error) {
      console.error('Failed to check service:', error)
    }
  }

  const handleToggleMaintenance = async (serviceId, maintenanceMode) => {
    try {
      await axios.post(
        `${API_URL}/api/services/${serviceId}/maintenance-mode?maintenance_mode=${maintenanceMode}`
      )
      fetchServices()
    } catch (error) {
      console.error('Failed to toggle maintenance mode:', error)
      setError(error.response?.data?.detail || t('common.error'))
    }
  }

  const handleAdd = () => {
    setEditingService(null)
    setFormData({
      name: '',
      type: 'http',
      target: '',
      port: null,
      vm_id: null,
      check_interval: 60,
      timeout: 5,
      expected_status: 200,
      is_active: true,
      maintenance_mode: false,
      custom_command: '',
      custom_script: ''
    })
    setTestResult(null)
    setError(null)
    setShowModal(true)
  }

  const handleEdit = (service) => {
    setEditingService(service)
    setFormData({
      name: service.name,
      type: service.type,
      target: service.target,
      port: service.port || null,
      vm_id: service.vm_id || null,
      check_interval: service.check_interval,
      timeout: service.timeout,
      expected_status: service.expected_status,
      is_active: service.is_active,
      maintenance_mode: service.maintenance_mode || false,
      custom_command: service.custom_command || '',
      custom_script: service.custom_script || ''
    })
    setTestResult(null)
    setError(null)
    setShowModal(true)
  }

  const handleDelete = async (serviceId) => {
    try {
      await axios.delete(`${API_URL}/api/services/${serviceId}`)
      setDeleteConfirm(null)
      fetchServices()
    } catch (error) {
      console.error('Failed to delete service:', error)
      setError(error.response?.data?.detail || t('common.error'))
    }
  }

  const handleTestService = async () => {
    setTestingService(true)
    setTestResult(null)
    setError(null)
    
    try {
      // Create a temporary service object for testing
      const testData = {
        ...formData,
        port: formData.port || undefined
      }
      
      // Use the check endpoint with the service data
      // We'll need to create a test endpoint or use the existing one
      const response = await axios.post(`${API_URL}/api/services/test`, testData)
      if (response.data.success) {
        setTestResult({ success: true, message: t('services.testSuccess') })
      } else {
        setTestResult({ success: false, message: response.data.message || t('services.testFailed') })
      }
    } catch (error) {
      setTestResult({ 
        success: false, 
        message: error.response?.data?.detail || t('services.testFailed') 
      })
    } finally {
      setTestingService(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setValidationErrors({})
    
    // Validate form data
    const validation = validateService(formData)
    if (!validation.isValid) {
      setValidationErrors(validation.errors)
      return
    }
    
    try {
      const submitData = {
        ...formData,
        port: formData.port || undefined,
        vm_id: formData.vm_id || undefined
      }
      
      if (editingService) {
        await axios.put(`${API_URL}/api/services/${editingService.id}`, submitData)
      } else {
        await axios.post(`${API_URL}/api/services`, submitData)
      }
      
      setShowModal(false)
      setFormData({
        name: '',
        type: 'http',
        target: '',
        port: null,
        vm_id: null,
        check_interval: 60,
        timeout: 5,
        expected_status: 200,
        is_active: true,
        maintenance_mode: false,
        custom_command: '',
        custom_script: ''
      })
      setValidationErrors({})
      fetchServices()
    } catch (error) {
      setError(error.response?.data?.detail || t('common.error'))
    }
  }

  const requiresPort = formData.type === 'port'
  const requiresExpectedStatus = formData.type === 'http' || formData.type === 'https'

  if (loading) {
    return <div className="loading">{t('common.loading')}</div>
  }

  return (
    <div className="services">
      <div className="page-header">
        <h1>{t('services.title')}</h1>
        <button className="add-button" onClick={handleAdd}>
          {t('services.addService')}
        </button>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="services-list">
        {services.map((service) => {
          const check = healthChecks[service.id]
          return (
            <div key={service.id} className="service-card">
              <div className="service-header">
                <div>
                  <h2>{service.name}</h2>
                  <p className="service-target">{service.target}</p>
                </div>
                <div className="service-actions">
                  {service.maintenance_mode && (
                    <span className="status-badge maintenance" title={t('services.maintenanceMode')}>
                      🔧 {t('services.maintenance')}
                    </span>
                  )}
                  {check && (
                    <span className={`status-badge ${check.status}`}>
                      {t(`services.status.${check.status}`)}
                    </span>
                  )}
                  <button
                    className="action-button edit-button"
                    onClick={() => handleEdit(service)}
                  >
                    {t('common.edit')}
                  </button>
                  <button
                    className="action-button check-button"
                    onClick={() => handleCheck(service.id)}
                  >
                    {t('services.checkNow')}
                  </button>
                  <button
                    className={`action-button ${service.maintenance_mode ? 'maintenance-active' : 'maintenance-button'}`}
                    onClick={() => handleToggleMaintenance(service.id, !service.maintenance_mode)}
                    title={service.maintenance_mode ? t('services.disableMaintenance') : t('services.enableMaintenance')}
                  >
                    {service.maintenance_mode ? '🔧 ' + t('services.maintenance') : t('services.setMaintenance')}
                  </button>
                  <button
                    className="action-button delete-button"
                    onClick={() => setDeleteConfirm(service.id)}
                  >
                    {t('common.delete')}
                  </button>
                </div>
              </div>
              <div className="service-info">
                <p>
                  <strong>{t('common.type')}:</strong> {t(`services.types.${service.type}`)}
                </p>
                {service.port && (
                  <p>
                    <strong>{t('services.port')}:</strong> {service.port}
                  </p>
                )}
                {service.vm_id && (
                  <p>
                    <strong>{t('services.vm')}:</strong> {
                      vms.find(vm => vm.id === service.vm_id)?.name || `VM ID: ${service.vm_id}`
                    }
                  </p>
                )}
                {check && (
                  <>
                    {check.response_time && (
                      <p>
                        <strong>{t('services.responseTime')}:</strong> {check.response_time.toFixed(2)}ms
                      </p>
                    )}
                    {check.error_message && (
                      <p className="error-message">
                        <strong>{t('services.error')}:</strong> {check.error_message}
                      </p>
                    )}
                    <p>
                      <strong>{t('common.lastCheck')}:</strong>{' '}
                      {new Date(check.checked_at).toLocaleString()}
                    </p>
                  </>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingService ? t('services.editService') : t('services.addService')}</h2>
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
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label>{t('services.serviceType')}</label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  required
                >
                  <option value="http">{t('services.types.http')}</option>
                  <option value="https">{t('services.types.https')}</option>
                  <option value="ping">{t('services.types.ping')}</option>
                  <option value="port">{t('services.types.port')}</option>
                  <option value="custom">{t('services.types.custom')}</option>
                </select>
              </div>

              {formData.type === 'custom' && (
                <>
                  <div className="form-group">
                    <label>{t('services.customCommand')}</label>
                    <input
                      type="text"
                      value={formData.custom_command || ''}
                      onChange={(e) => setFormData({ ...formData, custom_command: e.target.value })}
                      placeholder="curl -f http://example.com || exit 1"
                    />
                    <small>{t('services.customCommandDesc')}</small>
                  </div>
                  <div className="form-group">
                    <label>{t('services.customScript')}</label>
                    <textarea
                      value={formData.custom_script || ''}
                      onChange={(e) => setFormData({ ...formData, custom_script: e.target.value })}
                      rows={5}
                      placeholder="#!/bin/bash&#10;curl -f http://example.com || exit 1"
                    />
                    <small>{t('services.customScriptDesc')}</small>
                  </div>
                </>
              )}

              <div className="form-group">
                <label>{t('services.target')}</label>
                <input
                  type="text"
                  value={formData.target}
                  onChange={(e) => setFormData({ ...formData, target: e.target.value })}
                  placeholder={formData.type === 'ping' ? '192.168.1.1' : formData.type === 'port' ? '192.168.1.1' : 'https://example.com'}
                  required
                />
              </div>

              {(requiresPort || formData.type === 'http' || formData.type === 'https') && (
                <div className="form-group">
                  <label>{t('services.port')} {requiresPort ? '' : '(optional)'}</label>
                  <input
                    type="number"
                    value={formData.port || ''}
                    onChange={(e) => setFormData({ ...formData, port: e.target.value ? parseInt(e.target.value) : null })}
                    min="1"
                    max="65535"
                    placeholder={formData.type === 'http' ? '80' : formData.type === 'https' ? '443' : ''}
                    required={requiresPort}
                  />
                </div>
              )}

              {requiresExpectedStatus && (
                <div className="form-group">
                  <label>{t('services.expectedStatus')}</label>
                  <input
                    type="number"
                    value={formData.expected_status}
                    onChange={(e) => setFormData({ ...formData, expected_status: parseInt(e.target.value) })}
                    min="100"
                    max="599"
                    required
                  />
                </div>
              )}

              <div className="form-group">
                <label>{t('services.vm')}</label>
                <select
                  value={formData.vm_id || ''}
                  onChange={(e) => setFormData({ ...formData, vm_id: e.target.value ? parseInt(e.target.value) : null })}
                >
                  <option value="">{t('services.noVm')}</option>
                  {vms.map((vm) => (
                    <option key={vm.id} value={vm.id}>
                      {vm.name} (VMID: {vm.vmid})
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>{t('services.checkInterval')}</label>
                <input
                  type="number"
                  value={formData.check_interval}
                  onChange={(e) => setFormData({ ...formData, check_interval: parseInt(e.target.value) })}
                  min="10"
                  required
                />
              </div>

              <div className="form-group">
                <label>{t('services.timeout')}</label>
                <input
                  type="number"
                  value={formData.timeout}
                  onChange={(e) => setFormData({ ...formData, timeout: parseInt(e.target.value) })}
                  min="1"
                  max="60"
                  required
                />
              </div>

              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  />
                  {t('services.isActive')}
                </label>
              </div>

              {editingService && (
                <div className="form-group">
                  <label>
                    <input
                      type="checkbox"
                      checked={formData.maintenance_mode || false}
                      onChange={(e) => setFormData({ ...formData, maintenance_mode: e.target.checked })}
                    />
                    {t('services.maintenanceMode')}
                  </label>
                  <small>{t('services.maintenanceModeDesc')}</small>
                </div>
              )}

              {testResult && (
                <div className={`connection-result ${testResult.success ? 'success' : 'error'}`}>
                  {testResult.message}
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
                  onClick={handleTestService}
                  disabled={testingService || !formData.target || (requiresPort && !formData.port)}
                >
                  {testingService ? t('common.loading') : t('services.testService')}
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
            <h2>{t('services.deleteService')}</h2>
            <p>{t('services.confirmDelete')}</p>
            <p className="warning-text">{t('services.deleteWarning')}</p>
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

export default Services
