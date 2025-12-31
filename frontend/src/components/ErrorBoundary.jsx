import React from 'react'
import { useTranslation } from 'react-i18next'
import './ErrorBoundary.css'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true }
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      error,
      errorInfo
    })
    console.error('Error caught by boundary:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <ErrorFallback
          error={this.state.error}
          errorInfo={this.state.errorInfo}
          onReset={() => this.setState({ hasError: false, error: null, errorInfo: null })}
        />
      )
    }

    return this.props.children
  }
}

const ErrorFallback = ({ error, errorInfo, onReset }) => {
  const { t } = useTranslation()

  return (
    <div className="error-boundary">
      <div className="error-boundary-content">
        <h1>{t('error.title')}</h1>
        <p>{t('error.message')}</p>
        {process.env.NODE_ENV === 'development' && error && (
          <details className="error-details">
            <summary>{t('error.details')}</summary>
            <pre>{error.toString()}</pre>
            {errorInfo && <pre>{errorInfo.componentStack}</pre>}
          </details>
        )}
        <button onClick={onReset} className="error-reset-button">
          {t('error.reset')}
        </button>
      </div>
    </div>
  )
}

export default ErrorBoundary

