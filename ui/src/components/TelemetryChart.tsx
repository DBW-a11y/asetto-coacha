import Plot from '../plotly'
import type { TelemetryData } from '../api'

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
  data: TelemetryData
}

export default function TelemetryChart({ data }: Props) {
  const pos = data.normalized_pos

  return (
    <div>
      <Plot
        data={[
          { x: pos, y: data.speed_kmh, type: 'scatter', mode: 'lines', name: 'Speed', line: { color: '#4fc3f7', width: 1.5 } } as any,
        ]}
        layout={{ ...BASE, yaxis: { gridcolor: '#1e1e2a', title: 'km/h' }, title: 'Speed' }}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: '100%' }}
      />

      <Plot
        data={[
          { x: pos, y: data.throttle, type: 'scatter', mode: 'lines', name: 'Throttle', line: { color: '#66bb6a', width: 1.5 }, fill: 'tozeroy', fillcolor: 'rgba(102,187,106,0.1)' } as any,
          { x: pos, y: data.brake, type: 'scatter', mode: 'lines', name: 'Brake', line: { color: '#ef5350', width: 1.5 }, fill: 'tozeroy', fillcolor: 'rgba(239,83,80,0.1)' } as any,
        ]}
        layout={{ ...BASE, yaxis: { gridcolor: '#1e1e2a', title: '%', range: [0, 1.05] }, title: 'Inputs' }}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: '100%' }}
      />

      <Plot
        data={[
          { x: pos, y: data.gear, type: 'scatter', mode: 'lines', name: 'Gear', line: { color: '#ffa726', width: 1.5 } } as any,
          { x: pos, y: data.steering, type: 'scatter', mode: 'lines', name: 'Steering', line: { color: '#ab47bc', width: 1 }, yaxis: 'y2' } as any,
        ]}
        layout={{
          ...BASE,
          yaxis: { gridcolor: '#1e1e2a', title: 'Gear', side: 'left' },
          yaxis2: { gridcolor: '#1e1e2a', title: 'Steering', overlaying: 'y', side: 'right', range: [-1, 1] },
          title: 'Gear & Steering',
        }}
        config={{ responsive: true, displayModeBar: false }}
        style={{ width: '100%' }}
      />
    </div>
  )
}
