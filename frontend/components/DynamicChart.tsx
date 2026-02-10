'use client'

import { memo, useMemo } from 'react'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  ScatterChart,
  Scatter,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

interface ChartConfig {
  type: 'line' | 'bar' | 'scatter' | 'pie' | 'area'
  xKey: string
  yKey: string
  groupBy?: string
}

interface DynamicChartProps {
  data: Array<Record<string, unknown>>
  config: ChartConfig
}

const COLORS = [
  '#3b82f6',
  '#10b981',
  '#f59e0b',
  '#ef4444',
  '#8b5cf6',
  '#ec4899',
  '#14b8a6',
  '#f97316',
]

const MAX_LINE_POINTS = 280
const MAX_SCATTER_POINTS = 650
const MAX_BAR_POINTS = 30
const MAX_PIE_POINTS = 12

function toNumber(value: unknown): number | null {
  if (value === null || value === undefined || typeof value === 'boolean') return null
  if (typeof value === 'number') return Number.isFinite(value) ? value : null
  const parsed = Number(String(value).replace(',', ''))
  return Number.isFinite(parsed) ? parsed : null
}

function sampleEvenly(rows: Array<Record<string, unknown>>, maxPoints: number) {
  if (rows.length <= maxPoints) return rows
  const step = Math.max(1, Math.floor(rows.length / maxPoints))
  const sampled = rows.filter((_, index) => index % step === 0)
  if (sampled[sampled.length - 1] !== rows[rows.length - 1]) {
    sampled.push(rows[rows.length - 1])
  }
  return sampled.slice(0, maxPoints)
}

function aggregateTopCategories(
  rows: Array<Record<string, unknown>>,
  xKey: string,
  yKey: string,
  maxPoints: number
) {
  const buckets = new Map<string, number>()
  for (const row of rows) {
    const x = row[xKey]
    const y = toNumber(row[yKey])
    if (x === null || x === undefined || y === null) continue
    const label = String(x)
    buckets.set(label, (buckets.get(label) ?? 0) + y)
  }

  const ranked = Array.from(buckets.entries()).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
  if (ranked.length <= maxPoints) {
    return ranked.map(([key, value]) => ({ [xKey]: key, [yKey]: value }))
  }

  const top = ranked.slice(0, maxPoints - 1)
  const otherTotal = ranked.slice(maxPoints - 1).reduce((sum, [, value]) => sum + value, 0)
  return [
    ...top.map(([key, value]) => ({ [xKey]: key, [yKey]: value })),
    { [xKey]: 'Other', [yKey]: otherTotal },
  ]
}

function optimizeForChart(
  rows: Array<Record<string, unknown>>,
  config: ChartConfig
): Array<Record<string, unknown>> {
  if (!rows.length) return rows

  if (config.type === 'line' || config.type === 'area') {
    return sampleEvenly(rows, MAX_LINE_POINTS)
  }
  if (config.type === 'scatter') {
    return sampleEvenly(rows, MAX_SCATTER_POINTS)
  }
  if (config.type === 'bar') {
    if (config.groupBy) return sampleEvenly(rows, MAX_LINE_POINTS)
    return aggregateTopCategories(rows, config.xKey, config.yKey, MAX_BAR_POINTS)
  }
  if (config.type === 'pie') {
    return aggregateTopCategories(rows, config.xKey, config.yKey, MAX_PIE_POINTS)
  }
  return rows
}

