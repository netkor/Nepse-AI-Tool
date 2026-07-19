import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api';
import { 
  AreaChart, Area, Line, BarChart, Bar, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid 
} from 'recharts';
import { 
  Loader2, ArrowLeft, Plus, Check, Bell, TrendingUp, TrendingDown, Eye, Info, AlertTriangle, Calendar 
} from 'lucide-react';

export default function StockDetail() {
  const { symbol } = useParams();
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);
  const [stockInfo, setStockInfo] = useState(null);
  const [stockSignal, setStockSignal] = useState(null);
  const [seasonal, setSeasonal] = useState([]);
  const [timeframe, setTimeframe] = useState('3M'); // 1M, 3M, 6M, 1Y, ALL
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Watchlist & Alert state
  const [inWatchlist, setInWatchlist] = useState(false);
  const [watchlistId, setWatchlistId] = useState(null);
  const [alertType, setAlertType] = useState('PRICE_ABOVE');
  const [alertValue, setAlertValue] = useState('');
  const [alertSuccess, setAlertSuccess] = useState('');
  const [alertError, setAlertError] = useState('');
  
  // Calculator state
  const [investmentAmount, setInvestmentAmount] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError('');

        // 1. Fetch History WITH Indicators
        const historyResponse = await api.get(`/api/signals/${symbol}/`);
        setHistory(historyResponse.data);

        // 2. Fetch Stock Symbol Info
        const stocksResponse = await api.get('/api/stocks/');
        const currentStock = stocksResponse.data.find(s => s.symbol === symbol);
        setStockInfo(currentStock);

        // 3. Fetch recommendation for advice banner
        const signalsResponse = await api.get('/api/signals/');
        const currentSignal = signalsResponse.data.find(s => s.symbol === symbol);
        setStockSignal(currentSignal);

        // 4. Fetch Seasonal monthly averages
        const seasonalResponse = await api.get(`/api/signals/seasonal/${symbol}/`);
        setSeasonal(seasonalResponse.data);

        // 5. Fetch Watchlist to check status
        const watchlistResponse = await api.get('/api/watchlist/');
        const watchEntry = watchlistResponse.data.find(w => w.stock_details.symbol === symbol);
        if (watchEntry) {
          setInWatchlist(true);
          setWatchlistId(watchEntry.id);
        }
      } catch (err) {
        setError('Failed to fetch details for ' + symbol);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [symbol]);

  const getFilteredHistory = () => {
    if (!history.length) return [];
    
    const cutoffDate = new Date();
    if (timeframe === '1M') cutoffDate.setMonth(cutoffDate.getMonth() - 1);
    else if (timeframe === '3M') cutoffDate.setMonth(cutoffDate.getMonth() - 3);
    else if (timeframe === '6M') cutoffDate.setMonth(cutoffDate.getMonth() - 6);
    else if (timeframe === '1Y') cutoffDate.setFullYear(cutoffDate.getFullYear() - 1);
    else return history;

    return history.filter(item => new Date(item.date) >= cutoffDate);
  };

  const chartData = getFilteredHistory().map(item => ({
    date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' }),
    price: parseFloat(item.close),
    sma20: item.sma20 ? parseFloat(item.sma20) : null,
    sma50: item.sma50 ? parseFloat(item.sma50) : null,
    volume: parseInt(item.volume)
  }));

  const toggleWatchlist = async () => {
    try {
      if (inWatchlist) {
        await api.delete(`/api/watchlist/${symbol}/`);
        setInWatchlist(false);
        setWatchlistId(null);
      } else {
        const response = await api.post('/api/watchlist/', { stock: stockInfo.id });
        setInWatchlist(true);
        setWatchlistId(response.data.id);
      }
    } catch (err) {
      console.error('Watchlist toggle error', err);
    }
  };

  const handleCreateAlert = async (e) => {
    e.preventDefault();
    setAlertSuccess('');
    setAlertError('');

    if (!alertValue || isNaN(parseFloat(alertValue))) {
      setAlertError('Please enter a valid numeric value');
      return;
    }

    try {
      await api.post('/api/alerts/', {
        stock: stockInfo.id,
        alert_type: alertType,
        target_value: parseFloat(alertValue)
      });
      setAlertSuccess(`Alert successfully configured for ${symbol}!`);
      setAlertValue('');
    } catch (err) {
      setAlertError('Failed to configure alert. Please verify your fields.');
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
        <Loader2 className="animate-spin" size={48} color="var(--accent-primary)" />
      </div>
    );
  }

  if (error || !stockInfo) {
    return (
      <div className="main-content">
        <button onClick={() => navigate('/')} className="btn-secondary" style={{ marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ArrowLeft size={16} /> Back to Dashboard
        </button>
        <div style={{ background: 'rgba(239, 68, 68, 0.1)', color: 'var(--color-danger)', padding: '16px', borderRadius: '8px' }}>
          {error || 'Stock info could not be retrieved.'}
        </div>
      </div>
    );
  }

  const latestPrice = parseFloat(stockInfo.current_price);
  const changeVal = parseFloat(stockInfo.change_percentage);
  const isUp = changeVal >= 0;

  const strokeColor = isUp ? 'var(--color-success)' : 'var(--color-danger)';
  const fillColor = isUp ? 'rgba(16, 185, 129, 0.05)' : 'rgba(239, 68, 68, 0.05)';

  const latestData = history.length > 0 ? history[history.length - 1] : null;
  const sma20Val = latestData && latestData.sma20 ? parseFloat(latestData.sma20).toFixed(2) : 'N/A';
  const sma50Val = latestData && latestData.sma50 ? parseFloat(latestData.sma50).toFixed(2) : 'N/A';

  // Format Recommendation Advice card styles
  let recLabel = 'HOLD';
  let recDesc = 'Trend is neutral. Await stronger momentum triggers.';
  let recColor = 'var(--color-warning)';
  let recBg = 'rgba(245, 158, 11, 0.05)';
  let recBorder = 'rgba(245, 158, 11, 0.15)';

  if (stockSignal) {
    recLabel = stockSignal.recommendation;
    recDesc = stockSignal.signal_desc;
    if (recLabel === 'BUY') {
      recColor = 'var(--color-success)';
      recBg = 'rgba(16, 185, 129, 0.05)';
      recBorder = 'rgba(16, 185, 129, 0.15)';
    } else if (recLabel === 'SELL') {
      recColor = 'var(--color-danger)';
      recBg = 'rgba(239, 68, 68, 0.05)';
      recBorder = 'rgba(239, 68, 68, 0.15)';
    }
  }

  return (
    <div className="main-content">
      {/* Back button and Watchlist control */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <button onClick={() => navigate('/')} className="btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ArrowLeft size={16} /> Back to Dashboard
        </button>

        <button 
          onClick={toggleWatchlist} 
          className="btn-secondary"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            borderColor: inWatchlist ? 'var(--color-success)' : 'var(--border-standard)',
            color: inWatchlist ? 'var(--color-success)' : 'var(--text-secondary)'
          }}
        >
          {inWatchlist ? (
            <>
              <Check size={16} /> In Watchlist
            </>
          ) : (
            <>
              <Plus size={16} /> Add to Watchlist
            </>
          )}
        </button>
      </div>

      {/* Header Info */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px', flexWrap: 'wrap', gap: '20px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '6px' }}>
            <h1 style={{ fontSize: '36px', fontWeight: '700' }}>{stockInfo.symbol}</h1>
            <span style={{
              background: 'var(--bg-tertiary)',
              padding: '4px 10px',
              borderRadius: '6px',
              fontSize: '14px',
              color: 'var(--text-secondary)',
              border: '1px solid var(--border-standard)'
            }}>
              EQ
            </span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '18px' }}>{stockInfo.name}</p>
        </div>

        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '32px', fontWeight: '700', marginBottom: '4px' }}>
            Rs. {latestPrice.toFixed(2)}
          </div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            gap: '6px',
            fontSize: '16px',
            color: isUp ? 'var(--color-success)' : 'var(--color-danger)'
          }}>
            {isUp ? <TrendingUp size={18} /> : <TrendingDown size={18} />}
            <span>{isUp ? '+' : ''}{changeVal.toFixed(2)}%</span>
          </div>
        </div>
      </div>

      {/* Action Recommendation Banner */}
      <div style={{
        background: recBg,
        border: `1px solid ${recBorder}`,
        borderLeft: `5px solid ${recColor}`,
        padding: '20px',
        borderRadius: '12px',
        marginBottom: '32px',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '16px'
      }}>
        <div style={{
          background: recColor,
          padding: '6px 12px',
          borderRadius: '6px',
          color: recColor === 'var(--color-warning)' ? '#1e1b4b' : 'white',
          fontWeight: '800',
          fontSize: '13px',
          marginTop: '2px'
        }}>
          {recLabel}
        </div>
        <div>
          <h4 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '6px' }}>
            {stockSignal ? stockSignal.signal_label : 'Analysing Trend'}
          </h4>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', lineHeight: '1.5' }}>
            {recDesc}
          </p>
          {stockSignal && stockSignal.take_profit && stockSignal.stop_loss && (
            <div style={{ marginTop: '12px', display: 'flex', gap: '16px' }}>
              <div style={{ background: 'var(--surface-color)', border: '1px solid var(--border-color)', padding: '8px 16px', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ color: 'var(--text-secondary)', fontSize: '12px', textTransform: 'uppercase', fontWeight: '700' }}>Target:</span>
                <span style={{ color: 'var(--color-success)', fontSize: '16px', fontWeight: '800' }}>Rs. {stockSignal.take_profit}</span>
              </div>
              <div style={{ background: 'var(--surface-color)', border: '1px solid var(--border-color)', padding: '8px 16px', borderRadius: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ color: 'var(--text-secondary)', fontSize: '12px', textTransform: 'uppercase', fontWeight: '700' }}>Stop Loss:</span>
                <span style={{ color: 'var(--color-danger)', fontSize: '16px', fontWeight: '800' }}>Rs. {stockSignal.stop_loss}</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Risk / Reward Calculator */}
      {stockSignal && stockSignal.take_profit && stockSignal.stop_loss && (
        <div className="glass-card" style={{ padding: '24px', marginBottom: '32px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <TrendingUp size={20} color="var(--accent-primary)" /> 1-Click Risk/Reward Calculator
          </h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '16px' }}>
            Enter your planned investment amount below to see exactly how much capital you are risking at the Stop Loss level, and how much you will profit at the Target level.
          </p>
          <div style={{ display: 'flex', gap: '16px', alignItems: 'flex-start', flexWrap: 'wrap' }}>
            <div style={{ flex: '1', minWidth: '250px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '8px', textTransform: 'uppercase' }}>
                Planned Investment (Rs.)
              </label>
              <input 
                type="number"
                className="input-field"
                placeholder="e.g. 50000"
                value={investmentAmount}
                onChange={(e) => setInvestmentAmount(e.target.value)}
              />
            </div>
            
            {investmentAmount > 0 && stockInfo && (
              <div style={{ flex: '2', display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                <div style={{ flex: '1', background: 'rgba(239, 68, 68, 0.05)', border: '1px solid rgba(239, 68, 68, 0.2)', padding: '16px', borderRadius: '12px' }}>
                  <span style={{ display: 'block', color: 'var(--text-secondary)', fontSize: '12px', fontWeight: '600', marginBottom: '4px' }}>Maximum Risk (At SL)</span>
                  <span style={{ display: 'block', color: 'var(--color-danger)', fontSize: '20px', fontWeight: '800' }}>
                    Rs. {(((stockInfo.current_price - stockSignal.stop_loss) / stockInfo.current_price) * investmentAmount).toFixed(2)}
                  </span>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>If price drops to Rs. {stockSignal.stop_loss}</span>
                </div>
                
                <div style={{ flex: '1', background: 'rgba(16, 185, 129, 0.05)', border: '1px solid rgba(16, 185, 129, 0.2)', padding: '16px', borderRadius: '12px' }}>
                  <span style={{ display: 'block', color: 'var(--text-secondary)', fontSize: '12px', fontWeight: '600', marginBottom: '4px' }}>Target Profit (At TP)</span>
                  <span style={{ display: 'block', color: 'var(--color-success)', fontSize: '20px', fontWeight: '800' }}>
                    Rs. {(((stockSignal.take_profit - stockInfo.current_price) / stockInfo.current_price) * investmentAmount).toFixed(2)}
                  </span>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>If price hits Rs. {stockSignal.take_profit}</span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Main Grid: Chart and Alert Setup */}
      <div style={{ display: 'grid', gridTemplateColumns: '3fr 1fr', gap: '32px', alignItems: 'start', flexWrap: 'wrap', marginBottom: '32px' }}>
        
        {/* Left Column: Chart Card */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
            <div>
              <h3 style={{ fontSize: '18px', fontWeight: '600' }}>Price with Moving Averages</h3>
              <div style={{ display: 'flex', gap: '12px', marginTop: '6px', fontSize: '12px' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: strokeColor }}></span>
                  Price (LTP)
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#f59e0b' }}></span>
                  20 SMA
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#6366f1' }}></span>
                  50 SMA
                </span>
              </div>
            </div>
            
            <div style={{ display: 'flex', gap: '8px', background: 'var(--bg-tertiary)', padding: '4px', borderRadius: '8px' }}>
              {['1M', '3M', '6M', '1Y', 'ALL'].map((tf) => (
                <button
                  key={tf}
                  onClick={() => setTimeframe(tf)}
                  style={{
                    padding: '6px 12px',
                    borderRadius: '6px',
                    border: 'none',
                    background: timeframe === tf ? 'var(--accent-primary)' : 'transparent',
                    color: timeframe === tf ? 'white' : 'var(--text-secondary)',
                    fontWeight: timeframe === tf ? '600' : '400',
                    cursor: 'pointer',
                    fontSize: '13px',
                    transition: 'all 0.15s ease'
                  }}
                >
                  {tf}
                </button>
              ))}
            </div>
          </div>

          <div style={{ width: '100%', height: '380px', marginBottom: '16px' }}>
            {chartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={strokeColor} stopOpacity={0.1}/>
                      <stop offset="95%" stopColor={strokeColor} stopOpacity={0.0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                  <XAxis 
                    dataKey="date" 
                    stroke="var(--text-muted)" 
                    fontSize={11} 
                    tickLine={false} 
                    dy={10}
                  />
                  <YAxis 
                    stroke="var(--text-muted)" 
                    fontSize={11} 
                    tickLine={false}
                    domain={['auto', 'auto']}
                    dx={-5}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      background: 'var(--bg-secondary)', 
                      borderColor: 'var(--border-standard)',
                      borderRadius: '8px',
                      color: 'white',
                      boxShadow: '0 4px 12px rgba(0,0,0,0.5)'
                    }} 
                  />
                  <Area 
                    type="monotone" 
                    dataKey="price" 
                    stroke={strokeColor} 
                    strokeWidth={2}
                    fillOpacity={1} 
                    fill="url(#colorPrice)" 
                  />
                  <Line 
                    type="monotone" 
                    dataKey="sma20" 
                    stroke="#f59e0b" 
                    strokeWidth={1.5} 
                    dot={false}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="sma50" 
                    stroke="#6366f1" 
                    strokeWidth={1.5} 
                    dot={false}
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', color: 'var(--text-muted)' }}>
                No historical records available for this timeframe.
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Alert Creator / Info */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Quick Metrics Card */}
          <div className="glass-card">
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px' }}>Technical Metrics</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-standard)', paddingBottom: '8px' }}>
                <span style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
                  20-day SMA
                </span>
                <span style={{ fontWeight: '600', color: '#f59e0b' }}>Rs. {sma20Val}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-standard)', paddingBottom: '8px' }}>
                <span style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>
                  50-day SMA
                </span>
                <span style={{ fontWeight: '600', color: '#6366f1' }}>Rs. {sma50Val}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-standard)', paddingBottom: '8px' }}>
                <span style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>Volume Traded</span>
                <span style={{ fontWeight: '600' }}>{parseInt(stockInfo.volume).toLocaleString()}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-standard)', paddingBottom: '8px' }}>
                <span style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>Last Updated</span>
                <span style={{ fontWeight: '500', fontSize: '13px' }}>
                  {new Date(stockInfo.last_updated).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            </div>
          </div>

          {/* Upcoming Events Card */}
          {stockSignal && stockSignal.upcoming_events && stockSignal.upcoming_events.length > 0 && (
            <div className="glass-card">
              <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Calendar size={18} color="#f59e0b" /> Upcoming Events
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {stockSignal.upcoming_events.map((ev, idx) => (
                  <div key={idx} style={{ 
                    display: 'flex', flexDirection: 'column', gap: '4px',
                    borderLeft: '3px solid #f59e0b',
                    paddingLeft: '12px',
                    background: 'rgba(245, 158, 11, 0.05)',
                    padding: '10px 12px',
                    borderRadius: '0 6px 6px 0'
                  }}>
                    <span style={{ fontSize: '11px', color: '#f59e0b', fontWeight: '700', textTransform: 'uppercase' }}>{ev.type}</span>
                    <span style={{ fontSize: '14px', fontWeight: '600', color: 'white' }}>{ev.title}</span>
                    <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Date: {ev.date} ({ev.days_away} days away)</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Trigger Alert Card */}
          <div className="glass-card">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
              <Bell size={18} color="var(--accent-primary)" />
              <h3 style={{ fontSize: '16px', fontWeight: '600' }}>Set Price Alert</h3>
            </div>

            {alertSuccess && (
              <div style={{
                background: 'rgba(16, 185, 129, 0.1)',
                border: '1px solid rgba(16, 185, 129, 0.2)',
                color: 'var(--color-success)',
                padding: '10px',
                borderRadius: '8px',
                fontSize: '13px',
                marginBottom: '16px'
              }}>
                {alertSuccess}
              </div>
            )}

            {alertError && (
              <div style={{
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.2)',
                color: 'var(--color-danger)',
                padding: '10px',
                borderRadius: '8px',
                fontSize: '13px',
                marginBottom: '16px'
              }}>
                {alertError}
              </div>
            )}

            <form onSubmit={handleCreateAlert}>
              <div className="input-group">
                <label>Trigger Type</label>
                <select 
                  className="input-field" 
                  value={alertType} 
                  onChange={(e) => setAlertType(e.target.value)}
                  style={{ background: 'var(--bg-tertiary)', fontSize: '14px' }}
                >
                  <option value="PRICE_ABOVE">Price Rises Above (Rs)</option>
                  <option value="PRICE_BELOW">Price Drops Below (Rs)</option>
                </select>
              </div>

              <div className="input-group" style={{ marginBottom: '20px' }}>
                <label>Threshold Value</label>
                <input
                  type="text"
                  placeholder="e.g. 550.00"
                  className="input-field"
                  value={alertValue}
                  onChange={(e) => setAlertValue(e.target.value)}
                />
              </div>

              <button type="submit" className="btn-primary" style={{ padding: '10px', fontSize: '14px' }}>
                Set Trigger
              </button>
            </form>
          </div>

        </div>

      </div>

      {/* 4. Seasonal month-wise returns BarChart at Bottom */}
      {seasonal.length > 0 && (
        <div className="glass-card" style={{ padding: '24px', marginBottom: '32px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '20px' }}>
            <Calendar size={20} color="var(--accent-primary)" />
            <h3 style={{ fontSize: '18px', fontWeight: '600' }}>Seasonal Monthly Performance (Historical Average Return %)</h3>
          </div>
          
          <div style={{ width: '100%', height: '240px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={seasonal} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                <XAxis dataKey="month" stroke="var(--text-muted)" fontSize={11} tickLine={false} />
                <YAxis stroke="var(--text-muted)" fontSize={11} tickLine={false} unit="%" />
                <Tooltip 
                  formatter={(value) => [`${value}%`, 'Average Return']}
                  contentStyle={{ 
                    background: 'var(--bg-secondary)', 
                    borderColor: 'var(--border-standard)',
                    borderRadius: '8px',
                    color: 'white'
                  }} 
                />
                <Bar dataKey="average_return">
                  {seasonal.map((entry, index) => {
                    const isPositive = entry.average_return >= 0;
                    return (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={isPositive ? 'rgba(16, 185, 129, 0.7)' : 'rgba(239, 68, 68, 0.7)'} 
                        stroke={isPositive ? 'var(--color-success)' : 'var(--color-danger)'}
                        strokeWidth={1}
                      />
                    );
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '12px', lineHeight: '1.4' }}>
            * This bar chart calculates the mathematical average return of the stock for each calendar month (Jan–Dec) over its entire historical data. Green bars indicate months that have historically been profitable, while red bars indicate historically negative months.
          </p>
        </div>
      )}

    </div>
  );
}
