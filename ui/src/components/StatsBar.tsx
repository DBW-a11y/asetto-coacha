interface StatItem {
  label: string
  value: string
  unit?: string
}

interface Props {
  stats: StatItem[]
}

const styles = {
  bar: {
    display: 'flex',
    flexWrap: 'wrap' as const,
    gap: '12px',
    padding: '16px',
    background: '#16161e',
    borderRadius: '10px',
    border: '1px solid #2a2a3a',
  },
  item: {
    flex: '1 1 120px',
    padding: '8px 12px',
    background: 'rgba(255,255,255,0.03)',
    borderRadius: '8px',
    textAlign: 'center' as const,
  },
  label: {
    fontSize: '11px',
    color: '#666',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px',
    marginBottom: '4px',
  },
  value: {
    fontSize: '20px',
    fontWeight: 700,
    color: '#fff',
  },
  unit: {
    fontSize: '12px',
    color: '#666',
    marginLeft: '2px',
  },
} as const

export default function StatsBar({ stats }: Props) {
  return (
    <div style={styles.bar}>
      {stats.map((s, i) => (
        <div key={i} style={styles.item}>
          <div style={styles.label}>{s.label}</div>
          <div style={styles.value}>
            {s.value}
            {s.unit && <span style={styles.unit}>{s.unit}</span>}
          </div>
        </div>
      ))}
    </div>
  )
}
