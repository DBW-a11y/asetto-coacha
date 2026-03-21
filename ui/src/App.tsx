import { Routes, Route, Link } from 'react-router-dom'
import SessionList from './pages/SessionList'
import SessionDetail from './pages/SessionDetail'
import LapView from './pages/LapView'

const styles = {
  app: {
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    background: '#0a0a0f',
    color: '#e0e0e0',
    minHeight: '100vh',
  },
  nav: {
    background: '#12121a',
    borderBottom: 'none',
    padding: '12px 24px',
    display: 'flex',
    alignItems: 'center',
    gap: '24px',
    position: 'relative' as const,
  },
  navLine: {
    position: 'absolute' as const,
    bottom: 0,
    left: 0,
    right: 0,
    height: '2px',
    background: 'linear-gradient(90deg, #ff4444 0%, #ff8800 50%, #ff4444 100%)',
  },
  logo: {
    color: '#ff4444',
    fontWeight: 700,
    fontSize: '18px',
    textDecoration: 'none',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
  },
  content: {
    maxWidth: '1400px',
    margin: '0 auto',
    padding: '24px',
  },
} as const

function FlagIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <rect x="3" y="2" width="4" height="4" fill="#ff4444" />
      <rect x="7" y="2" width="4" height="4" fill="#fff" />
      <rect x="11" y="2" width="4" height="4" fill="#ff4444" />
      <rect x="3" y="6" width="4" height="4" fill="#fff" />
      <rect x="7" y="6" width="4" height="4" fill="#ff4444" />
      <rect x="11" y="6" width="4" height="4" fill="#fff" />
      <rect x="3" y="10" width="4" height="4" fill="#ff4444" />
      <rect x="7" y="10" width="4" height="4" fill="#fff" />
      <rect x="11" y="10" width="4" height="4" fill="#ff4444" />
      <line x1="2" y1="2" x2="2" y2="18" stroke="#666" strokeWidth="1.5" />
    </svg>
  )
}

export default function App() {
  return (
    <div style={styles.app}>
      <nav style={styles.nav}>
        <Link to="/" style={styles.logo}>
          <FlagIcon />
          Racing Coach
        </Link>
        <div style={styles.navLine} />
      </nav>
      <div style={styles.content}>
        <Routes>
          <Route path="/" element={<SessionList />} />
          <Route path="/session/:sessionId" element={<SessionDetail />} />
          <Route path="/session/:sessionId/lap/:lapNumber" element={<LapView />} />
        </Routes>
      </div>
    </div>
  )
}
