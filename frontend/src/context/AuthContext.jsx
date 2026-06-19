import { useState, useEffect } from 'react'
import { authApi } from '../api/client'
import AuthContext from './auth-context'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(() => Boolean(localStorage.getItem('access')))

  useEffect(() => {
    const token = localStorage.getItem('access')
    if (!token) return

    authApi.me()
      .then(({ data }) => setUser(data))
      .catch(() => {
        localStorage.removeItem('access')
        localStorage.removeItem('refresh')
      })
      .finally(() => setLoading(false))
  }, [])

  const login = async (credentials) => {
    const { data } = await authApi.login(credentials)
    localStorage.setItem('access', data.access)
    localStorage.setItem('refresh', data.refresh)
    setUser(data.user)
    return data
  }

  const logout = () => {
    localStorage.removeItem('access')
    localStorage.removeItem('refresh')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
