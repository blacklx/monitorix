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
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

/**
 * Keyboard shortcuts hook
 * 
 * Shortcuts:
 * - Ctrl/Cmd + K: Search (opens search modal if implemented)
 * - Ctrl/Cmd + D: Dashboard
 * - Ctrl/Cmd + N: Nodes
 * - Ctrl/Cmd + V: VMs
 * - Ctrl/Cmd + S: Services
 * - Ctrl/Cmd + A: Alerts
 * - Ctrl/Cmd + M: Metrics
 * - Ctrl/Cmd + U: Users (admin only)
 * - Ctrl/Cmd + P: Profile
 * - Ctrl/Cmd + ,: Settings (if implemented)
 * - Esc: Close modals/dialogs
 */
export const useKeyboardShortcuts = (onSearch, onCloseModal) => {
  const navigate = useNavigate()

  useEffect(() => {
    const handleKeyDown = (e) => {
      // Ignore if typing in input, textarea, or contenteditable
      if (
        e.target.tagName === 'INPUT' ||
        e.target.tagName === 'TEXTAREA' ||
        e.target.isContentEditable
      ) {
        // Allow Esc to close modals even when typing
        if (e.key === 'Escape' && onCloseModal) {
          onCloseModal()
        }
        return
      }

      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0
      const ctrlKey = isMac ? e.metaKey : e.ctrlKey

      // Ctrl/Cmd + K: Search
      if (ctrlKey && e.key === 'k') {
        e.preventDefault()
        if (onSearch) {
          onSearch()
        }
        return
      }

      // Ctrl/Cmd + D: Dashboard
      if (ctrlKey && e.key === 'd') {
        e.preventDefault()
        navigate('/dashboard')
        return
      }

      // Ctrl/Cmd + N: Nodes
      if (ctrlKey && e.key === 'n') {
        e.preventDefault()
        navigate('/nodes')
        return
      }

      // Ctrl/Cmd + V: VMs
      if (ctrlKey && e.key === 'v') {
        e.preventDefault()
        navigate('/vms')
        return
      }

      // Ctrl/Cmd + S: Services
      if (ctrlKey && e.key === 's') {
        e.preventDefault()
        navigate('/services')
        return
      }

      // Ctrl/Cmd + A: Alerts
      if (ctrlKey && e.key === 'a') {
        e.preventDefault()
        navigate('/alerts')
        return
      }

      // Ctrl/Cmd + M: Metrics
      if (ctrlKey && e.key === 'm') {
        e.preventDefault()
        navigate('/metrics')
        return
      }

      // Ctrl/Cmd + U: Users (admin only)
      if (ctrlKey && e.key === 'u') {
        e.preventDefault()
        navigate('/users')
        return
      }

      // Ctrl/Cmd + P: Profile
      if (ctrlKey && e.key === 'p') {
        e.preventDefault()
        navigate('/profile')
        return
      }

      // Esc: Close modals
      if (e.key === 'Escape' && onCloseModal) {
        onCloseModal()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [navigate, onSearch, onCloseModal])
}

