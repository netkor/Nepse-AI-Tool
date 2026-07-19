import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import { 
  Loader2, Trash2, Plus, RefreshCw, AlertCircle, TrendingUp, TrendingDown, Briefcase, PlusCircle 
} from 'lucide-react';

export default function Portfolio() {
  const [portfolio, setPortfolio] = useState([]);
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  const [riskThreshold, setRiskThreshold] = useState(50);
  const [riskData, setRiskData] = useState(null);
  
  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedStockId, setSelectedStockId] = useState('');
  const [balance, setBalance] = useState('');
  const [costPrice, setCostPrice] = useState('');
  const [modalError, setModalError] = useState('');
  const [modalSuccess, setModalSuccess] = useState('');

  const navigate = useNavigate();

  const fetchData = async () => {
    try {
      setLoading(true);
      setError('');
      
      const [portfolioResponse, stocksResponse, riskResponse] = await Promise.all([
        api.get('/api/stocks/portfolio/'),
        api.get('/api/stocks/'),
        api.get(`/api/stocks/portfolio/risk/?threshold=${riskThreshold}`)
      ]);
      setPortfolio(portfolioResponse.data);
      setStocks(stocksResponse.data);
      setRiskData(riskResponse.data);
    } catch (err) {
      setError('Failed to fetch portfolio data. Please make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [riskThreshold]);

  const handleRemoveItem = async (id) => {
    if (!window.confirm('Are you sure you want to delete this scrip from your portfolio?')) return;
    try {
      await api.delete(`/api/stocks/portfolio/${id}/`);
      setPortfolio(prev => prev.filter(item => item.id !== id));
    } catch (err) {
      console.error('Failed to remove portfolio entry', err);
    }
  };

  const handleAddHolding = async (e) => {
    e.preventDefault();
    setModalError('');
    setModalSuccess('');

    if (!selectedStockId || !balance || !costPrice) {
      setModalError('Please fill in all inputs');
      return;
    }

    try {
      const existing = portfolio.find(p => p.stock === parseInt(selectedStockId));
      if (existing) {
        await api.put(`/api/stocks/portfolio/${existing.id}/`, {
          stock: selectedStockId,
          balance: parseInt(balance),
          cost_price: parseFloat(costPrice)
        });
        setModalSuccess('Holding updated successfully!');
      } else {
        await api.post('/api/stocks/portfolio/', {
          stock: selectedStockId,
          balance: parseInt(balance),
          cost_price: parseFloat(costPrice)
        });
        setModalSuccess('Holding added successfully!');
      }

      const portfolioResponse = await api.get('/api/stocks/portfolio/');
      setPortfolio(portfolioResponse.data);
      
      setTimeout(() => {
        setIsModalOpen(false);
        setBalance('');
        setCostPrice('');
        setSelectedStockId('');
        setModalSuccess('');
        fetchData(); // Refetch to update risk analysis
      }, 1000);

    } catch (err) {
      setModalError('Failed to save holding. Check if parameters are valid.');
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
        <Loader2 className="animate-spin" size={48} color="var(--accent-primary)" />
      </div>
    );
  }

  // Calculate portfolio totals
  const totalInvestment = portfolio.reduce((sum, item) => sum + item.total_investment, 0);
  const currentValue = portfolio.reduce((sum, item) => sum + item.current_value, 0);
  const overallPL = currentValue - totalInvestment;
  const plPercentage = totalInvestment > 0 ? (overallPL / totalInvestment) * 100 : 0;
  const isProfit = overallPL >= 0;

  // Filter for active BUY or SELL signals on held stocks
  const activeAlerts = portfolio.filter(item => 
    item.active_signal && (item.active_signal.recommendation === 'BUY' || item.active_signal.recommendation === 'SELL')
  );

  // Sector Diversification Calculation via Backend API
  const overExposedSectors = riskData ? riskData.sectors.filter(s => s.is_over_exposed) : [];

  return (
    <div className="main-content">
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h1 className="page-title">My Stock Portfolio</h1>
          <p className="page-subtitle">Track shares balance, LTP values, overall P/L, and actionable buy/sell signals</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <label style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-secondary)' }}>Sector Risk Threshold</label>
            <select 
              value={riskThreshold} 
              onChange={(e) => {
                setRiskThreshold(Number(e.target.value));
              }}
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid var(--border-standard)',
                color: 'white',
                padding: '8px 12px',
                borderRadius: '6px',
                fontSize: '13px',
                outline: 'none',
                cursor: 'pointer'
              }}
            >
              <option value={30} style={{ color: 'black' }}>30% (Strict)</option>
              <option value={40} style={{ color: 'black' }}>40% (Moderate)</option>
              <option value={50} style={{ color: 'black' }}>50% (Default)</option>
              <option value={60} style={{ color: 'black' }}>60% (Relaxed)</option>
              <option value={100} style={{ color: 'black' }}>100% (No Limit)</option>
            </select>
          </div>
          <button onClick={() => setIsModalOpen(true)} className="btn-primary" style={{ width: 'auto', display: 'flex', alignItems: 'center', gap: '8px', height: '37px', alignSelf: 'flex-end' }}>
            <PlusCircle size={18} /> Add Holding
          </button>
        </div>
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

      {/* Summary Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: '24px',
        marginBottom: '40px'
      }}>
        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <span style={{ color: 'var(--text-secondary)', fontSize: '14px', fontWeight: '500' }}>Total Cost Basis</span>
          <span style={{ fontSize: '28px', fontWeight: '700' }}>Rs. {totalInvestment.toLocaleString([], { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
        </div>

        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <span style={{ color: 'var(--text-secondary)', fontSize: '14px', fontWeight: '500' }}>Value as of LTP</span>
          <span style={{ fontSize: '28px', fontWeight: '700' }}>Rs. {currentValue.toLocaleString([], { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
        </div>

        <div className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '8px', borderLeft: `4px solid ${isProfit ? 'var(--color-success)' : 'var(--color-danger)'}` }}>
          <span style={{ color: 'var(--text-secondary)', fontSize: '14px', fontWeight: '500' }}>Overall Profit / Loss</span>
          <span style={{ fontSize: '28px', fontWeight: '700', color: isProfit ? 'var(--color-success)' : 'var(--color-danger)' }}>
            Rs. {overallPL.toLocaleString([], { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
          <span style={{ fontSize: '13px', color: isProfit ? 'var(--color-success)' : 'var(--color-danger)', display: 'flex', alignItems: 'center', gap: '4px' }}>
            {isProfit ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
            {isProfit ? '+' : ''}{plPercentage.toFixed(2)}%
          </span>
        </div>
      </div>

      {/* Warnings & Actionable Alerts for holdings */}
      {(activeAlerts.length > 0 || overExposedSectors.length > 0) && (
        <div style={{
          background: 'rgba(99, 102, 241, 0.05)',
          border: '1px solid rgba(99, 102, 241, 0.15)',
          borderRadius: '12px',
          padding: '20px',
          marginBottom: '40px'
        }}>
          {overExposedSectors.length > 0 && (
            <div style={{ marginBottom: activeAlerts.length > 0 ? '24px' : '0' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', color: 'var(--color-danger)', fontWeight: '600' }}>
                <AlertCircle size={20} />
                <h4>Diversification Warning: High Sector Risk</h4>
              </div>
              <ul style={{ paddingLeft: '24px', margin: 0, color: 'var(--text-secondary)', fontSize: '14px' }}>
                {overExposedSectors.map(s => (
                  <li key={s.sector}>
                    Your portfolio is heavily concentrated in <strong>{s.sector}</strong> ({s.percentage.toFixed(1)}%). 
                    Consider diversifying into other sectors to reduce systemic risk.
                  </li>
                ))}
              </ul>
            </div>
          )}

          {activeAlerts.length > 0 && (
            <>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', color: 'var(--accent-primary)', fontWeight: '600' }}>
                <AlertCircle size={20} />
                <h4>Action Signals Detected on Your Holdings ({activeAlerts.length})</h4>
              </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {activeAlerts.map((item) => {
              const sig = item.active_signal;
              const isBuy = sig.recommendation === 'BUY';
              
              return (
                <div 
                  key={item.id} 
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    background: 'rgba(255, 255, 255, 0.01)',
                    padding: '12px 16px',
                    borderRadius: '8px',
                    borderLeft: `4px solid ${isBuy ? 'var(--color-success)' : 'var(--color-danger)'}`
                  }}
                >
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <div>
                      <span style={{ fontWeight: '700', fontSize: '15px', marginRight: '12px' }}>{item.stock_details.symbol}</span>
                      <span style={{
                        fontSize: '11px',
                        fontWeight: '700',
                        background: isBuy ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                        color: isBuy ? 'var(--color-success)' : 'var(--color-danger)',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        display: 'inline-block',
                        verticalAlign: 'middle'
                      }}>
                        {isBuy ? 'BUY ALERT' : 'SELL ALERT'}
                      </span>
                    </div>
                    <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{sig.desc}</span>
                  </div>
                </div>
              );
            })}
          </div>
            </>
          )}
        </div>
      )}

      {/* Holdings Listing Card */}
      <div className="glass-card" style={{ padding: '24px 0' }}>
        <div style={{ padding: '0 24px 20px 24px', borderBottom: '1px solid var(--border-standard)' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600' }}>Investment Holdings</h3>
        </div>

        <div className="table-container" style={{ border: 'none', borderRadius: 0 }}>
          <table className="custom-table">
            <thead>
              <tr>
                <th style={{ paddingLeft: '24px' }}>Scrip</th>
                <th>Balance</th>
                <th>Avg Cost</th>
                <th>LTP</th>
                <th>Total Cost</th>
                <th>Current Value</th>
                <th>Overall P/L</th>
                <th>Action Advice</th>
                <th style={{ paddingRight: '24px', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {portfolio.map((item) => {
                const s = item.stock_details;
                const change = item.overall_pl;
                const isItemProfit = change >= 0;
                
                const sig = item.active_signal;
                let rec = 'HOLD';
                let desc = 'Keep holding; trend is neutral';
                let badgeBg = 'rgba(245, 158, 11, 0.1)';
                let badgeText = 'var(--color-warning)';
                let badgeBorder = 'rgba(245, 158, 11, 0.2)';
                
                if (sig) {
                  rec = sig.recommendation;
                  if (rec === 'BUY') {
                    badgeBg = 'rgba(16, 185, 129, 0.1)';
                    badgeText = 'var(--color-success)';
                    badgeBorder = 'rgba(16, 185, 129, 0.2)';
                    desc = 'Bullish trigger: consider accumulating';
                  } else if (rec === 'SELL') {
                    badgeBg = 'rgba(239, 68, 68, 0.1)';
                    badgeText = 'var(--color-danger)';
                    badgeBorder = 'rgba(239, 68, 68, 0.2)';
                    desc = 'Bearish trigger: consider protecting capital';
                  } else if (sig.type === 'BULLISH_HOLD') {
                    desc = 'Stable uptrend; continue holding';
                  } else if (sig.type === 'BEARISH_HOLD') {
                    desc = 'Downtrending; do not buy more';
                  }
                }

                return (
                  <tr key={item.id}>
                    <td 
                      style={{ paddingLeft: '24px', fontWeight: '700', cursor: 'pointer' }}
                      onClick={() => navigate(`/stock/${s.symbol}`)}
                    >
                      {s.symbol}
                    </td>
                    <td>{item.balance}</td>
                    <td>Rs. {parseFloat(item.cost_price).toFixed(2)}</td>
                    <td style={{ fontWeight: '500' }}>Rs. {parseFloat(s.current_price).toFixed(2)}</td>
                    <td style={{ color: 'var(--text-secondary)' }}>Rs. {item.total_investment.toLocaleString([], { maximumFractionDigits: 2 })}</td>
                    <td>Rs. {item.current_value.toLocaleString([], { maximumFractionDigits: 2 })}</td>
                    <td className={isItemProfit ? 'trend-up' : 'trend-down'}>
                      Rs. {change.toLocaleString([], { maximumFractionDigits: 2 })} ({isItemProfit ? '+' : ''}{item.pl_percentage.toFixed(2)}%)
                    </td>
                    {/* Action Advice Badge */}
                    <td>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                        <span style={{
                          background: badgeBg,
                          color: badgeText,
                          border: `1px solid ${badgeBorder}`,
                          padding: '2px 8px',
                          borderRadius: '4px',
                          fontSize: '11px',
                          fontWeight: '700',
                          width: 'fit-content'
                        }}>
                          {rec}
                        </span>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                          {desc}
                        </span>
                        {sig && sig.take_profit && (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '4px' }}>
                            <div style={{ display: 'flex', gap: '8px', fontSize: '10px', fontWeight: '600' }}>
                              <span style={{ color: 'var(--color-success)' }}>TP: {sig.take_profit}</span>
                              <span style={{ color: 'var(--color-danger)' }}>
                                SL: {isItemProfit && sig.trailing_sl ? sig.trailing_sl : sig.stop_loss}
                              </span>
                            </div>
                            {isItemProfit && sig.trailing_sl && (
                              <span style={{ fontSize: '9px', color: 'var(--color-warning)', fontStyle: 'italic' }}>
                                (Trailing SL active to protect profits)
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    </td>
                    <td style={{ textAlign: 'right', paddingRight: '24px' }}>
                      <button 
                        onClick={() => handleRemoveItem(item.id)}
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
              {portfolio.length === 0 && (
                <tr>
                  <td colSpan="9" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                    No holdings in your portfolio yet. Click "Add Holding" to seed.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Holding Modal */}
      {isModalOpen && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          background: 'rgba(0,0,0,0.6)',
          backdropFilter: 'blur(4px)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div className="glass-card" style={{ maxWidth: '400px', width: '100%', border: '1px solid rgba(255,255,255,0.1)' }}>
            <h3 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '20px' }}>Add or Update Holding</h3>
            
            {modalError && (
              <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', color: 'var(--color-danger)', padding: '10px', borderRadius: '8px', fontSize: '13px', marginBottom: '16px' }}>
                {modalError}
              </div>
            )}

            {modalSuccess && (
              <div style={{ background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.2)', color: 'var(--color-success)', padding: '10px', borderRadius: '8px', fontSize: '13px', marginBottom: '16px' }}>
                {modalSuccess}
              </div>
            )}

            <form onSubmit={handleAddHolding}>
              <div className="input-group">
                <label>Select Scrip (Stock)</label>
                <select 
                  className="input-field" 
                  value={selectedStockId} 
                  onChange={(e) => setSelectedStockId(e.target.value)}
                  style={{ background: 'var(--bg-tertiary)' }}
                  required
                >
                  <option value="">-- Choose Stock --</option>
                  {stocks.map(s => (
                    <option key={s.id} value={s.id}>{s.symbol} - {s.name}</option>
                  ))}
                </select>
              </div>

              <div className="input-group">
                <label>Shares Quantity (Balance)</label>
                <input
                  type="number"
                  placeholder="e.g. 100"
                  className="input-field"
                  value={balance}
                  onChange={(e) => setBalance(e.target.value)}
                  required
                />
              </div>

              <div className="input-group" style={{ marginBottom: '28px' }}>
                <label>Average Cost Price (Rs.)</label>
                <input
                  type="text"
                  placeholder="e.g. 353.42"
                  className="input-field"
                  value={costPrice}
                  onChange={(e) => setCostPrice(e.target.value)}
                  required
                />
              </div>

              <div style={{ display: 'flex', gap: '12px' }}>
                <button type="button" onClick={() => setIsModalOpen(false)} className="btn-secondary" style={{ flexGrow: 1 }}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary" style={{ flexGrow: 1 }}>
                  Save
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
