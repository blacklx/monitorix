import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import axios from 'axios'
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
import './Metrics.css'

const API_URL = import.meta.env.REACT_APP_API_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000'

const Metrics = () => {
  const { t } = useTranslation()
  const [nodes, setNodes] = useState([])
  const [vms, setVms] = useState([])
  const [selectedNode, setSelectedNode] = useState(null)
  const [selectedVM, setSelectedVM] = useState(null)
  const [timeRange, setTimeRange] = useState(24)
  const [metrics, setMetrics] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchNodes()
    fetchVMs()
  }, [])

  useEffect(() => {
    fetchMetrics()
  }, [selectedNode, selectedVM, timeRange])

  useEffect(() => {
    if (selectedNode) {
      fetchVMs(selectedNode)
    } else {
      setVms([])
      setSelectedVM(null)
    }
  }, [selectedNode])

  const handleExportCSV = async () => {
    try {
      const params = new URLSearchParams()
      if (selectedNode) params.append('node_id', selectedNode)
      if (selectedVM) params.append('vm_id', selectedVM)
      params.append('hours', timeRange)

      const response = await axios.get(`${API_URL}/api/metrics/export/csv?${params}`, {
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `metrics_${new Date().toISOString().split('T')[0]}.csv`)
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
      if (selectedNode) params.append('node_id', selectedNode)
      if (selectedVM) params.append('vm_id', selectedVM)
      params.append('hours', timeRange)

      const response = await axios.get(`${API_URL}/api/metrics/export/json?${params}`, {
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `metrics_${new Date().toISOString().split('T')[0]}.json`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      console.error('Failed to export JSON:', error)
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

  const fetchVMs = async (nodeId = null) => {
    try {
      const url = nodeId
        ? `${API_URL}/api/vms?node_id=${nodeId}`
        : `${API_URL}/api/vms`
      const response = await axios.get(url)
      setVms(response.data)
    } catch (error) {
      console.error('Failed to fetch VMs:', error)
    }
  }

  const fetchMetrics = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (selectedNode) params.append('node_id', selectedNode)
      if (selectedVM) params.append('vm_id', selectedVM)
      params.append('hours', timeRange)

      const [cpuResponse, memoryResponse, diskResponse] = await Promise.all([
        axios.get(`${API_URL}/api/metrics?metric_type=cpu&${params}`),
        axios.get(`${API_URL}/api/metrics?metric_type=memory&${params}`),
        axios.get(`${API_URL}/api/metrics?metric_type=disk&${params}`)
      ])

      // Combine and format metrics data
      const cpuData = cpuResponse.data.map(m => ({
        time: new Date(m.recorded_at).getTime(),
        cpu: m.value
      }))

      const memoryData = memoryResponse.data.map(m => ({
        time: new Date(m.recorded_at).getTime(),
        memory: m.value
      }))

      const diskData = diskResponse.data.map(m => ({
        time: new Date(m.recorded_at).getTime(),
        disk: m.value
      }))

      // Merge data by timestamp
      const timeMap = new Map()
      
      cpuData.forEach(item => {
        if (!timeMap.has(item.time)) {
          timeMap.set(item.time, { time: item.time })
        }
        timeMap.get(item.time).cpu = item.cpu
      })

      memoryData.forEach(item => {
        if (!timeMap.has(item.time)) {
          timeMap.set(item.time, { time: item.time })
        }
        timeMap.get(item.time).memory = item.memory
      })

      diskData.forEach(item => {
        if (!timeMap.has(item.time)) {
          timeMap.set(item.time, { time: item.time })
        }
        timeMap.get(item.time).disk = item.disk
      })

      // Convert to array and sort by time
      const combined = Array.from(timeMap.values())
        .sort((a, b) => a.time - b.time)
        .map(item => ({
          ...item,
          time: new Date(item.time).toLocaleString()
        }))

      setMetrics(combined)
    } catch (error) {
      console.error('Failed to fetch metrics:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading && metrics.length === 0) {
    return <div className="loading">{t('metrics.loading')}</div>
  }

  return (
    <div className="metrics">
      <div className="page-header">
        <h1>{t('metrics.title')}</h1>
      </div>

      <div className="metrics-controls">
        <div className="control-group">
          <label>{t('metrics.selectNode')}</label>
          <select
            value={selectedNode || ''}
            onChange={(e) => setSelectedNode(e.target.value ? parseInt(e.target.value) : null)}
          >
            <option value="">{t('metrics.allNodes')}</option>
            {nodes.map((node) => (
              <option key={node.id} value={node.id}>
                {node.name}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label>{t('metrics.selectVM')}</label>
          <select
            value={selectedVM || ''}
            onChange={(e) => setSelectedVM(e.target.value ? parseInt(e.target.value) : null)}
            disabled={!selectedNode}
          >
            <option value="">{t('metrics.allVMs')}</option>
            {vms.map((vm) => (
              <option key={vm.id} value={vm.id}>
                {vm.name} (VMID: {vm.vmid})
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label>{t('metrics.timeRange')}</label>
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(parseInt(e.target.value))}
          >
            <option value={1}>1 {t('metrics.hours')}</option>
            <option value={6}>6 {t('metrics.hours')}</option>
            <option value={12}>12 {t('metrics.hours')}</option>
            <option value={24}>24 {t('metrics.hours')}</option>
            <option value={48}>48 {t('metrics.hours')}</option>
            <option value={72}>72 {t('metrics.hours')}</option>
            <option value={168}>168 {t('metrics.hours')} (7 days)</option>
          </select>
        </div>
      </div>

      <div className="metrics-actions">
        <button
          className="export-button"
          onClick={handleExportCSV}
        >
          {t('metrics.exportCSV')}
        </button>
        <button
          className="export-button"
          onClick={handleExportJSON}
        >
          {t('metrics.exportJSON')}
        </button>
      </div>

      {metrics.length === 0 ? (
        <div className="no-data">{t('metrics.noData')}</div>
      ) : (
        <div className="metrics-charts">
          <div className="chart-container">
            <h2>{t('metrics.cpu')}</h2>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={metrics}>
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
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-container">
            <h2>{t('metrics.memory')}</h2>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={metrics}>
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
                  dataKey="memory"
                  stroke="#2ecc71"
                  strokeWidth={2}
                  dot={false}
                  name="Memory %"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-container">
            <h2>{t('metrics.disk')}</h2>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={metrics}>
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
                  dataKey="disk"
                  stroke="#f39c12"
                  strokeWidth={2}
                  dot={false}
                  name="Disk %"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  )
}

export default Metrics

