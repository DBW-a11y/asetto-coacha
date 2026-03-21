import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import type { TelemetryData, LapAnalysis } from '../api'
import TelemetryChart from '../components/TelemetryChart'
import ScoreCard from '../components/ScoreCard'
import CoachingCard from '../components/CoachingCard'
import StatsBar from '../components/StatsBar'
import CornerCards from '../components/CornerCards'

function formatLapTime(ms: number): string {
  const s = ms / 1000
  const min = Math.floor(s / 60)
  const sec = s % 60
  return min > 0 ? `${min}:${sec.toFixed(3).padStart(6, '0')}` : `${sec.toFixed(3)}s`
}

const styles = {
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '24px',
  },
  lapTitle: {
    fontSize: '28px',
    fontWeight: 700,
    color: '#fff',
  },
  lapTime: {
    fontSize: '28px',
    fontWeight: 700,
    color: '#ff6666',
    fontFamily: 'monospace',
  },
  section: {
    marginTop: '24px',
  },
  sectionHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    cursor: 'pointer',
    padding: '12px 0',
    fontSize: '16px',
    fontWeight: 600,
    color: '#aaa',
    userSelect: 'none' as const,
  },
  sectionContent: {
    paddingTop: '8px',
  },
} as const

export default function LapView() {
  const { sessionId, lapNumber } = useParams<{ sessionId: string; lapNumber: string }>()
  const lap = parseInt(lapNumber || '0')
  const [telemetry, setTelemetry] = useState<TelemetryData | null>(null)
  const [analysis, setAnalysis] = useState<LapAnalysis | null>(null)
  const [showCharts, setShowCharts] = useState(true)
  const [showCorners, setShowCorners] = useState(true)

  useEffect(() => {
    if (!sessionId) return
    api.getLapTelemetry(sessionId, lap, 2).then(setTelemetry)
    api.analyzeLap(sessionId, lap).then(setAnalysis)
  }, [sessionId, lap])

  const statsItems = analysis ? [
    { label: 'Max Speed', value: analysis.metrics.max_speed_kmh?.toFixed(0) ?? '-', unit: 'km/h' },
    { label: 'Avg Speed', value: analysis.metrics.avg_speed_kmh?.toFixed(0) ?? '-', unit: 'km/h' },
    { label: 'Throttle', value: analysis.metrics.avg_throttle != null ? (analysis.metrics.avg_throttle * 100).toFixed(0) : '-', unit: '%' },
    { label: 'Brake', value: analysis.metrics.avg_brake != null ? (analysis.metrics.avg_brake * 100).toFixed(0) : '-', unit: '%' },
    { label: 'Max RPM', value: analysis.metrics.max_rpm?.toFixed(0) ?? '-' },
    { label: 'Corners', value: String(analysis.corners.length) },
  ] : []

  return (
    <div>
      {/* Header */}
      <Link to={`/session/${sessionId}`} style={{ color: '#888', textDecoration: 'none', fontSize: '14px' }}>
        &larr; Back to session
      </Link>
      <div style={styles.header}>
        <span style={styles.lapTitle}>Lap {lap + 1}</span>
        {analysis && (
          <span style={styles.lapTime}>{formatLapTime(analysis.metrics.lap_time_ms)}</span>
        )}
      </div>

      {/* Score Gauges */}
      {analysis && <ScoreCard score={analysis.score} />}

      {/* Quick Stats */}
      {analysis && (
        <div style={{ marginTop: '16px' }}>
          <StatsBar stats={statsItems} />
        </div>
      )}

      {/* AI Coach Analysis — Main content */}
      {sessionId && (
        <div style={{ marginTop: '24px' }}>
          <CoachingCard sessionId={sessionId} lapNumber={lap} />
        </div>
      )}

      {/* Telemetry Charts — Collapsible */}
      <div style={styles.section}>
        <div style={styles.sectionHeader} onClick={() => setShowCharts(!showCharts)}>
          <span>{showCharts ? '▾' : '▸'}</span>
          <span>Telemetry Charts</span>
        </div>
        {showCharts && telemetry && (
          <div style={styles.sectionContent}>
            <TelemetryChart data={telemetry} />
          </div>
        )}
      </div>

      {/* Corners — Collapsible */}
      {analysis && analysis.corners.length > 0 && (
        <div style={styles.section}>
          <div style={styles.sectionHeader} onClick={() => setShowCorners(!showCorners)}>
            <span>{showCorners ? '▾' : '▸'}</span>
            <span>Corners ({analysis.corners.length})</span>
          </div>
          {showCorners && (
            <div style={styles.sectionContent}>
              <CornerCards corners={analysis.corners as any} />
            </div>
          )}
        </div>
      )}
    </div>
  )
}
