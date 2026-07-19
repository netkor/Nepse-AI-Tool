import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import { 
  Search, Loader2, ArrowUpRight, ArrowDownRight, Compass, Radar, 
  TrendingUp, TrendingDown, Eye, Check, AlertTriangle, HelpCircle,
  Activity, Zap, BarChart2, Layers
} from 'lucide-react';

export default function Scanners() {
  const [signals, setSignals] = useState([]);
  const [customSignals, setCustomSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeScanner, setActiveScanner] = useState('GOLDEN_CROSS');
  const [search, setSearch] = useState('');
  const [minTurnover, setMinTurnover] = useState(5000000); // 50 Lakhs default
  const navigate = useNavigate();

  const fetchSignals = async () => {
    try {
      setLoading(true);
      setError('');
      const [response, customResponse] = await Promise.all([
        api.get(`/api/signals/?min_turnover=${minTurnover}`),
        api.get(`/api/signals/custom-strategy/?min_turnover=${minTurnover}`)
      ]);
      setSignals(response.data || []);
      setCustomSignals(customResponse.data || []);
    } catch (err) {
      setError('Failed to load screener data. Make sure the backend server is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSignals();
  }, [minTurnover]);

  // Filter signals based on selected active scanner preset
  const getMatchingStocks = () => {
    if (activeScanner === 'LOW_VOL_CROSS') {
      return customSignals.filter(sig => {
        if (!sig) return false;
        return sig.symbol.toLowerCase().includes(search.toLowerCase()) ||
               sig.name.toLowerCase().includes(search.toLowerCase());
      });
    }

    return signals.filter(sig => {
      if (!sig) return false;

      // Search filter
      const matchesSearch = sig.symbol.toLowerCase().includes(search.toLowerCase()) ||
                            sig.name.toLowerCase().includes(search.toLowerCase());
      if (!matchesSearch) return false;

      // Preset Scanner Filter conditions
      switch (activeScanner) {
        case 'GOLDEN_CROSS':
          return sig.price_action === 'BUY' && 
                 sig.signals_list.some(s => s.label.includes('Golden'));
                 
        case 'RSI_OVERSOLD':
          return sig.mean_reversion === 'BUY' || (sig.rsi_value !== null && sig.rsi_value <= 30);
          
        case 'BULLISH_DIVG':
          return sig.divergence === 'BUY';
          
        case 'DOW_BUY':
          return sig.dow === 'BUY';
          
        case 'VOLUME_BREAKOUT':
          return sig.price_action === 'BUY' && 
                 sig.signals_list.some(s => s.label.includes('Volume'));
                 
        case 'DEATH_CROSS':
          return sig.price_action === 'SELL' && 
                 sig.signals_list.some(s => s.label.includes('Death'));
                 
        case 'RSI_OVERBOUGHT':
          return sig.mean_reversion === 'SELL' || (sig.rsi_value !== null && sig.rsi_value >= 70);
          
        default:
          return false;
      }
    });
  };

  const matches = getMatchingStocks();

  // Preset definitions for rendering card grid
  const scannerPresets = [
    {
      id: 'GOLDEN_CROSS',
      title: 'Golden Cross Crossover',
      icon: <Zap size={22} color="var(--color-success)" />,
      desc: 'Short term MA crossed above long term MA. Start of macro uptrend.',
      badgeText: 'Bullish Crossover',
      badgeColor: 'var(--color-success)',
      badgeBg: 'rgba(16, 185, 129, 0.1)'
    },
    {
      id: 'LOW_VOL_CROSS',
      title: 'Low-Vol EMA Cross (Exit / SL)',
      icon: <Layers size={22} color="#8b5cf6" />,
      desc: '9 EMA down-cross 18 EMA with volume trading below 20-day HMA.',
      badgeText: 'Custom Strategy',
      badgeColor: '#8b5cf6',
      badgeBg: 'rgba(139, 92, 246, 0.1)'
    },
    {
      id: 'RSI_OVERSOLD',
      title: 'RSI Oversold Bottom',
      icon: <TrendingUp size={22} color="#10b981" />,
      desc: '14-day RSI dropped below 30. High probability of price rebound.',
      badgeText: 'Mean Reversion Buy',
      badgeColor: '#10b981',
      badgeBg: 'rgba(16, 185, 129, 0.1)'
    },
    {
      id: 'BULLISH_DIVG',
      title: 'Bullish RSI Divergence',
      icon: <Radar size={22} color="#6366f1" />,
      desc: 'Price forms lower low, but RSI forms higher low. Trend reversal signal.',
      badgeText: 'Divergence Alert',
      badgeColor: '#6366f1',
      badgeBg: 'rgba(99, 102, 241, 0.1)'
    },
    {
      id: 'DOW_BUY',
      title: 'Dow Theory Uptrend',
      icon: <Activity size={22} color="#f59e0b" />,
      desc: 'Price forming series of higher highs and higher lows. Strong momentum.',
      badgeText: 'Dow Buy',
      badgeColor: '#f59e0b',
      badgeBg: 'rgba(245, 158, 11, 0.1)'
    },
    {
      id: 'VOLUME_BREAKOUT',
      title: 'Volume Spike Breakout',
      icon: <Layers size={22} color="#ec4899" />,
      desc: 'Traded volume is > 2.5x higher than average with positive returns.',
      badgeText: 'Price Action Buy',
      badgeColor: '#ec4899',
      badgeBg: 'rgba(236, 72, 153, 0.1)'
    },
    {
      id: 'DEATH_CROSS',
      title: 'Death Cross Warning',
      icon: <AlertTriangle size={22} color="var(--color-danger)" />,
      desc: 'Short term MA crossed below long term MA. Start of macro downtrend.',
      badgeText: 'Bearish Crossover',
      badgeColor: 'var(--color-danger)',
      badgeBg: 'rgba(239, 68, 68, 0.1)'
    },
    {
      id: 'RSI_OVERBOUGHT',
      title: 'RSI Overbought High',
      icon: <TrendingDown size={22} color="#ef4444" />,
      desc: '14-day RSI rose above 70. Momentum stretched, correction probable.',
      badgeText: 'Mean Reversion Sell',
      badgeColor: '#ef4444',
      badgeBg: 'rgba(239, 68, 68, 0.1)'
    }
  ];

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
        <Loader2 className="animate-spin" size={48} color="var(--accent-primary)" />
      </div>
    );
  }

  const activePresetInfo = scannerPresets.find(p => p.id === activeScanner);

  return (
    <div className="main-content">
      {/* Page Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '28px' }}>
        <div>
          <h1 className="page-title">Technical Screener</h1>
          <p className="page-subtitle">Scan the entire NEPSE market for professional trade signals & setups</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <label style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-secondary)' }}>Min 20-Day Avg Turnover</label>
            <select 
              value={minTurnover} 
              onChange={(e) => {
                setMinTurnover(Number(e.target.value));
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
              <option value={0} style={{ color: 'black' }}>No Filter (All Stocks)</option>
              <option value={1000000} style={{ color: 'black' }}>10 Lakhs</option>
              <option value={5000000} style={{ color: 'black' }}>50 Lakhs (Default)</option>
              <option value={10000000} style={{ color: 'black' }}>1 Crore</option>
              <option value={50000000} style={{ color: 'black' }}>5 Crores</option>
            </select>
          </div>
          <button 
            onClick={fetchSignals} 
            className="btn-secondary" 
            style={{ width: 'auto', display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 16px', alignSelf: 'flex-end', height: '37px' }}
          >
            <Compass size={16} /> Re-Scan Market
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

      {/* Grid of Preset Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '16px',
        marginBottom: '40px'
      }}>
        {scannerPresets.map((preset) => {
          const isActive = activeScanner === preset.id;
          const presetMatchesCount = preset.id === 'LOW_VOL_CROSS' 
            ? customSignals.length 
            : signals.filter(sig => {
                if (preset.id === 'GOLDEN_CROSS') {
                  return sig.price_action === 'BUY' && sig.signals_list.some(s => s.label.includes('Golden'));
                }
                if (preset.id === 'RSI_OVERSOLD') {
                  return sig.mean_reversion === 'BUY' || (sig.rsi_value !== null && sig.rsi_value <= 30);
                }
                if (preset.id === 'BULLISH_DIVG') {
                  return sig.divergence === 'BUY';
                }
                if (preset.id === 'DOW_BUY') {
                  return sig.dow === 'BUY';
                }
                if (preset.id === 'VOLUME_BREAKOUT') {
                  return sig.price_action === 'BUY' && sig.signals_list.some(s => s.label.includes('Volume'));
                }
                if (preset.id === 'DEATH_CROSS') {
                  return sig.price_action === 'SELL' && sig.signals_list.some(s => s.label.includes('Death'));
                }
                if (preset.id === 'RSI_OVERBOUGHT') {
                  return sig.mean_reversion === 'SELL' || (sig.rsi_value !== null && sig.rsi_value >= 70);
                }
                return false;
              }).length;

          return (
            <div 
              key={preset.id}
              onClick={() => setActiveScanner(preset.id)}
              className="glass-card"
              style={{
                padding: '20px',
                cursor: 'pointer',
                border: isActive ? `1.5px solid var(--accent-primary)` : '1px solid var(--border-standard)',
                background: isActive ? 'rgba(99, 102, 241, 0.04)' : 'rgba(255, 255, 255, 0.01)',
                transition: 'all 0.2s ease',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                height: '100%',
                position: 'relative'
              }}
              onMouseEnter={(e) => {
                if (!isActive) e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)';
              }}
              onMouseLeave={(e) => {
                if (!isActive) e.currentTarget.style.borderColor = 'var(--border-standard)';
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  {preset.icon}
                  <span style={{
                    background: preset.badgeBg,
                    color: preset.badgeColor,
                    fontSize: '11px',
                    fontWeight: '700',
                    padding: '3px 8px',
                    borderRadius: '4px',
                    textTransform: 'uppercase'
                  }}>
                    {preset.badgeText}
                  </span>
                </div>
                
                <h4 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '6px', color: isActive ? 'white' : 'rgba(255,255,255,0.9)' }}>
                  {preset.title}
                </h4>
                
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.4', marginBottom: '16px' }}>
                  {preset.desc}
                </p>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid rgba(255,255,255,0.03)', paddingTop: '10px' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: '600' }}>ACTIVE SCANS</span>
                <span style={{
                  fontSize: '15px',
                  fontWeight: '800',
                  color: presetMatchesCount > 0 ? preset.badgeColor : 'var(--text-muted)'
                }}>
                  {presetMatchesCount} {presetMatchesCount === 1 ? 'stock' : 'stocks'}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Screener Results Area */}
      <div className="glass-card" style={{ padding: '24px 0' }}>
        
        {/* Results Toolbar */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '0 24px 20px 24px',
          borderBottom: '1px solid var(--border-standard)',
          flexWrap: 'wrap',
          gap: '16px'
        }}>
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Radar size={18} color="var(--accent-primary)" />
              {activePresetInfo?.title} Matches ({matches.length})
            </h3>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
              {activePresetInfo?.desc}
            </p>
          </div>

          {/* Search match input */}
          <div style={{ position: 'relative', maxWidth: '300px', width: '100%' }}>
            <Search size={16} color="var(--text-secondary)" style={{
              position: 'absolute',
              left: '12px',
              top: '50%',
              transform: 'translateY(-50%)'
            }} />
            <input
              type="text"
              placeholder="Search matches..."
              className="input-field"
              style={{ paddingLeft: '36px', paddingTop: '6px', paddingBottom: '6px', fontSize: '13px' }}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>

        {/* Results Matches Table */}
        <div className="table-container" style={{ border: 'none', borderRadius: 0 }}>
          {activeScanner === 'LOW_VOL_CROSS' ? (
            <table className="custom-table">
              <thead>
                <tr>
                  <th style={{ paddingLeft: '24px' }}>Symbol</th>
                  <th>Company Name</th>
                  <th>Price (LTP)</th>
                  <th>Volume / HMA 20</th>
                  <th style={{ textAlign: 'center' }}>Quarterly Fundamental Trends (EPS / ROE / Net Profit)</th>
                  <th>Financial Verdict</th>
                  <th>Exit Target Profit (TP)</th>
                  <th>Exit Stop Loss (SL)</th>
                  <th style={{ paddingRight: '24px', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {matches.map((sig) => {
                  const hasUpward = sig.eps_trend === 'Upward' && sig.roe_trend === 'Upward' && sig.net_profit_trend === 'Upward';
                  const hasDownward = sig.eps_trend === 'Downward' || sig.roe_trend === 'Downward' || sig.net_profit_trend === 'Downward';

                  return (
                    <tr key={sig.symbol}>
                      <td style={{ paddingLeft: '24px', fontWeight: '700' }}>
                        {sig.symbol}
                        {sig.event_annotation && (
                          <div style={{ fontSize: '10px', color: '#f59e0b', marginTop: '2px', fontWeight: '600', whiteSpace: 'nowrap' }}>
                            📅 {sig.event_annotation}
                          </div>
                        )}
                      </td>
                      <td style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>{sig.name}</td>
                      <td style={{ fontWeight: '600' }}>Rs. {parseFloat(sig.price).toFixed(2)}</td>
                      <td style={{ fontSize: '13px' }}>
                        <span style={{ fontWeight: '600' }}>{sig.volume.toLocaleString()}</span>
                        <span style={{ color: 'var(--text-muted)', fontSize: '11px', marginLeft: '4px' }}>
                          (HMA: {sig.vol_hma20.toLocaleString()})
                        </span>
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <div style={{ display: 'flex', gap: '6px', justifyContent: 'center' }}>
                          <span style={{
                            background: sig.eps_trend === 'Upward' ? 'rgba(16, 185, 129, 0.1)' : sig.eps_trend === 'Downward' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(255, 255, 255, 0.05)',
                            color: sig.eps_trend === 'Upward' ? 'var(--color-success)' : sig.eps_trend === 'Downward' ? 'var(--color-danger)' : 'var(--text-secondary)',
                            padding: '3px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: '700'
                          }}>
                            EPS: {sig.eps_trend}
                          </span>
                          <span style={{
                            background: sig.roe_trend === 'Upward' ? 'rgba(16, 185, 129, 0.1)' : sig.roe_trend === 'Downward' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(255, 255, 255, 0.05)',
                            color: sig.roe_trend === 'Upward' ? 'var(--color-success)' : sig.roe_trend === 'Downward' ? 'var(--color-danger)' : 'var(--text-secondary)',
                            padding: '3px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: '700'
                          }}>
                            ROE: {sig.roe_trend}
                          </span>
                          <span style={{
                            background: sig.net_profit_trend === 'Upward' ? 'rgba(16, 185, 129, 0.1)' : sig.net_profit_trend === 'Downward' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(255, 255, 255, 0.05)',
                            color: sig.net_profit_trend === 'Upward' ? 'var(--color-success)' : sig.net_profit_trend === 'Downward' ? 'var(--color-danger)' : 'var(--text-secondary)',
                            padding: '3px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: '700'
                          }}>
                            Profit: {sig.net_profit_trend}
                          </span>
                        </div>
                      </td>
                      <td>
                        <span style={{
                          color: hasUpward ? 'var(--color-success)' : hasDownward ? 'var(--color-danger)' : 'var(--text-secondary)',
                          fontSize: '12px',
                          fontWeight: '700'
                        }}>
                          {sig.fundamental_verdict}
                        </span>
                      </td>
                      <td style={{ color: 'var(--color-success)', fontWeight: '600' }}>Rs. {sig.tp_level.toFixed(2)}</td>
                      <td style={{ color: 'var(--color-danger)', fontWeight: '600' }}>Rs. {sig.sl_level.toFixed(2)}</td>
                      <td style={{ paddingRight: '24px', textAlign: 'right' }}>
                        <button 
                          onClick={() => navigate(`/stock/${sig.symbol}`)}
                          className="btn-secondary" 
                          style={{
                            width: 'auto', padding: '6px 12px', fontSize: '12px',
                            display: 'inline-flex', alignItems: 'center', gap: '6px', borderRadius: '6px'
                          }}
                        >
                          <Eye size={13} /> Analyze Chart
                        </button>
                      </td>
                    </tr>
                  );
                })}
                {matches.length === 0 && (
                  <tr>
                    <td colSpan="9" style={{ textAlign: 'center', padding: '48px', color: 'var(--text-muted)', fontSize: '14px' }}>
                      No stocks currently match the custom crossover strategy.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          ) : (
            <table className="custom-table">
              <thead>
                <tr>
                  <th style={{ paddingLeft: '24px' }}>Symbol</th>
                  <th>Company Name</th>
                  <th>Price (LTP)</th>
                  <th>Change %</th>
                  <th>RSI (14-day)</th>
                  <th>Specific Alert Description</th>
                  <th style={{ paddingRight: '24px', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {matches.map((sig) => {
                  const change = parseFloat(sig.change_percentage);
                  const isUp = change >= 0;
                  
                  let specificDesc = sig.signal_desc;
                  const matchingAlertObj = sig.signals_list ? sig.signals_list.find(s => {
                    if (activeScanner === 'GOLDEN_CROSS' || activeScanner === 'VOLUME_BREAKOUT') return s.category === 'PRICE_ACTION';
                    if (activeScanner === 'RSI_OVERSOLD' || activeScanner === 'RSI_OVERBOUGHT') return s.category === 'MEAN_REVERSION';
                    if (activeScanner === 'BULLISH_DIVG') return s.category === 'DIVERGENCE';
                    if (activeScanner === 'DOW_BUY') return s.category === 'DOW';
                    return false;
                  }) : null;
                  if (matchingAlertObj) {
                    specificDesc = matchingAlertObj.desc;
                  }

                  let rsiBg = 'rgba(255, 255, 255, 0.05)';
                  let rsiText = 'var(--text-secondary)';
                  if (sig.rsi_value !== null && sig.rsi_value !== undefined) {
                    if (sig.rsi_value <= 30) {
                      rsiBg = 'rgba(16, 185, 129, 0.15)';
                      rsiText = 'var(--color-success)';
                    } else if (sig.rsi_value >= 70) {
                      rsiBg = 'rgba(239, 68, 68, 0.15)';
                      rsiText = 'var(--color-danger)';
                    }
                  }

                  return (
                    <tr key={sig.symbol}>
                      <td style={{ paddingLeft: '24px', fontWeight: '700' }}>
                        {sig.symbol}
                        {sig.event_annotation && (
                          <div style={{ fontSize: '10px', color: '#f59e0b', marginTop: '2px', fontWeight: '600', whiteSpace: 'nowrap' }}>
                            📅 {sig.event_annotation}
                          </div>
                        )}
                      </td>
                      <td style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>{sig.name}</td>
                      <td style={{ fontWeight: '600' }}>Rs. {parseFloat(sig.price).toFixed(2)}</td>
                      <td className={isUp ? 'trend-up' : 'trend-down'} style={{ fontSize: '13px', fontWeight: '600' }}>
                        {isUp ? '+' : ''}{change.toFixed(2)}%
                      </td>
                      <td>
                        <span style={{
                          background: rsiBg,
                          color: rsiText,
                          padding: '3px 8px',
                          borderRadius: '4px',
                          fontSize: '11px',
                          fontWeight: '700'
                        }}>
                          {sig.rsi_value !== null && sig.rsi_value !== undefined ? sig.rsi_value : 'N/A'}
                        </span>
                      </td>
                      <td style={{ color: 'var(--text-secondary)', fontSize: '13px', maxWidth: '350px', lineHeight: '1.4' }}>
                        {specificDesc}
                      </td>
                      <td style={{ paddingRight: '24px', textAlign: 'right' }}>
                        <button 
                          onClick={() => navigate(`/stock/${sig.symbol}`)}
                          className="btn-secondary" 
                          style={{
                            width: 'auto', padding: '6px 12px', fontSize: '12px',
                            display: 'inline-flex', alignItems: 'center', gap: '6px', borderRadius: '6px'
                          }}
                        >
                          <Eye size={13} /> Analyze Chart
                        </button>
                      </td>
                    </tr>
                  );
                })}
                {matches.length === 0 && (
                  <tr>
                    <td colSpan="7" style={{ textAlign: 'center', padding: '48px', color: 'var(--text-muted)', fontSize: '14px' }}>
                      No stocks currently match the "{activePresetInfo?.title}" scan criteria.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
