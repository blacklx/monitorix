import { Outlet, Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../contexts/AuthContext'
import { useTheme } from '../contexts/ThemeContext'
import { useWebSocket } from '../contexts/WebSocketContext'
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts'
import VersionInfo from './VersionInfo'
import './Layout.css'

const Layout = () => {
  const { user, logout } = useAuth()
  const { t, i18n } = useTranslation()
  const { theme, themes, toggleTheme, setTheme } = useTheme()
  const location = useLocation()
  const { isConnected, isReconnecting, reconnectAttempt, connectionError } = useWebSocket(() => {})
  
  // Enable keyboard shortcuts
  useKeyboardShortcuts(null, null)

  const isActive = (path) => location.pathname === path

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng)
    localStorage.setItem('language', lng)
  }

  return (
    <div className="layout">
      <nav className="navbar">
        <div className="nav-brand">
          <h1>Monitorix</h1>
        </div>
        <div className="nav-links">
          <Link to="/dashboard" className={isActive('/dashboard') ? 'active' : ''}>
            {t('nav.dashboard')}
          </Link>
          <Link to="/nodes" className={isActive('/nodes') ? 'active' : ''}>
            {t('nav.nodes')}
          </Link>
          <Link to="/vms" className={isActive('/vms') ? 'active' : ''}>
            {t('nav.vms')}
          </Link>
          <Link to="/services" className={isActive('/services') ? 'active' : ''}>
            {t('nav.services')}
          </Link>
          <Link to="/alerts" className={isActive('/alerts') ? 'active' : ''}>
            {t('nav.alerts')}
          </Link>
          <Link to="/metrics" className={isActive('/metrics') ? 'active' : ''}>
            {t('nav.metrics')}
          </Link>
          {user?.is_admin && (
            <>
              <Link to="/users" className={isActive('/users') ? 'active' : ''}>
                {t('nav.users')}
              </Link>
              <Link to="/backup" className={isActive('/backup') ? 'active' : ''}>
                {t('nav.backup')}
              </Link>
              <Link to="/audit-logs" className={isActive('/audit-logs') ? 'active' : ''}>
                {t('nav.auditLogs')}
              </Link>
            </>
          )}
          <Link to="/notification-channels" className={isActive('/notification-channels') ? 'active' : ''}>
            {t('nav.notificationChannels')}
          </Link>
          <Link to="/alert-rules" className={isActive('/alert-rules') ? 'active' : ''}>
            {t('nav.alertRules')}
          </Link>
        </div>
        <div className="nav-user">
          <Link to="/profile" className={isActive('/profile') ? 'active' : ''}>
            {t('nav.profile')}
          </Link>
          <div 
            className={`websocket-status ${isReconnecting ? 'reconnecting' : ''}`}
            title={
              isConnected 
                ? t('common.websocketConnected') 
                : isReconnecting 
                  ? t('common.websocketReconnecting', { attempt: reconnectAttempt })
                  : connectionError || t('common.websocketDisconnected')
            }
          >
            <span className={`status-indicator ${isConnected ? 'connected' : isReconnecting ? 'reconnecting' : 'disconnected'}`}></span>
            <span className="status-text">
              {isConnected 
                ? t('common.connected') 
                : isReconnecting 
                  ? t('common.reconnecting', { attempt: reconnectAttempt })
                  : t('common.disconnected')}
            </span>
          </div>
          <select
            value={theme}
            onChange={(e) => setTheme(e.target.value)}
            className="theme-select"
            title={t('nav.theme')}
          >
            {themes.map(t => (
              <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
            ))}
          </select>
          <select
            value={i18n.language}
            onChange={(e) => changeLanguage(e.target.value)}
            className="language-select"
          >
            <option value="en">{t('languages.en')}</option>
            <option value="no">{t('languages.no')}</option>
            <option value="sv">{t('languages.sv')}</option>
            <option value="da">{t('languages.da')}</option>
            <option value="fi">{t('languages.fi')}</option>
            <option value="fr">{t('languages.fr')}</option>
            <option value="de">{t('languages.de')}</option>
          </select>
          <span>{user?.username}</span>
          <button onClick={logout}>{t('nav.logout')}</button>
        </div>
      </nav>
      <main className="main-content">
        <Outlet />
      </main>
      <footer className="app-footer">
        <VersionInfo />
      </footer>
    </div>
  )
}

export default Layout

