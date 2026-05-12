import React, { createContext, useState, useCallback, useEffect } from 'react'
import { authAPI } from '../api/index'

export const AuthContext = createContext(null)

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    // Initialize auth on mount
    useEffect(() => {
        const token = localStorage.getItem('access_token')
        if (token) {
            fetchUserProfile()
        } else {
            setLoading(false)
        }
    }, [])

    const fetchUserProfile = useCallback(async () => {
        try {
            const response = await authAPI.getProfile()
            setUser(response.data.data)
            setError(null)
        } catch (err) {
            console.error('Failed to fetch profile:', err)
            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')
            setUser(null)
        } finally {
            setLoading(false)
        }
    }, [])

    const register = useCallback(async (email, username, password, firstName = '', lastName = '') => {
        try {
            setLoading(true)
            const response = await authAPI.register(email, username, password, firstName, lastName)
            setError(null)
            return response.data
        } catch (err) {
            const message = err.response?.data?.message || 'Registration failed'
            setError(message)
            throw err
        } finally {
            setLoading(false)
        }
    }, [])

    const login = useCallback(async (email, password) => {
        try {
            setLoading(true)
            const response = await authAPI.login(email, password)
            const { access, refresh } = response.data

            localStorage.setItem('access_token', access)
            localStorage.setItem('refresh_token', refresh)

            await fetchUserProfile()
            setError(null)
            return response.data
        } catch (err) {
            const message = err.response?.data?.message || 'Login failed'
            setError(message)
            throw err
        } finally {
            setLoading(false)
        }
    }, [fetchUserProfile])

    const logout = useCallback(() => {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        setUser(null)
        setError(null)
    }, [])

    const updateProfile = useCallback(async (data) => {
        try {
            const response = await authAPI.updateProfile(data)
            setUser(response.data.data)
            setError(null)
            return response.data
        } catch (err) {
            const message = err.response?.data?.message || 'Update failed'
            setError(message)
            throw err
        }
    }, [])

    const value = {
        user,
        loading,
        error,
        isAuthenticated: !!user,
        register,
        login,
        logout,
        updateProfile,
        fetchUserProfile,
    }

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export default AuthContext
