import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import { 
  Search, Loader2, ArrowUpRight, ArrowDownRight, TrendingUp, TrendingDown, 
  Zap, BarChart3, Activity, BarChart2, RefreshCw, BarChart, Layers 
} from 'lucide-react';

export default function Dashboard() {
  const [stocks, setStocks] = useState([]);
  const [signals, setSignals] = useState([]);
  const [weeklySignals, setWeeklySignals] = useState([]);
  const [bulkTrades, setBulkTrades] = useState([]);
  const [topPicks, setTopPicks] = useState([]);
  const [marketSummary, setMarketSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Tabs: 'securities', 'signals', 'bulk'
  const [activeTab, setActiveTab] = useState('securities'); 
  // Timeframe: 'DAILY' or 'WEEKLY' (for signals tab)
  const [timeframe, setTimeframe] = useState('DAILY'); 
  const [signalFilter, setSignalFilter] = useState('BUY'); // 'ALL', 'BUY', 'SELL', 'HOLD'
  const [categoryFilter, setCategoryFilter] = useState('ALL'); // 'ALL', 'PRICE_ACTION', 'MEAN_REVERSION', 'DIVERGENCE', 'DOW'
  
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const fetchData = async () => {
    try {
      setLoading(true);
      setError('');

      // Fetch all dashboard stats in parallel
      const [
        stocksResponse,
        signalsResponse,
        weeklyResponse,
        bulkResponse,
        summaryResponse,
        topPicksResponse
      ] = await Promise.all([
        api.get('/api/stocks/'),
        api.get('/api/signals/'),
        api.get('/api/signals/weekly/'),
        api.get('/api/signals/bulk-transactions/'),
        api.get('/api/signals/market-summary/'),
        api.get('/api/signals/custom-strategy/')
      ]);

      setStocks(stocksResponse.data || []);
      setSignals(signalsResponse.data || []);
      setWeeklySignals(weeklyResponse.data || []);
      setBulkTrades(bulkResponse.data || []);
      setMarketSummary(summaryResponse.data);
      setTopPicks(topPicksResponse.data || []);
    } catch (err) {
      setError('Failed to fetch dashboard metrics. Please make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Filter stocks based on search input safely
  const filteredStocks = (stocks || []).filter(stock => {
    if (!stock) return false;
    const symbol = stock.symbol || '';
    const name = stock.name || '';
    return symbol.toLowerCase().includes(search.toLowerCase()) ||
           name.toLowerCase().includes(search.toLowerCase());
  });

  // Filter signals safely
  const currentSignalsSource = timeframe === 'DAILY' ? (signals || []) : (weeklySignals || []);
  const filteredSignals = currentSignalsSource.filter(sig => {
    if (!sig) return false;
    const symbol = sig.symbol || '';
    const name = sig.name || '';
    const matchesSearch = symbol.toLowerCase().includes(search.toLowerCase()) ||
                         name.toLowerCase().includes(search.toLowerCase());
    if (!matchesSearch) return false;

    const matchesRec = signalFilter === 'ALL' || sig.recommendation === signalFilter;
    if (!matchesRec) return false;

    if (timeframe === 'DAILY') {
      if (categoryFilter === 'ALL') return true;
      if (categoryFilter === 'PRICE_ACTION') return sig.price_action !== 'HOLD';
      if (categoryFilter === 'MEAN_REVERSION') return sig.mean_reversion !== 'HOLD';
      if (categoryFilter === 'DIVERGENCE') return sig.divergence !== 'HOLD';
      if (categoryFilter === 'DOW') return sig.dow !== 'HOLD';
    }

    return true;
  });

  // Filter bulk trades safely
  const filteredBulk = (bulkTrades || []).filter(trade => {
    if (!trade) return false;
    const symbol = trade.symbol || '';
    const name = trade.name || '';
    return symbol.toLowerCase().includes(search.toLowerCase()) ||
           name.toLowerCase().includes(search.toLowerCase());
  });

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
        <Loader2 className="animate-spin" size={48} color="var(--accent-primary)" />
      </div>
    );
  }

  // Count signals safely
  const buyCount = currentSignalsSource.filter(s => s && s.recommendation === 'BUY').length;
  const sellCount = currentSignalsSource.filter(s => s && s.recommendation === 'SELL').length;
  const holdCount = currentSignalsSource.filter(s => s && s.recommendation === 'HOLD').length;

  // Format volume safely
  const formatVol = (val) => {
    if (val === null || val === undefined || isNaN(val)) return '0';
    const num = parseFloat(val);
    if (num >= 10000000) return `${(num / 10000000).toFixed(2)} Cr`;
    if (num >= 100000) return `${(num / 100000).toFixed(2)} Lac`;
    return num.toLocaleString();
  };

  // Format amount safely
  const formatAmt = (val) => {
    if (val === null || val === undefined || isNaN(val)) return 'Rs. 0';
    const num = parseFloat(val);
    if (num >= 1000000000) return `${(num / 1000000000).toFixed(2)} Ar`;
    if (num >= 10000000) return `${(num / 10000000).toFixed(2)} Cr`;
    return `Rs. ${num.toLocaleString()}`;
  };

  const isIndexUp = marketSummary && marketSummary.nepse_change !== undefined ? marketSummary.nepse_change >= 0 : true;

  return (
    <div className="main-content">
      {/* Top Title Section */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 className="page-title">Market Dashboard</h1>
          <p className="page-subtitle">Real-time Nepal Stock Exchange (NEPSE) analytics & indicators</p>
        </div>
        <button 
          onClick={fetchData} 
          className="btn-secondary" 
          style={{ width: 'auto', display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 16px' }}
        >
          <RefreshCw size={16} /> Refresh
        </button>
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

      {/* 1. Market Status Bar */}
      {marketSummary && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px',
          background: 'rgba(255, 255, 255, 0.02)',
          border: '1px solid var(--border-standard)',
          borderRadius: '12px',
          padding: '16px 24px',
          marginBottom: '32px'
        }}>
          <div>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: '600', textTransform: 'uppercase' }}>NEPSE Index</span>
            <div style={{ fontSize: '20px', fontWeight: '800', marginTop: '4px' }}>{marketSummary.nepse_index.toFixed(2)}</div>
            <div style={{ 
              fontSize: '12px', 
              fontWeight: '600', 
              color: isIndexUp ? 'var(--color-success)' : 'var(--color-danger)',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              marginTop: '2px'
            }}>
              {isIndexUp ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
              {isIndexUp ? '+' : ''}{marketSummary.nepse_change.toFixed(2)} ({marketSummary.nepse_change_percentage.toFixed(2)}%)
            </div>
          </div>

          <div>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: '600', textTransform: 'uppercase' }}>Daily Volume</span>
            <div style={{ fontSize: '20px', fontWeight: '800', marginTop: '4px' }}>{formatVol(marketSummary.total_volume)}</div>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>shares traded today</span>
          </div>

          <div>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: '600', textTransform: 'uppercase' }}>Daily Turnover</span>
            <div style={{ fontSize: '20px', fontWeight: '800', marginTop: '4px' }}>{formatAmt(marketSummary.total_amount)}</div>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>amount traded today</span>
          </div>

          <div>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: '600', textTransform: 'uppercase' }}>Market Sentiment</span>
            <div style={{ display: 'flex', gap: '12px', marginTop: '8px', fontSize: '14px', fontWeight: '700' }}>
              <span className="trend-up" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                🟢 {marketSummary.advances}
              </span>
              <span className="trend-down" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                🔴 {marketSummary.declines}
              </span>
              <span style={{ color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                🟡 {marketSummary.unchanged}
              </span>
            </div>
            <span style={{ fontSize: '11px', color: 'var(--text-secondary)', display: 'block', marginTop: '4px' }}>Adv / Dec / Unch</span>
          </div>
        </div>
      )}

      {/* 1.5 Top Picks (Value + Momentum) */}
      {topPicks && topPicks.length > 0 && (
        <div style={{ marginBottom: '40px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '800', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-success)' }}>
            <Zap size={20} /> High Conviction Top Picks (Value + Momentum)
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
            {topPicks.map(pick => (
              <div key={pick.symbol} className="glass-card" style={{ padding: '16px', cursor: 'pointer', borderLeft: '4px solid var(--color-success)' }} onClick={() => navigate(`/stock/${pick.symbol}`)}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <div>
                    <h4 style={{ fontSize: '18px', fontWeight: '800', margin: 0 }}>{pick.symbol}</h4>
                    <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Rs. {pick.price.toFixed(2)}</span>
                  </div>
                  <span style={{ background: 'rgba(16, 185, 129, 0.15)', color: 'var(--color-success)', padding: '4px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: '800' }}>
                    {pick.fundamental_verdict}
                  </span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Technicals:</span>
                    <span style={{ fontWeight: '600' }}>{pick.technical_label}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-muted)' }}>P/E Ratio:</span>
                    <span style={{ fontWeight: '600', color: pick.pe_ratio === 'Undervalued' ? 'var(--color-success)' : 'inherit' }}>{pick.pe_ratio}</span>
                  </div>
                  <div style={{ display: 'flex', gap: '12px', marginTop: '4px' }}>
                    <span style={{ background: 'var(--surface-color)', padding: '2px 6px', borderRadius: '4px', border: '1px solid var(--border-color)', color: 'var(--color-success)' }}>TP: Rs. {pick.tp_level}</span>
                    <span style={{ background: 'var(--surface-color)', padding: '2px 6px', borderRadius: '4px', border: '1px solid var(--border-color)', color: 'var(--color-danger)' }}>SL: Rs. {pick.sl_level}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 2. Middle Row: Pressure Gauges & Top Turnover */}
      {marketSummary && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1.2fr 1fr',
          gap: '32px',
          marginBottom: '40px',
          alignItems: 'start'
        }}>
          {/* Pressure Gauge */}
          <div className="glass-card" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Activity size={18} color="var(--accent-primary)" /> Live Market Pressure Gauge
            </h3>
            <div style={{
              width: '100%',
              height: '24px',
              borderRadius: '8px',
              overflow: 'hidden',
              display: 'flex',
              marginBottom: '20px',
              background: 'rgba(255,255,255,0.05)'
            }}>
              <div style={{ width: `${marketSummary.buy_pressure_pct}%`, background: 'var(--color-success)', height: '100%' }} />
              <div style={{ width: `${marketSummary.neutral_pressure_pct}%`, background: 'var(--color-warning)', height: '100%' }} />
              <div style={{ width: `${marketSummary.sell_pressure_pct}%`, background: 'var(--color-danger)', height: '100%' }} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--color-success)' }}></span>
                  BUY PRESSURE
                </span>
                <span style={{ fontSize: '18px', fontWeight: '700', color: 'var(--color-success)', paddingLeft: '14px' }}>
                  {marketSummary.buy_pressure_pct}%
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--color-warning)' }}></span>
                  NEUTRAL (HOLD)
                </span>
                <span style={{ fontSize: '18px', fontWeight: '700', color: 'var(--color-warning)', paddingLeft: '14px' }}>
                  {marketSummary.neutral_pressure_pct}%
                </span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <span style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--color-danger)' }}></span>
                  SELL PRESSURE
                </span>
                <span style={{ fontSize: '18px', fontWeight: '700', color: 'var(--color-danger)', paddingLeft: '14px' }}>
                  {marketSummary.sell_pressure_pct}%
                </span>
              </div>
            </div>
          </div>

          {/* Top Turnover */}
          <div className="glass-card" style={{ padding: '24px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '700', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <BarChart2 size={18} color="var(--accent-primary)" /> Top active stocks (Turnover)
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {marketSummary.top_turnover.map((item) => {
                const isUp = item.change_percentage >= 0;
                return (
                  <div 
                    key={item.symbol}
                    onClick={() => navigate(`/stock/${item.symbol}`)}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '8px 10px',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      background: 'rgba(255,255,255,0.01)',
                      border: '1px solid rgba(255,255,255,0.02)',
                      transition: 'all 0.15s ease'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.03)'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.01)'}
                  >
                    <div>
                      <span style={{ fontWeight: '700', fontSize: '14px' }}>{item.symbol}</span>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Vol: {item.volume.toLocaleString()} shares</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontWeight: '600', fontSize: '14px' }}>Rs. {item.price.toFixed(2)}</div>
                      <span style={{ fontSize: '12px', fontWeight: '600' }} className={isUp ? 'trend-up' : 'trend-down'}>
                        {isUp ? '+' : ''}{item.change_percentage.toFixed(2)}%
                      </span>
                    </div>
                    <div style={{ textAlign: 'right', minWidth: '80px' }}>
                      <span style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-secondary)' }}>
                        {formatAmt(item.turnover)}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Tab Navigation header */}
      <div style={{ display: 'flex', gap: '16px', borderBottom: '1px solid var(--border-standard)', marginBottom: '24px' }}>
        <button
          onClick={() => setActiveTab('securities')}
          style={{
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'securities' ? '2px solid var(--accent-primary)' : '2px solid transparent',
            color: activeTab === 'securities' ? 'white' : 'var(--text-secondary)',
            cursor: 'pointer',
            fontSize: '16px',
            fontWeight: '600',
            padding: '12px 16px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            transition: 'all 0.2s'
          }}
        >
          <BarChart3 size={18} /> All Securities ({stocks.length})
        </button>
        <button
          onClick={() => setActiveTab('signals')}
          style={{
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'signals' ? '2px solid var(--accent-primary)' : '2px solid transparent',
            color: activeTab === 'signals' ? 'white' : 'var(--text-secondary)',
            cursor: 'pointer',
            fontSize: '16px',
            fontWeight: '600',
            padding: '12px 16px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            transition: 'all 0.2s'
          }}
        >
          <Zap size={18} /> Buy / Sell Recommendations ({currentSignalsSource.length})
        </button>
        <button
          onClick={() => setActiveTab('bulk')}
          style={{
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'bulk' ? '2px solid var(--accent-primary)' : '2px solid transparent',
            color: activeTab === 'bulk' ? 'white' : 'var(--text-secondary)',
            cursor: 'pointer',
            fontSize: '16px',
            fontWeight: '600',
            padding: '12px 16px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            transition: 'all 0.2s'
          }}
        >
          <Layers size={18} /> Bulk Txn Zone ({bulkTrades.length})
        </button>
      </div>

      {/* Search and Filters toolbar */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        {activeTab === 'signals' ? (
          <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
            {/* BUY/SELL Filters */}
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={() => setSignalFilter('BUY')}
                style={{
                  padding: '6px 12px',
                  borderRadius: '6px',
                  border: '1px solid var(--border-standard)',
                  background: signalFilter === 'BUY' ? 'rgba(16, 185, 129, 0.15)' : 'transparent',
                  color: signalFilter === 'BUY' ? 'var(--color-success)' : 'var(--text-secondary)',
                  borderColor: signalFilter === 'BUY' ? 'var(--color-success)' : 'var(--border-standard)',
                  fontWeight: '600',
                  cursor: 'pointer',
                  fontSize: '13px'
                }}
              >
                🟢 BUY ({buyCount})
              </button>
              <button
                onClick={() => setSignalFilter('SELL')}
                style={{
                  padding: '6px 12px',
                  borderRadius: '6px',
                  border: '1px solid var(--border-standard)',
                  background: signalFilter === 'SELL' ? 'rgba(239, 68, 68, 0.15)' : 'transparent',
                  color: signalFilter === 'SELL' ? 'var(--color-danger)' : 'var(--text-secondary)',
                  borderColor: signalFilter === 'SELL' ? 'var(--color-danger)' : 'var(--border-standard)',
                  fontWeight: '600',
                  cursor: 'pointer',
                  fontSize: '13px'
                }}
              >
                🔴 SELL ({sellCount})
              </button>
              <button
                onClick={() => setSignalFilter('HOLD')}
                style={{
                  padding: '6px 12px',
                  borderRadius: '6px',
                  border: '1px solid var(--border-standard)',
                  background: signalFilter === 'HOLD' ? 'rgba(245, 158, 11, 0.15)' : 'transparent',
                  color: signalFilter === 'HOLD' ? 'var(--color-warning)' : 'var(--text-secondary)',
                  borderColor: signalFilter === 'HOLD' ? 'var(--color-warning)' : 'var(--border-standard)',
                  fontWeight: '600',
                  cursor: 'pointer',
                  fontSize: '13px'
                }}
              >
                🟡 HOLD ({holdCount})
              </button>
              <button
                onClick={() => setSignalFilter('ALL')}
                style={{
                  padding: '6px 12px',
                  borderRadius: '6px',
                  border: '1px solid var(--border-standard)',
                  background: signalFilter === 'ALL' ? 'rgba(255, 255, 255, 0.05)' : 'transparent',
                  color: 'white',
                  fontWeight: '600',
                  cursor: 'pointer',
                  fontSize: '13px'
                }}
              >
                All
              </button>
            </div>

            {/* DAILY VS WEEKLY TIMEFRAME TOGGLE */}
            <div style={{ height: '20px', width: '1px', background: 'var(--border-standard)' }} />
            
            <div style={{ display: 'flex', gap: '4px', background: 'var(--bg-tertiary)', padding: '3px', borderRadius: '8px' }}>
              <button
                onClick={() => { setTimeframe('DAILY'); setCategoryFilter('ALL'); }}
                style={{
                  padding: '4px 10px',
                  borderRadius: '6px',
                  border: 'none',
                  background: timeframe === 'DAILY' ? 'var(--accent-primary)' : 'transparent',
                  color: timeframe === 'DAILY' ? 'white' : 'var(--text-secondary)',
                  fontWeight: '600',
                  cursor: 'pointer',
                  fontSize: '12px'
                }}
              >
                Daily Signals
              </button>
              <button
                onClick={() => { setTimeframe('WEEKLY'); setCategoryFilter('ALL'); }}
                style={{
                  padding: '4px 10px',
                  borderRadius: '6px',
                  border: 'none',
                  background: timeframe === 'WEEKLY' ? 'var(--accent-primary)' : 'transparent',
                  color: timeframe === 'WEEKLY' ? 'white' : 'var(--text-secondary)',
                  fontWeight: '600',
                  cursor: 'pointer',
                  fontSize: '12px'
                }}
              >
                Weekly Signals
              </button>
            </div>
          </div>
        ) : <div />}

        <div style={{ position: 'relative', maxWidth: '300px', width: '100%' }}>
          <Search size={18} color="var(--text-secondary)" style={{
            position: 'absolute',
            left: '12px',
            top: '50%',
            transform: 'translateY(-50%)'
          }} />
          <input
            type="text"
            placeholder="Search symbol or company..."
            className="input-field"
            style={{ paddingLeft: '40px', paddingTop: '8px', paddingBottom: '8px', fontSize: '14px' }}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* 3. Sub-Category Types filter bar (Only on Daily signals) */}
      {activeTab === 'signals' && timeframe === 'DAILY' && (
        <div style={{
          display: 'flex',
          gap: '8px',
          padding: '10px 16px',
          background: 'rgba(255, 255, 255, 0.01)',
          border: '1px solid var(--border-standard)',
          borderRadius: '10px',
          marginBottom: '20px',
          flexWrap: 'wrap',
          alignItems: 'center'
        }}>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: '600', marginRight: '8px', textTransform: 'uppercase' }}>Scan Types:</span>
          <button onClick={() => setCategoryFilter('ALL')} style={{ padding: '4px 10px', borderRadius: '6px', border: 'none', background: categoryFilter === 'ALL' ? 'var(--accent-primary)' : 'transparent', color: categoryFilter === 'ALL' ? 'white' : 'var(--text-secondary)', cursor: 'pointer', fontSize: '12px', fontWeight: '600' }}>All Types</button>
          <button onClick={() => setCategoryFilter('PRICE_ACTION')} style={{ padding: '4px 10px', borderRadius: '6px', border: 'none', background: categoryFilter === 'PRICE_ACTION' ? 'var(--accent-primary)' : 'transparent', color: categoryFilter === 'PRICE_ACTION' ? 'white' : 'var(--text-secondary)', cursor: 'pointer', fontSize: '12px', fontWeight: '600' }}>Price Action</button>
          <button onClick={() => setCategoryFilter('MEAN_REVERSION')} style={{ padding: '4px 10px', borderRadius: '6px', border: 'none', background: categoryFilter === 'MEAN_REVERSION' ? 'var(--accent-primary)' : 'transparent', color: categoryFilter === 'MEAN_REVERSION' ? 'white' : 'var(--text-secondary)', cursor: 'pointer', fontSize: '12px', fontWeight: '600' }}>Mean Reversion</button>
          <button onClick={() => setCategoryFilter('DIVERGENCE')} style={{ padding: '4px 10px', borderRadius: '6px', border: 'none', background: categoryFilter === 'DIVERGENCE' ? 'var(--accent-primary)' : 'transparent', color: categoryFilter === 'DIVERGENCE' ? 'white' : 'var(--text-secondary)', cursor: 'pointer', fontSize: '12px', fontWeight: '600' }}>Divergence</button>
          <button onClick={() => setCategoryFilter('DOW')} style={{ padding: '4px 10px', borderRadius: '6px', border: 'none', background: categoryFilter === 'DOW' ? 'var(--accent-primary)' : 'transparent', color: categoryFilter === 'DOW' ? 'white' : 'var(--text-secondary)', cursor: 'pointer', fontSize: '12px', fontWeight: '600' }}>Dow Theory</button>
        </div>
      )}

      {/* Conditionally render Tab Panels */}
      {activeTab === 'securities' && (
        <div className="glass-card" style={{ padding: '24px 0' }}>
          <div className="table-container" style={{ border: 'none', borderRadius: 0 }}>
            <table className="custom-table">
              <thead>
                <tr>
                  <th style={{ paddingLeft: '24px' }}>Symbol</th>
                  <th>Company Name</th>
                  <th>Price (LTP)</th>
                  <th>Volume</th>
                  <th style={{ paddingRight: '24px' }}>Change %</th>
                </tr>
              </thead>
              <tbody>
                {filteredStocks.map((s) => {
                  const change = parseFloat(s.change_percentage);
                  return (
                    <tr key={s.symbol} onClick={() => navigate(`/stock/${s.symbol}`)} style={{ cursor: 'pointer' }}>
                      <td style={{ paddingLeft: '24px', fontWeight: '700' }}>{s.symbol}</td>
                      <td style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>{s.name}</td>
                      <td style={{ fontWeight: '500' }}>Rs. {parseFloat(s.current_price).toFixed(2)}</td>
                      <td style={{ color: 'var(--text-secondary)' }}>{parseInt(s.volume).toLocaleString()}</td>
                      <td style={{ paddingRight: '24px' }} className={change > 0 ? 'trend-up' : change < 0 ? 'trend-down' : ''}>
                        {change > 0 ? `+${change.toFixed(2)}%` : `${change.toFixed(2)}%`}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'signals' && (
        <div className="glass-card" style={{ padding: '24px 0' }}>
          <div className="table-container" style={{ border: 'none', borderRadius: 0 }}>
            <table className="custom-table">
              <thead>
                <tr>
                  <th style={{ paddingLeft: '24px' }}>Symbol</th>
                  <th>LTP (Rs.)</th>
                  <th>Change %</th>
                  <th>Action Signal</th>
                  {timeframe === 'DAILY' && <th>RSI (14)</th>}
                  <th style={{ paddingRight: '24px' }}>Advice & Explanation</th>
                </tr>
              </thead>
              <tbody>
                {filteredSignals.map((sig) => {
                  const rec = sig.recommendation;
                  const change = parseFloat(sig.change_percentage);
                  const rsiVal = sig.rsi_value;
                  
                  let badgeBg = 'rgba(245, 158, 11, 0.1)';
                  let badgeText = 'var(--color-warning)';
                  let badgeBorder = 'rgba(245, 158, 11, 0.2)';
                  
                  if (rec === 'BUY') {
                    badgeBg = 'rgba(16, 185, 129, 0.1)';
                    badgeText = 'var(--color-success)';
                    badgeBorder = 'rgba(16, 185, 129, 0.2)';
                  } else if (rec === 'SELL') {
                    badgeBg = 'rgba(239, 68, 68, 0.1)';
                    badgeText = 'var(--color-danger)';
                    badgeBorder = 'rgba(239, 68, 68, 0.2)';
                  }

                  let rsiBg = 'rgba(255, 255, 255, 0.05)';
                  let rsiText = 'var(--text-secondary)';
                  if (rsiVal !== null && rsiVal !== undefined) {
                    if (rsiVal <= 30) {
                      rsiBg = 'rgba(16, 185, 129, 0.15)';
                      rsiText = 'var(--color-success)';
                    } else if (rsiVal >= 70) {
                      rsiBg = 'rgba(239, 68, 68, 0.15)';
                      rsiText = 'var(--color-danger)';
                    }
                  }

                  return (
                    <tr key={sig.symbol} onClick={() => navigate(`/stock/${sig.symbol}`)} style={{ cursor: 'pointer' }}>
                      <td style={{ paddingLeft: '24px', fontWeight: '700' }}>{sig.symbol}</td>
                      <td style={{ fontWeight: '500' }}>Rs. {parseFloat(sig.price).toFixed(2)}</td>
                      <td className={change > 0 ? 'trend-up' : change < 0 ? 'trend-down' : ''}>
                        {change > 0 ? `+${change.toFixed(2)}%` : `${change.toFixed(2)}%`}
                      </td>
                      <td>
                        <span style={{ background: badgeBg, color: badgeText, border: `1px solid ${badgeBorder}`, padding: '4px 12px', borderRadius: '6px', fontSize: '12px', fontWeight: '700' }}>
                          {sig.recommendation}
                        </span>
                      </td>
                      {timeframe === 'DAILY' && (
                        <td>
                          <span style={{ background: rsiBg, color: rsiText, padding: '3px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: '600' }}>
                            {rsiVal !== null && rsiVal !== undefined ? rsiVal : 'N/A'}
                          </span>
                        </td>
                      )}
                      <td style={{ paddingRight: '24px', color: 'var(--text-secondary)', fontSize: '13px', lineHeight: '1.4' }}>
                        <strong>{sig.signal_label}:</strong> {sig.signal_desc}
                        {sig.take_profit && sig.stop_loss && (
                          <div style={{ marginTop: '6px', display: 'flex', gap: '12px' }}>
                            <span style={{ color: 'var(--color-success)', fontWeight: '600', backgroundColor: 'rgba(16, 185, 129, 0.1)', padding: '2px 6px', borderRadius: '4px' }}>Target: Rs. {sig.take_profit}</span>
                            <span style={{ color: 'var(--color-danger)', fontWeight: '600', backgroundColor: 'rgba(239, 68, 68, 0.1)', padding: '2px 6px', borderRadius: '4px' }}>Stop Loss: Rs. {sig.stop_loss}</span>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
                {filteredSignals.length === 0 && (
                  <tr>
                    <td colSpan={timeframe === 'DAILY' ? "6" : "5"} style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                      No {signalFilter} signals found in the market.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'bulk' && (
        <div className="glass-card" style={{ padding: '24px 0' }}>
          <div style={{ padding: '0 24px 20px 24px', borderBottom: '1px solid var(--border-standard)' }}>
            <h3 style={{ fontSize: '18px', fontWeight: '600' }}>Institutional Traded Volume Alerts (&gt; 1.2 Lakh shares or Rs. 80 Lakhs)</h3>
          </div>
          <div className="table-container" style={{ border: 'none', borderRadius: 0 }}>
            <table className="custom-table">
              <thead>
                <tr>
                  <th style={{ paddingLeft: '24px' }}>Symbol</th>
                  <th>Company Name</th>
                  <th>Price (Rs.)</th>
                  <th>Change %</th>
                  <th>Shares Traded</th>
                  <th style={{ paddingRight: '24px' }}>Turnover Value</th>
                </tr>
              </thead>
              <tbody>
                {filteredBulk.map((trade) => {
                  const isUp = trade.change_percentage >= 0;
                  return (
                    <tr key={trade.symbol} onClick={() => navigate(`/stock/${trade.symbol}`)} style={{ cursor: 'pointer' }}>
                      <td style={{ paddingLeft: '24px', fontWeight: '700' }}>{trade.symbol}</td>
                      <td style={{ color: 'var(--text-secondary)' }}>{trade.name}</td>
                      <td style={{ fontWeight: '500' }}>Rs. {parseFloat(trade.price).toFixed(2)}</td>
                      <td className={isUp ? 'trend-up' : 'trend-down'}>
                        {isUp ? '+' : ''}{trade.change_percentage.toFixed(2)}%
                      </td>
                      <td>{trade.volume.toLocaleString()} shares</td>
                      <td style={{ paddingRight: '24px', fontWeight: '700' }}>
                        {formatAmt(trade.turnover)}
                      </td>
                    </tr>
                  );
                })}
                {filteredBulk.length === 0 && (
                  <tr>
                    <td colSpan="6" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                      No bulk transactions recorded on this day.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