function DynamicChartView({ data, config }: DynamicChartProps) {
  const optimizedData = useMemo(() => optimizeForChart(data, config), [data, config])

  const groupedKeys = useMemo(
    () => (config.groupBy
      ? Array.from(new Set(optimizedData.map((row) => String(row[config.groupBy as string])))).slice(0, 8)
      : []),
    [optimizedData, config.groupBy]
  )

  const groupedData = useMemo(() => {
    if (!config.groupBy) return optimizedData

    return Array.from(
      optimizedData.reduce((acc, row) => {
        const xValue = String(row[config.xKey])
        const groupValue = String(row[config.groupBy as string])
        const yRaw = toNumber(row[config.yKey])
        if (!xValue || !groupValue || yRaw === null) return acc

        if (!acc.has(xValue)) {
          acc.set(xValue, { [config.xKey]: xValue })
        }
        const bucket = acc.get(xValue) as Record<string, unknown>
        bucket[groupValue] = (toNumber(bucket[groupValue]) ?? 0) + yRaw
        return acc
      }, new Map<string, Record<string, unknown>>()).values()
    )
  }, [optimizedData, config.groupBy, config.xKey, config.yKey])

  if (!optimizedData.length) {
    return (
      <div className="flex items-center justify-center h-64 bg-neutral-900 border border-neutral-800 rounded-lg">
        <p className="text-neutral-500">No data to display</p>
      </div>
    )
  }

  const chartData = config.groupBy ? groupedData : optimizedData

  const renderChart = () => {
    switch (config.type) {
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#404040" />
              <XAxis dataKey={config.xKey} stroke="#a3a3a3" style={{ fontSize: '12px' }} minTickGap={24} />
              <YAxis stroke="#a3a3a3" style={{ fontSize: '12px' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#262626',
                  border: '1px solid #404040',
                  borderRadius: '8px',
                  color: '#fff',
                }}
              />
              <Legend wrapperStyle={{ paddingTop: '20px', fontSize: '12px' }} />
              {groupedKeys.length > 0 ? groupedKeys.map((key, index) => (
                <Line
                  key={key}
                  isAnimationActive={false}
                  type="monotone"
                  name={key}
                  dataKey={key}
                  stroke={COLORS[index % COLORS.length]}
                  strokeWidth={2}
                  dot={false}
                />
              )) : (
                <Line
                  isAnimationActive={false}
                  type="monotone"
                  dataKey={config.yKey}
                  stroke={COLORS[0]}
                  strokeWidth={2}
                  dot={false}
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        )

      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#404040" />
              <XAxis dataKey={config.xKey} stroke="#a3a3a3" style={{ fontSize: '12px' }} minTickGap={24} />
              <YAxis stroke="#a3a3a3" style={{ fontSize: '12px' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#262626',
                  border: '1px solid #404040',
                  borderRadius: '8px',
                  color: '#fff',
                }}
              />
              <Legend wrapperStyle={{ paddingTop: '20px', fontSize: '12px' }} />
              {groupedKeys.length > 0 ? groupedKeys.map((key, index) => (
                <Bar
                  key={key}
                  isAnimationActive={false}
                  name={key}
                  dataKey={key}
                  fill={COLORS[index % COLORS.length]}
                  radius={[4, 4, 0, 0]}
                />
              )) : (
                <Bar isAnimationActive={false} dataKey={config.yKey} fill={COLORS[0]} radius={[4, 4, 0, 0]} />
              )}
            </BarChart>
          </ResponsiveContainer>
        )

      case 'area':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#404040" />
              <XAxis dataKey={config.xKey} stroke="#a3a3a3" style={{ fontSize: '12px' }} minTickGap={24} />
              <YAxis stroke="#a3a3a3" style={{ fontSize: '12px' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#262626',
                  border: '1px solid #404040',
                  borderRadius: '8px',
                  color: '#fff',
                }}
              />
              <Legend wrapperStyle={{ paddingTop: '20px', fontSize: '12px' }} />
              {groupedKeys.length > 0 ? groupedKeys.map((key, index) => (
                <Area
                  key={key}
                  isAnimationActive={false}
                  type="monotone"
                  name={key}
                  dataKey={key}
                  stroke={COLORS[index % COLORS.length]}
                  fill={COLORS[index % COLORS.length]}
                  fillOpacity={0.2}
                  stackId="grouped"
                />
              )) : (
                <Area
                  isAnimationActive={false}
                  type="monotone"
                  dataKey={config.yKey}
                  stroke={COLORS[0]}
                  fill={COLORS[0]}
                  fillOpacity={0.6}
                />
              )}
            </AreaChart>
          </ResponsiveContainer>
        )

      case 'scatter':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" stroke="#404040" />
              <XAxis dataKey={config.xKey} type="number" stroke="#a3a3a3" style={{ fontSize: '12px' }} />
              <YAxis dataKey={config.yKey} type="number" stroke="#a3a3a3" style={{ fontSize: '12px' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#262626',
                  border: '1px solid #404040',
                  borderRadius: '8px',
                  color: '#fff',
                }}
                cursor={{ strokeDasharray: '3 3' }}
              />
              <Legend wrapperStyle={{ paddingTop: '20px', fontSize: '12px' }} />
              <Scatter isAnimationActive={false} name={config.yKey} data={optimizedData} fill={COLORS[0]} />
            </ScatterChart>
          </ResponsiveContainer>
        )

      case 'pie':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
              <Pie
                isAnimationActive={false}
                data={optimizedData}
                dataKey={config.yKey}
                nameKey={config.xKey}
                cx="50%"
                cy="50%"
                outerRadius={120}
                label={optimizedData.length <= 10 ? (entry) => String(entry[config.xKey]) : false}
              >
                {optimizedData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: '#262626',
                  border: '1px solid #404040',
                  borderRadius: '8px',
                  color: '#fff',
                }}
              />
              <Legend wrapperStyle={{ paddingTop: '20px', fontSize: '12px' }} />
            </PieChart>
          </ResponsiveContainer>
        )

      default:
        return <div className="text-neutral-500">Unsupported chart type</div>
    }
  }

  return (
    <div className="bg-neutral-950 border border-neutral-800 rounded-lg p-6">
      {renderChart()}
    </div>
  )
}

export const DynamicChart = memo(DynamicChartView)
