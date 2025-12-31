import './LoadingSpinner.css'

const LoadingSpinner = ({ size = 'medium', message = null }) => {
  return (
    <div className={`loading-spinner-container ${size}`}>
      <div className="loading-spinner"></div>
      {message && <p className="loading-message">{message}</p>}
    </div>
  )
}

export default LoadingSpinner

