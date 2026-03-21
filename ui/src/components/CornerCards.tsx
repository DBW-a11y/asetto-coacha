interface Corner {
  corner_name: string
  entry_speed?: number
  min_speed: number
  exit_speed?: number
  max_lateral_g?: number
  trail_braking_pct?: number
  [key: string]: number | string | undefined
}

interface Props {
  corners: Corner[]
}

function speedColor(speed: number): string {
  if (speed > 200) return '#ef5350'
  if (speed > 140) return '#ffa726'
  return '#66bb6a'
}

const styles = {
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
    gap: '12px',
  },
  card: {
    background: '#16161e',
    border: '1px solid #2a2a3a',
    borderRadius: '10px',
    padding: '16px',
    transition: 'border-color 0.2s',
  },
  name: {
    fontSize: '14px',
    fontWeight: 600,
    color: '#fff',
    marginBottom: '10px',
    paddingBottom: '8px',
    borderBottom: '1px solid #1e1e2e',
  },
  row: {
    display: 'flex',
    justifyContent: 'space-between',
    fontSize: '12px',
    padding: '3px 0',
  },
  label: { color: '#666' },
  value: { color: '#ccc', fontWeight: 500 },
} as const

export default function CornerCards({ corners }: Props) {
  return (
    <div style={styles.grid}>
      {corners.map((c, i) => (
        <div key={i} style={styles.card}>
          <div style={styles.name}>{c.corner_name}</div>
          {c.entry_speed != null && (
            <div style={styles.row}>
              <span style={styles.label}>Entry</span>
              <span style={{ ...styles.value, color: speedColor(c.entry_speed) }}>
                {c.entry_speed.toFixed(0)} km/h
              </span>
            </div>
          )}
          <div style={styles.row}>
            <span style={styles.label}>Apex</span>
            <span style={{ ...styles.value, color: speedColor(c.min_speed) }}>
              {c.min_speed.toFixed(0)} km/h
            </span>
          </div>
          {c.exit_speed != null && (
            <div style={styles.row}>
              <span style={styles.label}>Exit</span>
              <span style={{ ...styles.value, color: speedColor(c.exit_speed) }}>
                {c.exit_speed.toFixed(0)} km/h
              </span>
            </div>
          )}
          {c.max_lateral_g != null && (
            <div style={styles.row}>
              <span style={styles.label}>Lateral G</span>
              <span style={styles.value}>{c.max_lateral_g.toFixed(2)}g</span>
            </div>
          )}
          {c.trail_braking_pct != null && (
            <div style={styles.row}>
              <span style={styles.label}>Trail Brake</span>
              <span style={styles.value}>{(c.trail_braking_pct * 100).toFixed(0)}%</span>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
