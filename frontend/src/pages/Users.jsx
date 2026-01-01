import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import axios from 'axios'
import { formatDate } from '../utils/dateFormat'
import { useAuth } from '../contexts/AuthContext'
import './Users.css'

const API_URL = import.meta.env.VITE_API_URL || import.meta.env.REACT_APP_API_URL || ''

const Users = () => {
  const { t } = useTranslation()
  const { user: currentUser } = useAuth()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingUser, setEditingUser] = useState(null)
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    is_active: true,
    is_admin: false
  })
  const [error, setError] = useState(null)
  const [deleteConfirm, setDeleteConfirm] = useState(null)

  useEffect(() => {
    if (currentUser?.is_admin) {
      fetchUsers()
    } else {
      setLoading(false)
    }
  }, [currentUser])

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/users`)
      setUsers(response.data)
    } catch (error) {
      console.error('Failed to fetch users:', error)
      setError(error.response?.data?.detail || t('common.error'))
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    setEditingUser(null)
    setFormData({
      username: '',
      email: '',
      password: '',
      is_active: true,
      is_admin: false
    })
    setError(null)
    setShowModal(true)
  }

  const handleEdit = (user) => {
    setEditingUser(user)
    setFormData({
      username: user.username,
      email: user.email,
      password: '', // Don't show password
      is_active: user.is_active,
      is_admin: user.is_admin
    })
    setError(null)
    setShowModal(true)
  }

  const handleDelete = async (userId) => {
    try {
      await axios.delete(`${API_URL}/api/users/${userId}`)
      setDeleteConfirm(null)
      fetchUsers()
    } catch (error) {
      console.error('Failed to delete user:', error)
      setError(error.response?.data?.detail || t('common.error'))
    }
  }

  const handleToggleActive = async (userId) => {
    try {
      await axios.put(`${API_URL}/api/users/${userId}/toggle-active`)
      fetchUsers()
    } catch (error) {
      console.error('Failed to toggle user active status:', error)
      setError(error.response?.data?.detail || t('common.error'))
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    try {
      if (editingUser) {
        // Update existing user
        const updateData = {
          username: formData.username,
          email: formData.email,
          is_active: formData.is_active,
          is_admin: formData.is_admin
        }
        if (formData.password) {
          updateData.password = formData.password
        }
        await axios.put(`${API_URL}/api/users/${editingUser.id}`, updateData)
      } else {
        // Create new user
        await axios.post(`${API_URL}/api/users`, formData)
      }
      setShowModal(false)
      fetchUsers()
    } catch (error) {
      setError(error.response?.data?.detail || t('common.error'))
    }
  }

  if (!currentUser?.is_admin) {
    return (
      <div className="users">
        <div className="error-message">
          {t('users.accessDenied')}
        </div>
      </div>
    )
  }

  if (loading) {
    return <div className="loading">{t('common.loading')}</div>
  }

  return (
    <div className="users">
      <div className="page-header">
        <h1>{t('users.title')}</h1>
        <button className="add-button" onClick={handleAdd}>
          {t('users.addUser')}
        </button>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="users-table">
        <table>
          <thead>
            <tr>
              <th>{t('users.username')}</th>
              <th>{t('users.email')}</th>
              <th>{t('users.status')}</th>
              <th>{t('users.role')}</th>
              <th>{t('users.createdAt')}</th>
              <th>{t('common.actions')}</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td>{user.username}</td>
                <td>{user.email}</td>
                <td>
                  <span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>
                    {user.is_active ? t('users.active') : t('users.inactive')}
                  </span>
                </td>
                <td>
                  {user.is_admin && (
                    <span className="admin-badge">{t('users.admin')}</span>
                  )}
                </td>
                <td>{formatDate(user.created_at)}</td>
                <td>
                  <div className="action-buttons">
                    <button
                      className="action-button edit-button"
                      onClick={() => handleEdit(user)}
                    >
                      {t('common.edit')}
                    </button>
                    <button
                      className={`action-button ${user.is_active ? 'deactivate-button' : 'activate-button'}`}
                      onClick={() => handleToggleActive(user.id)}
                      disabled={user.id === currentUser.id}
                    >
                      {user.is_active ? t('users.deactivate') : t('users.activate')}
                    </button>
                    <button
                      className="action-button delete-button"
                      onClick={() => setDeleteConfirm(user.id)}
                      disabled={user.id === currentUser.id}
                    >
                      {t('common.delete')}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingUser ? t('users.editUser') : t('users.addUser')}</h2>
              <button className="close-button" onClick={() => setShowModal(false)}>
                {t('common.close')}
              </button>
            </div>
            
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>{t('users.username')}</label>
                <input
                  type="text"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label>{t('users.email')}</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label>{editingUser ? t('users.newPassword') : t('users.password')}</label>
                <input
                  type="password"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  placeholder={editingUser ? t('users.passwordPlaceholder') : ''}
                  required={!editingUser}
                  minLength={8}
                />
                {editingUser && (
                  <small>{t('users.passwordPlaceholder')}</small>
                )}
              </div>

              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  />
                  {t('users.active')}
                </label>
              </div>

              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={formData.is_admin}
                    onChange={(e) => setFormData({ ...formData, is_admin: e.target.checked })}
                    disabled={editingUser?.id === currentUser.id}
                  />
                  {t('users.admin')}
                </label>
                {editingUser?.id === currentUser.id && (
                  <small>{t('users.cannotRemoveOwnAdmin')}</small>
                )}
              </div>

              {error && (
                <div className="error-message">
                  {error}
                </div>
              )}

              <div className="form-actions">
                <button type="button" onClick={() => setShowModal(false)}>
                  {t('common.cancel')}
                </button>
                <button type="submit">
                  {t('common.save')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {deleteConfirm && (
        <div className="modal-overlay" onClick={() => setDeleteConfirm(null)}>
          <div className="modal-content delete-confirm" onClick={(e) => e.stopPropagation()}>
            <h2>{t('users.deleteUser')}</h2>
            <p>{t('users.confirmDelete')}</p>
            <div className="form-actions">
              <button onClick={() => setDeleteConfirm(null)}>
                {t('common.cancel')}
              </button>
              <button className="delete-button" onClick={() => handleDelete(deleteConfirm)}>
                {t('common.delete')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Users

