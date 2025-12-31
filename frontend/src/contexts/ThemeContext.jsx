import { createContext, useState, useContext, useEffect } from 'react'

const ThemeContext = createContext(null)

const THEMES = ['light', 'dark', 'blue', 'green', 'purple']

export const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState(() => {
    // Check localStorage first, then system preference
    const savedTheme = localStorage.getItem('theme')
    if (savedTheme && THEMES.includes(savedTheme)) {
      return savedTheme
    }
    // Check system preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark'
    }
    return 'light'
  })

  useEffect(() => {
    // Apply theme to document
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])

  const toggleTheme = () => {
    const currentIndex = THEMES.indexOf(theme)
    const nextIndex = (currentIndex + 1) % THEMES.length
    setTheme(THEMES[nextIndex])
  }

  const setThemeByName = (themeName) => {
    if (THEMES.includes(themeName)) {
      setTheme(themeName)
    }
  }

  return (
    <ThemeContext.Provider value={{ theme, themes: THEMES, toggleTheme, setTheme: setThemeByName }}>
      {children}
    </ThemeContext.Provider>
  )
}

export const useTheme = () => {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider')
  }
  return context
}

