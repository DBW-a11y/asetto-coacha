import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import type { SessionDetail as SessionDetailType, CompareResult } from '../api'
import CompareChart from '../components/CompareChart'

function formatTime(ms: number): string {
  const s = ms / 1000
  const min = Math.floor(s / 60)
  const sec = s % 60
  return min > 0 ? `${min}:${sec.toFixed(3).padStart(6, '0')}` : `${sec.toFixed(3)}s`
}

function deltaColor(delta: number): string {
  if (delta === 0) return '#4caf50'
  if (delta < 0.5) return '#ffa726'
  return '#ef5350'
}

function LapRow({ lap, sessionId, isBest, delta }: {
  lap: { lap_number: number; lap_time_ms: number; is_valid: boolean }
  sessionId: string
  isBest: boolean
  delta: number
}) {
  const [hovered, setHovered] = useState(false)

  return (
    <tr
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: hovered ? 'rgba(255,255,255,0.03)' : 'transparent',
        transition: 'background 0.15s',
      }}
    >
      <td style={{ padding: '12px 16px', borderBottom: '1px solid #1e1e2a' }}>
        {isBest && <span style={{ color: '#ffd700', marginRight: '6px' }} title="Best lap">&#9733;</span>}
        {lap.lap_number + 1}
      </td>
      <td style={{
        padding: '12px 16px',
        borderBottom: '1px solid #1e1e2a',
        color: isBest ? '#4caf50' : '#e0e0e0',
        fontWeight: isBest ? 600 : 400,
        fontFamily: 'monospace',
      }}>
        {formatTime(lap.lap_time_ms)}
      </td>
      <td style={{
        padding: '12px 16px',
        borderBottom: '1px solid #1e1e2a',
        color: isBest ? '#4caf50' : deltaColor(delta),
        fontFamily: 'monospace',
      }}>
        {isBest ? '-' : `+${delta.toFixed(3)}s`}
      </td>
      <td style={{ padding: '12px 16px', borderBottom: '1px solid #1e1e2a' }}>
        {lap.is_valid
          ? <span style={{ color: '#66bb6a' }}>Yes</span>
          : <span style={{ color: '#ef5350' }}>No</span>
        }
      </td>
      <td style={{ padding: '12px 16px', borderBottom: '1px solid #1e1e2a' }}>
        <Link
          to={`/session/${sessionId}/lap/${lap.lap_number}`}
          style={{
            color: '#ff6666',
            textDecoration: 'none',
            padding: '4px 12px',
            borderRadius: '4px',
            border: '1px solid #ff444433',
            fontSize: '13px',
            transition: 'all 0.2s',
          }}
        >
          Analyze
        </Link>
      </td>
    </tr>
  )
}

const styles = {
  header: { marginBottom: '24px' },
  table: {
    width: '100%',
    borderCollapse: 'collapse' as const,
    background: '#16161e',
    borderRadius: '10px',
    overflow: 'hidden',
  },
  th: {
    textAlign: 'left' as const,
    padding: '12px 16px',
    background: '#1a1a24',
    color: '#888',
    fontSize: '12px',
    textTransform: 'uppercase' as const,
    borderBottom: '1px solid #2a2a3a',
  },
  compareSection: { marginTop: '32px' },
  select: {
    background: '#1a1a24',
    color: '#e0e0e0',
    border: '1px solid #2a2a3a',
    borderRadius: '4px',
    padding: '8px 12px',
    marginRight: '12px',
  },
  btn: {
    background: '#ff4444',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    padding: '8px 16px',
    cursor: 'pointer',
  },
} as const

export default function SessionDetail() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const [session, setSession] = useState<SessionDetailType | null>(null)
  const [refLap, setRefLap] = useState<number>(0)
  const [targetLap, setTargetLap] = useState<number>(1)
  const [comparison, setComparison] = useState<CompareResult | null>(null)
  const [comparing, setComparing] = useState(false)

  useEffect(() => {
    if (sessionId) {
      api.getSession(sessionId).then(s => {
        setSession(s)
        if (s.laps.length >= 2) {
          const best = s.laps.reduce((a, b) => a.lap_time_ms < b.lap_time_ms ? a : b)
          setRefLap(best.lap_number)
          const other = s.laps.find(l => l.lap_number !== best.lap_number)
          if (other) setTargetLap(other.lap_number)
        }
      })
    }
  }, [sessionId])

  if (!session) return <p>Loading...</p>

  const handleCompare = async () => {
    if (!sessionId) return
    setComparing(true)
    try {
      const result = await api.compareLaps(sessionId, refLap, targetLap)
      setComparison(result)
    } finally {
      setComparing(false)
    }
  }

  return (
    <div>
      <div style={styles.header}>
        <Link to="/" style={{ color: '#888', textDecoration: 'none', fontSize: '14px' }}>
          &larr; Sessions
        </Link>
        <h1>{session.track}</h1>
        <p style={{ color: '#888' }}>{session.car} &middot; {new Date(session.started_at).toLocaleString()}</p>
      </div>

      <table style={styles.table}>
        <thead>
          <tr>
            <th style={styles.th}>Lap</th>
            <th style={styles.th}>Time</th>
            <th style={styles.th}>Delta</th>
            <th style={styles.th}>Valid</th>
            <th style={styles.th}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {session.laps.map(lap => {
            const isBest = lap.lap_time_ms === session.best_lap_time_ms
            const delta = session.best_lap_time_ms
              ? (lap.lap_time_ms - session.best_lap_time_ms) / 1000
              : 0
            return (
              <LapRow
                key={lap.lap_number}
                lap={lap}
                sessionId={sessionId!}
                isBest={isBest}
                delta={delta}
              />
            )
          })}
        </tbody>
      </table>

      {session.laps.length >= 2 && (
        <div style={styles.compareSection}>
          <h2>Lap Comparison</h2>
          <div style={{ margin: '16px 0' }}>
            <label>
              Ref:
              <select style={styles.select} value={refLap} onChange={e => setRefLap(+e.target.value)}>
                {session.laps.map(l => (
                  <option key={l.lap_number} value={l.lap_number}>Lap {l.lap_number + 1}</option>
                ))}
              </select>
            </label>
            <label>
              vs:
              <select style={styles.select} value={targetLap} onChange={e => setTargetLap(+e.target.value)}>
                {session.laps.map(l => (
                  <option key={l.lap_number} value={l.lap_number}>Lap {l.lap_number + 1}</option>
                ))}
              </select>
            </label>
            <button style={styles.btn} onClick={handleCompare} disabled={comparing}>
              {comparing ? 'Comparing...' : 'Compare'}
            </button>
          </div>
          {comparison && <CompareChart data={comparison} refLabel={`Lap ${refLap + 1}`} targetLabel={`Lap ${targetLap + 1}`} />}
        </div>
      )}
    </div>
  )
}
