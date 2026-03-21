import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import type { Session } from '../api'

function formatTime(ms: number | null): string {
  if (!ms) return '-'
  const s = ms / 1000
  const min = Math.floor(s / 60)
  const sec = s % 60
  return min > 0 ? `${min}:${sec.toFixed(3).padStart(6, '0')}` : `${sec.toFixed(3)}s`
}

function SessionCard({ session }: { session: Session }) {
  const [hovered, setHovered] = useState(false)

  return (
    <Link
      to={`/session/${session.id}`}
      style={{
        background: hovered
          ? 'linear-gradient(135deg, #1a1a2e 0%, #16161e 100%)'
          : '#16161e',
        border: `1px solid ${hovered ? '#ff444466' : '#2a2a3a'}`,
        borderRadius: '10px',
        padding: '0',
        textDecoration: 'none',
        color: 'inherit',
        transition: 'all 0.25s ease',
        overflow: 'hidden',
        display: 'block',
        transform: hovered ? 'translateY(-2px)' : 'none',
        boxShadow: hovered ? '0 4px 20px rgba(255,68,68,0.1)' : 'none',
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Top color accent bar */}
      <div style={{
        height: '3px',
        background: 'linear-gradient(90deg, #ff4444, #ff8800)',
      }} />
      <div style={{ padding: '20px' }}>
        <div style={{ fontSize: '18px', fontWeight: 600, color: '#fff', marginBottom: '4px' }}>
          {session.track}
        </div>
        <div style={{ fontSize: '14px', color: '#888', marginBottom: '14px' }}>
          {session.car}
        </div>
        <div style={{ display: 'flex', gap: '24px', fontSize: '13px' }}>
          <div>
            <div style={{ color: '#666', fontSize: '11px', textTransform: 'uppercase' }}>Laps</div>
            <div style={{ color: '#ddd', fontSize: '16px', fontWeight: 500 }}>{session.num_laps}</div>
          </div>
          <div>
            <div style={{ color: '#666', fontSize: '11px', textTransform: 'uppercase' }}>Best Lap</div>
            <div style={{ color: '#ff6666', fontSize: '16px', fontWeight: 500, fontFamily: 'monospace' }}>
              {formatTime(session.best_lap_time_ms)}
            </div>
          </div>
          <div>
            <div style={{ color: '#666', fontSize: '11px', textTransform: 'uppercase' }}>Date</div>
            <div style={{ color: '#ddd', fontSize: '16px', fontWeight: 500 }}>
              {new Date(session.started_at).toLocaleDateString()}
            </div>
          </div>
        </div>
      </div>
    </Link>
  )
}

export default function SessionList() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.listSessions().then(setSessions).finally(() => setLoading(false))
  }, [])

  if (loading) return <p>Loading sessions...</p>
  if (sessions.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 0', color: '#666' }}>
        <h2>No sessions yet</h2>
        <p>Run <code>racing-coach generate-mock</code> to create sample data</p>
      </div>
    )
  }

  return (
    <div>
      <h1 style={{ marginBottom: '24px' }}>Sessions</h1>
      <div style={{
        display: 'grid',
        gap: '16px',
        gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
      }}>
        {sessions.map(s => (
          <SessionCard key={s.id} session={s} />
        ))}
      </div>
    </div>
  )
}
