import React, { createContext, useState, useEffect } from 'react'

export const AuthContext = createContext()

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [userId, setUserId] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if token exists in localStorage
    const token = localStorage.getItem('access_token')
    const user_id = localStorage.getItem('user_id')
    
    if (token && user_id) {
      setIsAuthenticated(true)
      setUserId(user_id)
    }
    setLoading(false)
  }, [])

  const login = (token, user_id) => {
    localStorage.setItem('access_token', token)
    localStorage.setItem('user_id', user_id)
    setIsAuthenticated(true)
    setUserId(user_id)
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_id')
    setIsAuthenticated(false)
    setUserId(null)
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, userId, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = React.useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
