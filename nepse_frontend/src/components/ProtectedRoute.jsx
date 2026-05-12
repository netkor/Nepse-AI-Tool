import React from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export const ProtectedRoute = ({ children }) => {
    const { isAuthenticated, loading } = useAuth()

    if (loading) {
        return (
            <div className="flex min-h-[70vh] items-center justify-center px-6">
                <div className="panel-surface rounded-3xl px-8 py-6 text-sm text-slate-200 shadow-soft">
                    Preparing your workspace...
                </div>
            </div>
        )
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />
    }

    return children
}

export default ProtectedRoute
