import React from 'react';
import { Zap, RotateCcw, Play, Pause, LayoutDashboard, BarChart3 } from 'lucide-react';
import StatusDot from '../common/StatusDot';

export default function Sidebar({ isConnected, isAutoRunning, onReset, onToggleAutoRun, terminated, activeTab, setActiveTab }) {
  return (
    <aside
      style={{
        width: 220,
        minHeight: '100vh',
        background: 'var(--surface-0)',
        borderRight: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        padding: 0,
        flexShrink: 0,
      }}
    >
      {/* Brand */}
      <div
        style={{
          padding: 'var(--space-6)',
          borderBottom: '1px solid var(--border-subtle)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 'var(--radius-md)',
              background: 'linear-gradient(135deg, var(--accent), var(--accent-strong))',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Zap size={18} color="var(--text-inverse)" strokeWidth={2.5} />
          </div>
          <div>
            <h1
              style={{
                fontSize: '1rem',
                fontWeight: 700,
                letterSpacing: '-0.02em',
                lineHeight: 1.2,
              }}
            >
              GridMind
            </h1>
            <span
              style={{
                fontSize: '0.625rem',
                color: 'var(--text-muted)',
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
                fontWeight: 500,
              }}
            >
              Energy Sim v1.0
            </span>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ padding: 'var(--space-4)', flex: 1, display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
        <button
          onClick={() => setActiveTab('dashboard')}
          className={`btn ${activeTab === 'dashboard' ? 'btn-accent' : ''}`}
          style={{
            width: '100%',
            justifyContent: 'flex-start',
            gap: 'var(--space-3)',
            padding: 'var(--space-2) var(--space-4)',
            fontSize: '0.8125rem',
            fontWeight: activeTab === 'dashboard' ? 600 : 500,
            background: activeTab === 'dashboard' ? 'var(--surface-3)' : 'transparent',
            borderColor: activeTab === 'dashboard' ? 'var(--accent)' : 'transparent',
            color: activeTab === 'dashboard' ? 'var(--accent)' : 'var(--text-muted)',
            boxShadow: 'none',
          }}
        >
          <LayoutDashboard size={15} style={{ opacity: activeTab === 'dashboard' ? 1 : 0.6 }} />
          Dashboard
        </button>

        <button
          onClick={() => setActiveTab('analytics')}
          className={`btn ${activeTab === 'analytics' ? 'btn-accent' : ''}`}
          style={{
            width: '100%',
            justifyContent: 'flex-start',
            gap: 'var(--space-3)',
            padding: 'var(--space-2) var(--space-4)',
            fontSize: '0.8125rem',
            fontWeight: activeTab === 'analytics' ? 600 : 500,
            background: activeTab === 'analytics' ? 'var(--surface-3)' : 'transparent',
            borderColor: activeTab === 'analytics' ? 'var(--accent)' : 'transparent',
            color: activeTab === 'analytics' ? 'var(--accent)' : 'var(--text-muted)',
            boxShadow: 'none',
          }}
        >
          <BarChart3 size={15} style={{ opacity: activeTab === 'analytics' ? 1 : 0.6 }} />
          Analytics
        </button>
      </nav>

      {/* Controls */}
      <div
        style={{
          padding: 'var(--space-5)',
          borderTop: '1px solid var(--border-subtle)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-3)',
        }}
      >
        <span
          style={{
            fontSize: '0.6875rem',
            fontWeight: 600,
            color: 'var(--text-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
            marginBottom: 'var(--space-1)',
          }}
        >
          Simulation
        </span>

        <button
          className="btn"
          onClick={onReset}
          style={{ width: '100%', justifyContent: 'center' }}
        >
          <RotateCcw size={14} />
          Reset Episode
        </button>

        <button
          className={`btn ${isAutoRunning ? 'btn-danger' : 'btn-accent'}`}
          onClick={onToggleAutoRun}
          disabled={terminated}
          style={{
            width: '100%',
            justifyContent: 'center',
            opacity: terminated ? 0.4 : 1,
          }}
        >
          {isAutoRunning ? <Pause size={14} /> : <Play size={14} />}
          {isAutoRunning ? 'Pause' : 'Auto-Run'}
        </button>

        {/* Connection */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-2)',
            marginTop: 'var(--space-2)',
            fontSize: '0.75rem',
            color: 'var(--text-muted)',
          }}
        >
          <StatusDot
            status={isConnected ? 'success' : 'danger'}
            pulse={isConnected}
            size={7}
          />
          {isConnected ? 'API Connected' : 'Disconnected'}
        </div>
      </div>
    </aside>
  );
}
