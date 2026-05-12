import './App.css'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import Navigation from './components/Navigation'
import ProtectedRoute from './components/ProtectedRoute'
import AppShell from './components/AppShell'

// Pages
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import WatchlistPage from './pages/WatchlistPage'
import SignalsPage from './pages/SignalsPage'

function App() {
    return (
        <Router>
            <AuthProvider>
                <AppShell>
                    <div className="min-h-screen">
                        <Navigation />
                        <Routes>
                            <Route path="/login" element={<LoginPage />} />
                            <Route path="/register" element={<RegisterPage />} />

                            <Route
                                path="/dashboard"
                                element={
                                    <ProtectedRoute>
                                        <DashboardPage />
                                    </ProtectedRoute>
                                }
                            />
                            <Route
                                path="/watchlist"
                                element={
                                    <ProtectedRoute>
                                        <WatchlistPage />
                                    </ProtectedRoute>
                                }
                            />
                            <Route
                                path="/signals"
                                element={
                                    <ProtectedRoute>
                                        <SignalsPage />
                                    </ProtectedRoute>
                                }
                            />

                            <Route path="/" element={<Navigate to="/dashboard" replace />} />
                        </Routes>
                    </div>
                </AppShell>
            </AuthProvider>
        </Router>
    )
}

export default App
