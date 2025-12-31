import React, { Suspense } from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { I18nextProvider } from 'react-i18next'
import { ThemeProvider } from './contexts/ThemeContext'
import App from './App'
import i18n from './i18n/config'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ThemeProvider>
      <I18nextProvider i18n={i18n}>
        <Suspense fallback={<div>Loading...</div>}>
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </Suspense>
      </I18nextProvider>
    </ThemeProvider>
  </React.StrictMode>,
)

