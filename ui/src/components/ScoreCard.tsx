interface Props {
  score: {
    overall: number
    braking: number
    throttle: number
    consistency: number
    smoothness: number
  }
}

function scoreColor(s: number): string {
  if (s >= 80) return '#66bb6a'
  if (s >= 60) return '#ffa726'
  return '#ef5350'
}

function ArcGauge({ value, label, size = 80 }: { value: number; label: string; size?: number }) {
  const r = (size - 10) / 2
  const cx = size / 2
  const cy = size / 2 + 4
  const startAngle = -220
  const endAngle = 40
  const totalArc = endAngle - startAngle
  const filledArc = totalArc * (value / 100)

  const polarToCartesian = (angle: number) => {
    const rad = (angle * Math.PI) / 180
    return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) }
  }

  const describeArc = (start: number, sweep: number) => {
    const s = polarToCartesian(start)
    const e = polarToCartesian(start + sweep)
    const largeArc = Math.abs(sweep) > 180 ? 1 : 0
    return `M ${s.x} ${s.y} A ${r} ${r} 0 ${largeArc} 1 ${e.x} ${e.y}`
  }

  const color = scoreColor(value)

  return (
    <div style={{ textAlign: 'center', flex: '1 1 0' }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <path
          d={describeArc(startAngle, totalArc)}
          fill="none"
          stroke="rgba(255,255,255,0.08)"
          strokeWidth={5}
          strokeLinecap="round"
        />
        <path
          d={describeArc(startAngle, filledArc)}
          fill="none"
          stroke={color}
          strokeWidth={5}
          strokeLinecap="round"
          style={{
            filter: `drop-shadow(0 0 4px ${color}60)`,
            transition: 'all 0.5s ease',
          }}
        />
        <text
          x={cx}
          y={cy - 2}
          textAnchor="middle"
          fill={color}
          fontSize={size > 90 ? 24 : 18}
          fontWeight={700}
        >
          {value}
        </text>
      </svg>
      <div style={{ fontSize: '11px', color: '#888', marginTop: '-6px' }}>{label}</div>
    </div>
  )
}

const styles = {
  container: {
    display: 'flex',
    gap: '8px',
    padding: '16px 8px',
    background: '#16161e',
    borderRadius: '10px',
    border: '1px solid #2a2a3a',
    justifyContent: 'center',
    alignItems: 'flex-start',
  },
} as const

export default function ScoreCard({ score }: Props) {
  return (
    <div style={styles.container}>
      <ArcGauge value={score.overall} label="Overall" size={96} />
      <ArcGauge value={score.braking} label="Braking" />
      <ArcGauge value={score.throttle} label="Throttle" />
      <ArcGauge value={score.consistency} label="Consistency" />
      <ArcGauge value={score.smoothness} label="Smoothness" />
    </div>
  )
}
