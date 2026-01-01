/**
 * Copyright 2024 Monitorix Contributors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { WebSocketProvider } from './contexts/WebSocketContext'
import ErrorBoundary from './components/ErrorBoundary'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Nodes from './pages/Nodes'
import VMs from './pages/VMs'
import Services from './pages/Services'
import Alerts from './pages/Alerts'
import Metrics from './pages/Metrics'
import Users from './pages/Users'
import Profile from './pages/Profile'
import NotificationChannels from './pages/NotificationChannels'
import AlertRules from './pages/AlertRules'
import Backup from './pages/Backup'
import AuditLogs from './pages/AuditLogs'
import Layout from './components/Layout'
import PrivateRoute from './components/PrivateRoute'

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <WebSocketProvider>
          <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <PrivateRoute>
                <Layout />
              </PrivateRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="nodes" element={<Nodes />} />
            <Route path="vms" element={<VMs />} />
            <Route path="services" element={<Services />} />
            <Route path="alerts" element={<Alerts />} />
            <Route path="metrics" element={<Metrics />} />
            <Route path="users" element={<Users />} />
            <Route path="profile" element={<Profile />} />
            <Route path="notification-channels" element={<NotificationChannels />} />
            <Route path="alert-rules" element={<AlertRules />} />
            <Route path="backup" element={<Backup />} />
            <Route path="audit-logs" element={<AuditLogs />} />
          </Route>
        </Routes>
        </WebSocketProvider>
      </AuthProvider>
    </ErrorBoundary>
  )
}

export default App

