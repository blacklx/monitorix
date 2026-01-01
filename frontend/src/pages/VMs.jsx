import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import axios from 'axios'
import { formatShortDateTime, formatDateForFilename } from '../utils/dateFormat'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'
import './VMs.css'

const API_URL = import.meta.env.VITE_API_URL || import.meta.env.REACT_APP_API_URL || ''

const VMs = () => {
  const { t } = useTranslation()
  const [vms, setVms] = useState([])
  const [filteredVms, setFilteredVms] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedNode, setSelectedNode] = useState(null)
  const [nodes, setNodes] = useState([])
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [selectedVM, setSelectedVM] = useState(null)
  const [vmDetails, setVmDetails] = useState(null)
  const [vmMetrics, setVmMetrics] = useState([])
  const [vmUptime, setVmUptime] = useState(null)
  const [loadingDetails, setLoadingDetails] = useState(false)
  const [detailsError, setDetailsError] = useState(null)

  useEffect(() => {
    fetchNodes()
    fetchVMs()
    const interval = setInterval(fetchVMs, 30000)
    return () => clearInterval(interval)
  }, [selectedNode])

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
      const url = selectedNode
        ? `${API_URL}/api/vms?node_id=${selectedNode}`
        : `${API_URL}/api/vms`
      const response = await axios.get(url)
      setVms(response.data)
      applyFilters(response.data)
    } catch (error) {
      console.error('Failed to fetch VMs:', error)
    } finally {
      setLoading(false)
    }
  }

  const applyFilters = (vmList = vms) => {
    let filtered = [...vmList]

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      filtered = filtered.filter(vm =>
        vm.name.toLowerCase().includes(query) ||
        vm.vmid.toString().includes(query) ||
        vm.status.toLowerCase().includes(query)
      )
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(vm => vm.status === statusFilter)
    }

    setFilteredVms(filtered)
  }

  const handleExportCSV = async () => {
    try {
      const params = selectedNode ? `?node_id=${selectedNode}` : ''
      const response = await axios.get(`${API_URL}/api/export/vms/csv${params}`, {
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `vms_${formatDateForFilename()}.csv`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      console.error('Failed to export CSV:', error)
    }
  }

  const handleExportJSON = async () => {
    try {
      const params = selectedNode ? `?node_id=${selectedNode}` : ''
      const response = await axios.get(`${API_URL}/api/export/vms/json${params}`, {
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `vms_${formatDateForFilename()}.json`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      console.error('Failed to export JSON:', error)
    }
  }

  useEffect(() => {
    applyFilters()
  }, [searchQuery, statusFilter, vms])

  useEffect(() => {
    if (selectedVM) {
      fetchVMDetails()
    }
  }, [selectedVM])

  const fetchVMDetails = async () => {
    if (!selectedVM) return
    
    setLoadingDetails(true)
    setDetailsError(null)
    setVmDetails(null)
    setVmMetrics([])
    setVmUptime(null)
    
    try {
      const [vmResponse, metricsResponse, uptimeResponse] = await Promise.all([
        axios.get(`${API_URL}/api/vms/${selectedVM.id}`),
        axios.get(`${API_URL}/api/metrics?vm_id=${selectedVM.id}&hours=24`),
        axios.get(`${API_URL}/api/vms/${selectedVM.id}/uptime?hours=24`)
      ])
      
      setVmDetails(vmResponse.data)
      setVmUptime(uptimeResponse.data)
      
      // Process metrics for charts
      const cpuMetrics = metricsResponse.data.filter(m => m.metric_type === 'cpu')
      const memoryMetrics = metricsResponse.data.filter(m => m.metric_type === 'memory')
      const diskMetrics = metricsResponse.data.filter(m => m.metric_type === 'disk')
      
      // Combine metrics by timestamp
      const timeMap = new Map()
      
      cpuMetrics.forEach(m => {
        const time = new Date(m.recorded_at).getTime()
        if (!timeMap.has(time)) {
          timeMap.set(time, { time: formatShortDateTime(m.recorded_at) })
        }
        timeMap.get(time).cpu = m.value
      })
      
      memoryMetrics.forEach(m => {
        const time = new Date(m.recorded_at).getTime()
        if (!timeMap.has(time)) {
          timeMap.set(time, { time: formatShortDateTime(m.recorded_at) })
        }
        timeMap.get(time).memory = m.value
      })
      
      diskMetrics.forEach(m => {
        const time = new Date(m.recorded_at).getTime()
        if (!timeMap.has(time)) {
          timeMap.set(time, { time: formatShortDateTime(m.recorded_at) })
        }
        timeMap.get(time).disk = m.value
      })
      
      const combined = Array.from(timeMap.values())
        .sort((a, b) => new Date(a.time) - new Date(b.time))
      
      setVmMetrics(combined)
    } catch (error) {
      console.error('Failed to fetch VM details:', error)
      setDetailsError(error.response?.data?.detail || error.message || 'Failed to load VM details')
    } finally {
      setLoadingDetails(false)
    }
  }

  const handleSyncVM = async (vmId) => {
    try {
      await axios.post(`${API_URL}/api/vms/${vmId}/sync`)
      fetchVMs()
      if (selectedVM && selectedVM.id === vmId) {
        fetchVMDetails()
      }
    } catch (error) {
      console.error('Failed to sync VM:', error)
    }
  }

  const handleViewDetails = async (vm) => {
    setSelectedVM(vm)
    setVmDetails(null)
    setVmMetrics([])
    setVmUptime(null)
    setLoadingDetails(true)
    
    try {
      const [vmResponse, metricsResponse, uptimeResponse] = await Promise.all([
        axios.get(`${API_URL}/api/vms/${vm.id}`),
        axios.get(`${API_URL}/api/metrics?vm_id=${vm.id}&hours=24`),
        axios.get(`${API_URL}/api/vms/${vm.id}/uptime?hours=24`)
      ])
      
      setVmDetails(vmResponse.data)
      setVmUptime(uptimeResponse.data)
      
      // Process metrics for charts
      const cpuMetrics = metricsResponse.data.filter(m => m.metric_type === 'cpu')
      const memoryMetrics = metricsResponse.data.filter(m => m.metric_type === 'memory')
      const diskMetrics = metricsResponse.data.filter(m => m.metric_type === 'disk')
      
      // Combine metrics by timestamp
      const timeMap = new Map()
      
      cpuMetrics.forEach(m => {
        const time = new Date(m.recorded_at).getTime()
        if (!timeMap.has(time)) {
          timeMap.set(time, { time: formatShortDateTime(m.recorded_at) })
        }
        timeMap.get(time).cpu = m.value
      })
      
      memoryMetrics.forEach(m => {
        const time = new Date(m.recorded_at).getTime()
        if (!timeMap.has(time)) {
          timeMap.set(time, { time: formatShortDateTime(m.recorded_at) })
        }
        timeMap.get(time).memory = m.value
      })
      
      diskMetrics.forEach(m => {
        const time = new Date(m.recorded_at).getTime()
        if (!timeMap.has(time)) {
          timeMap.set(time, { time: formatShortDateTime(m.recorded_at) })
        }
        timeMap.get(time).disk = m.value
      })
      
      const combined = Array.from(timeMap.values())
        .sort((a, b) => new Date(a.time) - new Date(b.time))
      
      setVmMetrics(combined)
    } catch (error) {
      console.error('Failed to fetch VM details:', error)
      setError(error.response?.data?.detail || error.message || 'Failed to load VM details')
    } finally {
      setLoadingDetails(false)
    }
  }

  if (loading) {
    return <div className="loading">{t('common.loading')}</div>
  }

  return (
    <div className="vms">
      <div className="page-header">
        <h1>{t('vms.title')}</h1>
        <div>
          <button className="export-button" onClick={handleExportCSV} style={{ marginRight: '10px' }}>
            {t('common.exportCSV')}
          </button>
          <button className="export-button" onClick={handleExportJSON}>
            {t('common.exportJSON')}
          </button>
        </div>
      </div>

      <div className="filters">
        <div className="filter-group">
          <label>{t('vms.allNodes')}</label>
          <select
            value={selectedNode || ''}
            onChange={(e) => setSelectedNode(e.target.value ? parseInt(e.target.value) : null)}
            className="node-filter"
          >
            <option value="">{t('vms.allNodes')}</option>
            {nodes.map((node) => (
              <option key={node.id} value={node.id}>
                {node.name}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label>{t('common.search')}</label>
          <input
            type="text"
            placeholder={t('common.search')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
        </div>

        <div className="filter-group">
          <label>{t('common.status')}</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="status-filter"
          >
            <option value="all">{t('common.all')}</option>
            <option value="running">{t('vms.status.running')}</option>
            <option value="stopped">{t('vms.status.stopped')}</option>
            <option value="paused">{t('vms.status.paused')}</option>
          </select>
        </div>
      </div>

      <div className="vms-grid">
        {filteredVms.length === 0 ? (
          <div className="no-results">{t('common.noResults')}</div>
        ) : (
          filteredVms.map((vm) => (
            <div key={vm.id} className="vm-card">
              <div className="vm-header">
                <h2>{vm.name}</h2>
                <span className={`status-badge ${vm.status}`}>
                  {t(`vms.status.${vm.status}`)}
                </span>
              </div>
              <div className="vm-info">
                <div className="metric">
                  <span className="metric-label">{t('vms.cpu')}:</span>
                  <div className="metric-bar">
                    <div
                      className="metric-fill"
                      style={{ width: `${vm.cpu_usage}%`, backgroundColor: '#3498db' }}
                    />
                    <span className="metric-value">{vm.cpu_usage.toFixed(1)}%</span>
                  </div>
                </div>
                <div className="metric">
                  <span className="metric-label">{t('vms.memory')}:</span>
                  <div className="metric-bar">
                    <div
                      className="metric-fill"
                      style={{ width: `${vm.memory_usage}%`, backgroundColor: '#2ecc71' }}
                    />
                    <span className="metric-value">
                      {vm.memory_usage.toFixed(1)}% ({formatBytes(vm.memory_total)})
                    </span>
                  </div>
                </div>
                <div className="metric">
                  <span className="metric-label">{t('vms.disk')}:</span>
                  <div className="metric-bar">
                    <div
                      className="metric-fill"
                      style={{ width: `${vm.disk_usage}%`, backgroundColor: '#f39c12' }}
                    />
                    <span className="metric-value">
                      {vm.disk_usage.toFixed(1)}% ({formatBytes(vm.disk_total)})
                    </span>
                  </div>
                </div>
                <p>
                  <strong>{t('vms.vmid')}:</strong> {vm.vmid}
                </p>
                <p>
                  <strong>{t('vms.uptime')}:</strong> {formatUptime(vm.uptime)}
                </p>
              </div>
              <div className="vm-actions">
                <button
                  className="action-button details-button"
                  onClick={() => handleViewDetails(vm)}
                >
                  {t('vms.viewDetails')}
                </button>
                <button
                  className="action-button sync-button"
                  onClick={() => handleSyncVM(vm.id)}
                >
                  {t('vms.sync')}
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {selectedVM && (
        <div className="modal-overlay" onClick={() => {
          setSelectedVM(null)
          setVmDetails(null)
          setVmMetrics([])
          setVmUptime(null)
          setDetailsError(null)
        }}>
          <div className="modal-content vm-details-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{selectedVM.name} - {t('vms.details')}</h2>
              <button className="close-button" onClick={() => {
                setSelectedVM(null)
                setVmDetails(null)
                setVmMetrics([])
                setVmUptime(null)
                setDetailsError(null)
              }}>
                ×
              </button>
            </div>

            {loadingDetails ? (
              <div className="loading">{t('common.loading')}</div>
            ) : detailsError ? (
              <div className="vm-details-content">
                <div className="error-message" style={{ padding: '1rem', margin: '1rem', backgroundColor: '#f8d7da', color: '#721c24', borderRadius: '4px' }}>
                  <strong>Error:</strong> {detailsError}
                </div>
                <div style={{ textAlign: 'center', marginTop: '1rem' }}>
                  <button className="action-button details-button" onClick={() => fetchVMDetails()}>
                    {t('common.retry') || 'Retry'}
                  </button>
                </div>
              </div>
            ) : vmDetails ? (
              <div className="vm-details-content">
                <div className="vm-details-info">
                    <div className="info-section">
                      <h3>{t('vms.generalInfo')}</h3>
                      <div className="info-grid">
                        <div className="info-item">
                          <strong>{t('vms.vmid')}:</strong> {vmDetails.vmid}
                        </div>
                        <div className="info-item">
                          <strong>{t('common.status')}:</strong>
                          <span className={`status-badge ${vmDetails.status}`}>
                            {t(`vms.status.${vmDetails.status}`)}
                          </span>
                        </div>
                        <div className="info-item">
                          <strong>{t('vms.uptime')}:</strong> {formatUptime(vmDetails.uptime)}
                        </div>
                        <div className="info-item">
                          <strong>{t('common.lastCheck')}:</strong>{' '}
                          {vmDetails.last_check
                            ? formatShortDateTime(vmDetails.last_check)
                            : t('common.never')}
                        </div>
                      </div>
                    </div>

                    <div className="info-section">
                      <h3>{t('vms.resources')}</h3>
                      <div className="metric-detail">
                        <div className="metric-header">
                          <span>{t('vms.cpu')}</span>
                          <span>{vmDetails.cpu_usage.toFixed(1)}%</span>
                        </div>
                        <div className="metric-bar">
                          <div
                            className="metric-fill"
                            style={{ width: `${vmDetails.cpu_usage}%`, backgroundColor: '#3498db' }}
                          />
                        </div>
                      </div>
                      <div className="metric-detail">
                        <div className="metric-header">
                          <span>{t('vms.memory')}</span>
                          <span>
                            {vmDetails.memory_usage.toFixed(1)}% ({formatBytes(vmDetails.memory_total)})
                          </span>
                        </div>
                        <div className="metric-bar">
                          <div
                            className="metric-fill"
                            style={{ width: `${vmDetails.memory_usage}%`, backgroundColor: '#2ecc71' }}
                          />
                        </div>
                      </div>
                      <div className="metric-detail">
                        <div className="metric-header">
                          <span>{t('vms.disk')}</span>
                          <span>
                            {vmDetails.disk_usage.toFixed(1)}% ({formatBytes(vmDetails.disk_total)})
                          </span>
                        </div>
                        <div className="metric-bar">
                          <div
                            className="metric-fill"
                            style={{ width: `${vmDetails.disk_usage}%`, backgroundColor: '#f39c12' }}
                          />
                        </div>
                      </div>
                    </div>

                    {vmUptime && (
                      <div className="info-section">
                        <h3>{t('vms.uptimeStats')}</h3>
                        <div className="uptime-stats">
                          <div className="stat-item">
                            <strong>{t('vms.uptimePercent')}:</strong> {vmUptime.uptime_percent.toFixed(2)}%
                          </div>
                          <div className="stat-item">
                            <strong>{t('vms.downtime')}:</strong> {formatUptime(vmUptime.downtime_minutes * 60)}
                          </div>
                          <div className="stat-item">
                            <strong>{t('vms.totalChecks')}:</strong> {vmUptime.total_checks}
                          </div>
                          <div className="stat-item">
                            <strong>{t('vms.period')}:</strong> {vmUptime.period_hours} {t('common.hours')}
                          </div>
                        </div>
                      </div>
                    )}

                    {vmMetrics.length > 0 && (
                      <div className="info-section">
                        <h3>{t('vms.metricsHistory')}</h3>
                        <ResponsiveContainer width="100%" height={300}>
                          <LineChart data={vmMetrics}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis
                              dataKey="time"
                              angle={-45}
                              textAnchor="end"
                              height={80}
                              interval="preserveStartEnd"
                            />
                            <YAxis domain={[0, 100]} />
                            <Tooltip />
                            <Legend />
                            <Line
                              type="monotone"
                              dataKey="cpu"
                              stroke="#3498db"
                              strokeWidth={2}
                              dot={false}
                              name="CPU %"
                            />
                            <Line
                              type="monotone"
                              dataKey="memory"
                              stroke="#2ecc71"
                              strokeWidth={2}
                              dot={false}
                              name="Memory %"
                            />
                            <Line
                              type="monotone"
                              dataKey="disk"
                              stroke="#f39c12"
                              strokeWidth={2}
                              dot={false}
                              name="Disk %"
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    )}

                    <div className="modal-actions">
                      <button
                        className="action-button sync-button"
                        onClick={() => handleSyncVM(selectedVM.id)}
                      >
                        {t('vms.syncNow')}
                      </button>
                      <button
                        className="action-button"
                        onClick={() => {
                          setSelectedVM(null)
                          setVmDetails(null)
                          setVmMetrics([])
                          setVmUptime(null)
                          setDetailsError(null)
                        }}
                      >
                        {t('common.close')}
                      </button>
                    </div>
                  </div>
                </div>
              ) : null}
            </div>
          )}
          </div>
        </div>
      )}
    </div>
  )
}

const formatBytes = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

const formatUptime = (seconds) => {
  if (seconds < 60) return `${seconds}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`
  return `${Math.floor(seconds / 86400)}d`
}

export default VMs
