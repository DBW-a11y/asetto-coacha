import Plotly from 'plotly.js-dist-min'
import { useRef, useEffect, memo } from 'react'

interface PlotProps {
  data: any[]
  layout?: Record<string, any>
  config?: Record<string, any>
  style?: React.CSSProperties
}

const Plot = memo(({ data, layout, config, style }: PlotProps) => {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!ref.current) return
    ;(Plotly as any).react(ref.current, data, layout, config)
    return () => {
      if (ref.current) (Plotly as any).purge(ref.current)
    }
  }, [data, layout, config])

  return <div ref={ref} style={style} />
})

export default Plot
