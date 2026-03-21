import Plot from '../plotly'
import type { CompareResult } from '../api'

/* eslint-disable @typescript-eslint/no-explicit-any */
const BASE: any = {
  paper_bgcolor: '#0a0a0f',
  plot_bgcolor: '#12121a',
  font: { color: '#aaa', size: 11 },
  margin: { l: 50, r: 20, t: 30, b: 40 },
  legend: { orientation: 'h', y: -0.15 },
  xaxis: { gridcolor: '#1e1e2a', title: 'Track Position' },
  yaxis: { gridcolor: '#1e1e2a' },
  height: 280,
}

interface Props {
  data: CompareResult
  refLabel: string
  targetLabel: string
}

export default function CompareChart({ data, refLabel, targetLabel }: Props) {
  const pos = data.positions

  return (
    <div>
      <Plot
        data={[
          {
            x: pos,
            y: data.delta_time_ms.map(d => d / 1000),
            type: 'scatter',
            mode: 'lines',
            name: 'Delta',
            line: { width: 2 },
            fill: 'tozeroy',
            fillcolor: 'rgba(255,68,68,0.15)',
          } as any,
        ]}
        layout={{
          ...BASE,
          yaxis: { gridcolor: '#1e1e2a', title: 'Delta (s)', zeroline: true, zerolinecolor: '#444' },
          title: `Time Delta (+ = ${targetLabel} slower)`,
        }}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: '100%' }}
      />

      <Plot
        data={[
          { x: pos, y: data.ref_speed, type: 'scatter', mode: 'lines', name: refLabel, line: { color: '#4fc3f7', width: 1.5 } } as any,
          { x: pos, y: data.target_speed, type: 'scatter', mode: 'lines', name: targetLabel, line: { color: '#ff8a65', width: 1.5 } } as any,
        ]}
        layout={{
          ...BASE,
          yaxis: { gridcolor: '#1e1e2a', title: 'km/h' },
          title: 'Speed Comparison',
        }}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: '100%' }}
      />

      <Plot
        data={[
          { x: pos, y: data.ref_throttle, type: 'scatter', mode: 'lines', name: `${refLabel} Throttle`, line: { color: '#66bb6a', width: 1 } } as any,
          { x: pos, y: data.target_throttle, type: 'scatter', mode: 'lines', name: `${targetLabel} Throttle`, line: { color: '#66bb6a', width: 1, dash: 'dash' } } as any,
          { x: pos, y: data.ref_brake, type: 'scatter', mode: 'lines', name: `${refLabel} Brake`, line: { color: '#ef5350', width: 1 } } as any,
          { x: pos, y: data.target_brake, type: 'scatter', mode: 'lines', name: `${targetLabel} Brake`, line: { color: '#ef5350', width: 1, dash: 'dash' } } as any,
        ]}
        layout={{
          ...BASE,
          yaxis: { gridcolor: '#1e1e2a', title: '%', range: [0, 1.05] },
          title: 'Inputs Comparison',
        }}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: '100%' }}
      />

      <div style={{
        background: '#16161e',
        border: '1px solid #2a2a3a',
        borderRadius: '8px',
        padding: '16px',
        textAlign: 'center',
        marginTop: '16px',
        fontSize: '18px',
      }}>
        Total Delta:{' '}
        <span style={{ color: data.total_delta_ms > 0 ? '#ef5350' : '#66bb6a', fontWeight: 700 }}>
          {data.total_delta_ms > 0 ? '+' : ''}{(data.total_delta_ms / 1000).toFixed(3)}s
        </span>
      </div>
    </div>
  )
}
