import { Outlet, Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../contexts/AuthContext'
import { useTheme } from '../contexts/ThemeContext'
import { useWebSocket } from '../hooks/useWebSocket'
import './Layout.css'

const Layout = () => {
  const { user, logout } = useAuth()
  const { t, i18n } = useTranslation()
  const { theme, toggleTheme } = useTheme()
  const location = useLocation()
  const { isConnected } = useWebSocket(() => {})

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
            <Link to="/users" className={isActive('/users') ? 'active' : ''}>
              {t('nav.users')}
            </Link>
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
          <div className="websocket-status" title={isConnected ? t('common.websocketConnected') : t('common.websocketDisconnected')}>
            <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}></span>
            <span className="status-text">{isConnected ? t('common.connected') : t('common.disconnected')}</span>
          </div>
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
    </div>
  )
}

export default Layout

