import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import { Loader2, Trash2, BellRing, Eye, EyeOff } from 'lucide-react';

export default function WatchlistAlerts() {
  const [watchlist, setWatchlist] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const fetchData = async () => {
    try {
      setLoading(true);
      setError('');
      
      // Fetch Watchlist
      const watchlistResponse = await api.get('/api/watchlist/');
      setWatchlist(watchlistResponse.data);

      // Fetch Alerts
      const alertsResponse = await api.get('/api/alerts/');
      setAlerts(alertsResponse.data);
    } catch (err) {
      setError('Failed to fetch watchlist and alerts data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRemoveWatchlist = async (symbol) => {
    try {
      await api.delete(`/api/watchlist/${symbol}/`);
      setWatchlist(prev => prev.filter(w => w.stock_details.symbol !== symbol));
    } catch (err) {
      console.error('Failed to remove watchlist entry', err);
    }
  };

  const handleDeleteAlert = async (id) => {
    try {
      await api.delete(`/api/alerts/${id}/`);
      setAlerts(prev => prev.filter(a => a.id !== id));
    } catch (err) {
      console.error('Failed to delete alert', err);
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
        <Loader2 className="animate-spin" size={48} color="var(--accent-primary)" />
      </div>
    );
  }

  return (
    <div className="main-content">
      <div style={{ marginBottom: '24px' }}>
        <h1 className="page-title">Watchlist & Alerts</h1>
        <p className="page-subtitle">Track your favorite assets and configure price thresholds</p>
      </div>

      {error && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.2)',
          color: 'var(--color-danger)',
          padding: '16px',
          borderRadius: '12px',
          marginBottom: '24px'
        }}>
          {error}
        </div>
      )}

      {/* Grid Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '32px', alignItems: 'start' }}>
        
        {/* Watchlist Section */}
        <div className="glass-card" style={{ padding: '24px 0' }}>
          <div style={{ padding: '0 24px 20px 24px', borderBottom: '1px solid var(--border-standard)' }}>
            <h3 style={{ fontSize: '18px', fontWeight: '600' }}>Active Watchlist</h3>
          </div>

          <div className="table-container" style={{ border: 'none', borderRadius: 0 }}>
            <table className="custom-table">
              <thead>
                <tr>
                  <th style={{ paddingLeft: '24px' }}>Symbol</th>
                  <th>LTP (Rs.)</th>
                  <th>Change</th>
                  <th style={{ textAlign: 'right', paddingRight: '24px' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {watchlist.map((w) => {
                  const s = w.stock_details;
                  const change = parseFloat(s.change_percentage);
                  return (
                    <tr key={w.id}>
                      <td 
                        style={{ paddingLeft: '24px', fontWeight: '700', cursor: 'pointer' }}
                        onClick={() => navigate(`/stock/${s.symbol}`)}
                      >
                        {s.symbol}
                      </td>
                      <td>Rs. {parseFloat(s.current_price).toFixed(2)}</td>
                      <td className={change > 0 ? 'trend-up' : change < 0 ? 'trend-down' : ''}>
                        {change > 0 ? `+${change.toFixed(2)}%` : `${change.toFixed(2)}%`}
                      </td>
                      <td style={{ textAlign: 'right', paddingRight: '24px' }}>
                        <button 
                          onClick={() => handleRemoveWatchlist(s.symbol)}
                          style={{
                            background: 'transparent',
                            border: 'none',
                            cursor: 'pointer',
                            color: 'var(--text-muted)'
                          }}
                          onMouseEnter={(e) => e.currentTarget.style.color = 'var(--color-danger)'}
                          onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-muted)'}
                        >
                          <Trash2 size={16} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
                {watchlist.length === 0 && (
                  <tr>
                    <td colSpan="4" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                      No items in your watchlist. Visit the Dashboard to add.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Alerts Section */}
        <div className="glass-card" style={{ padding: '24px 0' }}>
          <div style={{ padding: '0 24px 20px 24px', borderBottom: '1px solid var(--border-standard)' }}>
            <h3 style={{ fontSize: '18px', fontWeight: '600' }}>Configured Price Alerts</h3>
          </div>

          <div className="table-container" style={{ border: 'none', borderRadius: 0 }}>
            <table className="custom-table">
              <thead>
                <tr>
                  <th style={{ paddingLeft: '24px' }}>Asset</th>
                  <th>Condition</th>
                  <th>Threshold</th>
                  <th>Status</th>
                  <th style={{ textAlign: 'right', paddingRight: '24px' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {alerts.map((a) => {
                  const s = a.stock_details;
                  return (
                    <tr key={a.id}>
                      <td 
                        style={{ paddingLeft: '24px', fontWeight: '700', cursor: 'pointer' }}
                        onClick={() => navigate(`/stock/${s.symbol}`)}
                      >
                        {s.symbol}
                      </td>
                      <td style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                        {a.alert_type === 'PRICE_ABOVE' ? 'Rises Above' : 'Falls Below'}
                      </td>
                      <td style={{ fontWeight: '500' }}>Rs. {parseFloat(a.target_value).toFixed(2)}</td>
                      <td>
                        <span style={{
                          background: a.is_triggered ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                          color: a.is_triggered ? 'var(--color-success)' : 'var(--color-warning)',
                          padding: '2px 8px',
                          borderRadius: '4px',
                          fontSize: '11px',
                          fontWeight: '600',
                          border: a.is_triggered ? '1px solid rgba(16, 185, 129, 0.2)' : '1px solid rgba(245, 158, 11, 0.2)'
                        }}>
                          {a.is_triggered ? 'Triggered' : 'Active'}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right', paddingRight: '24px' }}>
                        <button 
                          onClick={() => handleDeleteAlert(a.id)}
                          style={{
                            background: 'transparent',
                            border: 'none',
                            cursor: 'pointer',
                            color: 'var(--text-muted)'
                          }}
                          onMouseEnter={(e) => e.currentTarget.style.color = 'var(--color-danger)'}
                          onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-muted)'}
                        >
                          <Trash2 size={16} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
                {alerts.length === 0 && (
                  <tr>
                    <td colSpan="5" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                      No active alerts set up.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>
  );
}
