import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { BarChart3, BellRing, LogOut, TrendingUp, User, Briefcase, Compass } from 'lucide-react';

export default function Navigation() {
  const navigate = useNavigate();
  const username = localStorage.getItem('username') || 'User';

  const handleLogout = () => {
    localStorage.clear();
    navigate('/login');
  };

  return (
    <aside style={{
      width: '280px',
      background: 'var(--bg-secondary)',
      backdropFilter: 'blur(12px)',
      borderRight: '1px solid var(--border-standard)',
      display: 'flex',
      flexDirection: 'column',
      padding: '32px 24px',
      height: '100vh',
      position: 'sticky',
      top: 0
    }}>
      {/* Brand logo/title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '40px' }}>
        <div style={{
          background: 'linear-gradient(135deg, var(--accent-primary), #4f46e5)',
          padding: '8px',
          borderRadius: '8px',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center'
        }}>
          <TrendingUp size={24} color="white" />
        </div>
        <div>
          <h1 style={{ fontSize: '18px', fontWeight: '700', letterSpacing: '-0.5px' }}>NEPSE AI</h1>
          <p style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Signal & Alerts</p>
        </div>
      </div>

      {/* Nav Menu */}
      <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px', flexGrow: 1 }}>
        <NavLink 
          to="/" 
          style={({ isActive }) => ({
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '12px 16px',
            borderRadius: '8px',
            textDecoration: 'none',
            color: isActive ? 'white' : 'var(--text-secondary)',
            background: isActive ? 'rgba(99, 102, 241, 0.1)' : 'transparent',
            border: isActive ? '1px solid rgba(99, 102, 241, 0.2)' : '1px solid transparent',
            fontWeight: isActive ? '600' : '400',
            transition: 'all 0.2s ease'
          })}
        >
          <BarChart3 size={20} />
          Market Dashboard
        </NavLink>

        <NavLink 
          to="/portfolio" 
          style={({ isActive }) => ({
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '12px 16px',
            borderRadius: '8px',
            textDecoration: 'none',
            color: isActive ? 'white' : 'var(--text-secondary)',
            background: isActive ? 'rgba(99, 102, 241, 0.1)' : 'transparent',
            border: isActive ? '1px solid rgba(99, 102, 241, 0.2)' : '1px solid transparent',
            fontWeight: isActive ? '600' : '400',
            transition: 'all 0.2s ease'
          })}
        >
          <Briefcase size={20} />
          My Portfolio
        </NavLink>

        <NavLink 
          to="/watchlist" 
          style={({ isActive }) => ({
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '12px 16px',
            borderRadius: '8px',
            textDecoration: 'none',
            color: isActive ? 'white' : 'var(--text-secondary)',
            background: isActive ? 'rgba(99, 102, 241, 0.1)' : 'transparent',
            border: isActive ? '1px solid rgba(99, 102, 241, 0.2)' : '1px solid transparent',
            fontWeight: isActive ? '600' : '400',
            transition: 'all 0.2s ease'
          })}
        >
          <BellRing size={20} />
          Watchlist & Alerts
        </NavLink>

        <NavLink 
          to="/scanners" 
          style={({ isActive }) => ({
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '12px 16px',
            borderRadius: '8px',
            textDecoration: 'none',
            color: isActive ? 'white' : 'var(--text-secondary)',
            background: isActive ? 'rgba(99, 102, 241, 0.1)' : 'transparent',
            border: isActive ? '1px solid rgba(99, 102, 241, 0.2)' : '1px solid transparent',
            fontWeight: isActive ? '600' : '400',
            transition: 'all 0.2s ease'
          })}
        >
          <Compass size={20} />
          Technical Screener
        </NavLink>
      </nav>

      {/* User profile & Logout */}
      <div style={{
        paddingTop: '20px',
        borderTop: '1px solid var(--border-standard)',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            background: 'var(--bg-tertiary)',
            width: '40px',
            height: '40px',
            borderRadius: '50%',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            border: '1px solid var(--border-standard)'
          }}>
            <User size={18} color="var(--text-secondary)" />
          </div>
          <div>
            <p style={{ fontSize: '14px', fontWeight: '600' }}>{username}</p>
            <p style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Online</p>
          </div>
        </div>

        <button 
          onClick={handleLogout}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '12px 16px',
            borderRadius: '8px',
            border: 'none',
            background: 'transparent',
            color: 'var(--color-danger)',
            cursor: 'pointer',
            fontFamily: 'inherit',
            fontSize: '15px',
            textAlign: 'left',
            transition: 'all 0.2s ease',
            width: '100%'
          }}
          onMouseEnter={(e) => e.target.style.background = 'rgba(239, 68, 68, 0.05)'}
          onMouseLeave={(e) => e.target.style.background = 'transparent'}
        >
          <LogOut size={20} />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
