import { useEffect, useState, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { api } from '../api'

interface Props {
  sessionId: string
  lapNumber: number
}

const styles = {
  wrapper: {
    position: 'relative' as const,
    borderRadius: '12px',
    padding: '2px',
    background: 'linear-gradient(135deg, #ff4444 0%, #ff8800 50%, #ffcc00 100%)',
  },
  inner: {
    background: '#12121a',
    borderRadius: '10px',
    padding: '24px',
    minHeight: '120px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
  },
  title: {
    fontSize: '18px',
    fontWeight: 700,
    color: '#fff',
  },
  refreshBtn: {
    background: 'rgba(255,255,255,0.08)',
    border: '1px solid rgba(255,255,255,0.15)',
    borderRadius: '6px',
    color: '#aaa',
    padding: '6px 12px',
    fontSize: '13px',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  markdown: {
    lineHeight: 1.7,
    fontSize: '14px',
    color: '#d0d0d0',
  },
  skeleton: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '12px',
  },
  error: {
    color: '#ef5350',
    fontSize: '14px',
  },
} as const

function SkeletonLines() {
  return (
    <div style={styles.skeleton}>
      {[100, 92, 85, 60].map((w, i) => (
        <div
          key={i}
          className="skeleton-pulse"
          style={{
            height: '14px',
            width: `${w}%`,
            borderRadius: '4px',
            background: 'rgba(255,255,255,0.06)',
          }}
        />
      ))}
    </div>
  )
}

export default function CoachingCard({ sessionId, lapNumber }: Props) {
  const [advice, setAdvice] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchCoaching = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await api.getCoaching(sessionId, lapNumber)
      setAdvice(result.advice)
    } catch (e: any) {
      setError(e.message || 'Failed to load coaching')
    } finally {
      setLoading(false)
    }
  }, [sessionId, lapNumber])

  useEffect(() => {
    fetchCoaching()
  }, [fetchCoaching])

  return (
    <div style={styles.wrapper}>
      <div style={styles.inner}>
        <div style={styles.header}>
          <span style={styles.title}>AI Coach Analysis</span>
          <button
            style={styles.refreshBtn}
            onClick={fetchCoaching}
            disabled={loading}
            title="Refresh"
          >
            {loading ? '...' : '↻ Refresh'}
          </button>
        </div>

        {loading && <SkeletonLines />}
        {error && <div style={styles.error}>{error}</div>}
        {!loading && !error && advice && (
          <div style={styles.markdown} className="coaching-markdown">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{advice}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}
