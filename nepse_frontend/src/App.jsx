import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Navigation from './components/Navigation';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import StockDetail from './pages/StockDetail';
import WatchlistAlerts from './pages/WatchlistAlerts';
import Portfolio from './pages/Portfolio';
import Scanners from './pages/Scanners';

// Protected Route wrapper component
function ProtectedRoute({ children }) {
  const token = localStorage.getItem('access_token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export default function App() {
  return (
    <Router>
      <Routes>
        {/* Public Login Route */}
        <Route path="/login" element={<Login />} />

        {/* Protected Application Layout */}
        <Route 
          path="/*" 
          element={
            <ProtectedRoute>
              <div className="app-container">
                <Navigation />
                <div style={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                  <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/stock/:symbol" element={<StockDetail />} />
                    <Route path="/portfolio" element={<Portfolio />} />
                    <Route path="/scanners" element={<Scanners />} />
                    <Route path="/watchlist" element={<WatchlistAlerts />} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                  </Routes>
                </div>
              </div>
            </ProtectedRoute>
          } 
        />
      </Routes>
    </Router>
  );
}
