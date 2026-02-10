'use client'

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
  '#3b82f6', // blue
  '#10b981', // green
  '#f59e0b', // amber
  '#ef4444', // red
  '#8b5cf6', // purple
  '#ec4899', // pink
  '#14b8a6', // teal
  '#f97316', // orange
]

export function DynamicChart({ data, config }: DynamicChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 bg-neutral-900 border border-neutral-800 rounded-lg">
        <p className="text-neutral-500">No data to display</p>
      </div>
    )
  }

  const groupedKeys = config.groupBy
    ? Array.from(new Set(data.map((row) => String(row[config.groupBy as string])))).slice(0, 8)
    : []

  const groupedData = config.groupBy
    ? Array.from(
      data.reduce((acc, row) => {
        const xValue = String(row[config.xKey])
        const groupValue = String(row[config.groupBy as string])
        const yRaw = Number(row[config.yKey])
        if (!xValue || !groupValue || Number.isNaN(yRaw)) return acc

        if (!acc.has(xValue)) {
          acc.set(xValue, { [config.xKey]: xValue })
        }
        const bucket = acc.get(xValue) as Record<string, unknown>
        bucket[groupValue] = (Number(bucket[groupValue] ?? 0) + yRaw)
        return acc
      }, new Map<string, Record<string, unknown>>()).values()
    )
    : data

  const renderChart = () => {
    switch (config.type) {
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={groupedData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#404040" />
              <XAxis
                dataKey={config.xKey}
                stroke="#a3a3a3"
                style={{ fontSize: '12px' }}
              />
              <YAxis stroke="#a3a3a3" style={{ fontSize: '12px' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#262626',
                  border: '1px solid #404040',
                  borderRadius: '8px',
                  color: '#fff',
                }}
              />
              <Legend
                wrapperStyle={{ paddingTop: '20px', fontSize: '12px' }}
              />
              {groupedKeys.length > 0 ? groupedKeys.map((key, index) => (
                <Line
                  key={key}
                  type="monotone"
                  name={key}
                  dataKey={key}
                  stroke={COLORS[index % COLORS.length]}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 5 }}
                />
              )) : (
                <Line
                  type="monotone"
                  dataKey={config.yKey}
                  stroke={COLORS[0]}
                  strokeWidth={2}
                  dot={{ fill: COLORS[0], r: 4 }}
                  activeDot={{ r: 6 }}
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        )

      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={groupedData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#404040" />
              <XAxis
                dataKey={config.xKey}
                stroke="#a3a3a3"
                style={{ fontSize: '12px' }}
              />
              <YAxis stroke="#a3a3a3" style={{ fontSize: '12px' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#262626',
                  border: '1px solid #404040',
                  borderRadius: '8px',
                  color: '#fff',
                }}
              />
              <Legend
                wrapperStyle={{ paddingTop: '20px', fontSize: '12px' }}
              />
              {groupedKeys.length > 0 ? groupedKeys.map((key, index) => (
                <Bar
                  key={key}
                  name={key}
                  dataKey={key}
                  fill={COLORS[index % COLORS.length]}
                  radius={[4, 4, 0, 0]}
                />
              )) : (
                <Bar dataKey={config.yKey} fill={COLORS[0]} radius={[4, 4, 0, 0]} />
              )}
            </BarChart>
          </ResponsiveContainer>
        )

      case 'area':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={groupedData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#404040" />
              <XAxis
                dataKey={config.xKey}
                stroke="#a3a3a3"
                style={{ fontSize: '12px' }}
              />
              <YAxis stroke="#a3a3a3" style={{ fontSize: '12px' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#262626',
                  border: '1px solid #404040',
                  borderRadius: '8px',
                  color: '#fff',
                }}
              />
              <Legend
                wrapperStyle={{ paddingTop: '20px', fontSize: '12px' }}
              />
              {groupedKeys.length > 0 ? groupedKeys.map((key, index) => (
                <Area
                  key={key}
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
              <XAxis
                dataKey={config.xKey}
                type="number"
                stroke="#a3a3a3"
                style={{ fontSize: '12px' }}
              />
              <YAxis
                dataKey={config.yKey}
                type="number"
                stroke="#a3a3a3"
                style={{ fontSize: '12px' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#262626',
                  border: '1px solid #404040',
                  borderRadius: '8px',
                  color: '#fff',
                }}
                cursor={{ strokeDasharray: '3 3' }}
              />
              <Legend
                wrapperStyle={{ paddingTop: '20px', fontSize: '12px' }}
              />
              <Scatter
                name={config.yKey}
                data={data}
                fill={COLORS[0]}
              />
            </ScatterChart>
          </ResponsiveContainer>
        )

      case 'pie':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
              <Pie
                data={data}
                dataKey={config.yKey}
                nameKey={config.xKey}
                cx="50%"
                cy="50%"
                outerRadius={120}
                label={(entry) => entry[config.xKey]}
              >
                {data.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={COLORS[index % COLORS.length]}
                  />
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
              <Legend
                wrapperStyle={{ paddingTop: '20px', fontSize: '12px' }}
              />
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
