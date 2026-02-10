'use client'

import { useEffect, useMemo, useState } from "react"

interface SchemaColumn {
  column_name: string
  column_type: string
}

interface MLLabProps {
  sessionId: string | null
  schema: SchemaColumn[]
}

interface RegressionResult {
  metrics?: {
    r_squared?: number
    rmse?: number
    mae?: number
  }
  top_drivers?: Array<{ feature: string; coefficient: number }>
}

interface AnomalyResult {
  anomaly_count?: number
  rows_analyzed?: number
  anomalies?: Array<{
    source_row_index: number
    metric_value: number
    abs_z_score: number
    group_value?: string | null
  }>
}

const NUMERIC_HINTS = [
  "TINYINT",
  "SMALLINT",
  "INTEGER",
  "BIGINT",
  "HUGEINT",
  "FLOAT",
  "DOUBLE",
  "DECIMAL",
  "REAL",
]

function isLikelyNumericType(columnType: string): boolean {
  const normalized = (columnType || "").toUpperCase()
  return NUMERIC_HINTS.some((hint) => normalized.includes(hint))
}

export function MLLab({ sessionId, schema }: MLLabProps) {
  const numericColumns = useMemo(
    () => schema.filter((column) => isLikelyNumericType(column.column_type)).map((column) => column.column_name),
    [schema]
  )
  const allColumns = useMemo(() => schema.map((column) => column.column_name), [schema])

  const [targetColumn, setTargetColumn] = useState("")
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([])
  const [regressionLoading, setRegressionLoading] = useState(false)
  const [regressionError, setRegressionError] = useState<string | null>(null)
  const [regressionResult, setRegressionResult] = useState<RegressionResult | null>(null)

  const [metricColumn, setMetricColumn] = useState("")
  const [groupByColumn, setGroupByColumn] = useState("")
  const [zThreshold, setZThreshold] = useState("3")
  const [anomalyLoading, setAnomalyLoading] = useState(false)
  const [anomalyError, setAnomalyError] = useState<string | null>(null)
  const [anomalyResult, setAnomalyResult] = useState<AnomalyResult | null>(null)

  useEffect(() => {
    if (!numericColumns.length) {
      setTargetColumn("")
      setMetricColumn("")
      setSelectedFeatures([])
      return
    }

    const nextTarget = numericColumns[0]
    setTargetColumn(nextTarget)
    setMetricColumn(nextTarget)
    setSelectedFeatures(numericColumns.filter((column) => column !== nextTarget).slice(0, 4))
  }, [numericColumns])

  useEffect(() => {
    if (!targetColumn) {
      setSelectedFeatures([])
      return
    }
    setSelectedFeatures((previous) => previous.filter((feature) => feature !== targetColumn))
  }, [targetColumn])

  const toggleFeature = (feature: string) => {
    setSelectedFeatures((previous) => {
      if (previous.includes(feature)) {
        return previous.filter((item) => item !== feature)
      }
      return [...previous, feature]
    })
  }

  const runRegression = async () => {
    if (!sessionId || !targetColumn) return

    setRegressionLoading(true)
    setRegressionError(null)
    setRegressionResult(null)
    try {
      const response = await fetch("/api/ml/regression", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          target_column: targetColumn,
          feature_columns: selectedFeatures,
          test_fraction: 0.2,
          max_rows: 12000,
        }),
      })

      const payload = await response.json()
      if (!response.ok) {
        throw new Error(payload.detail || "Regression failed")
      }
      setRegressionResult(payload as RegressionResult)
    } catch (error) {
      setRegressionError(error instanceof Error ? error.message : "Regression failed")
    } finally {
      setRegressionLoading(false)
    }
  }

  const runAnomalyDetection = async () => {
    if (!sessionId || !metricColumn) return

    setAnomalyLoading(true)
    setAnomalyError(null)
    setAnomalyResult(null)
    try {
      const response = await fetch("/api/ml/anomalies", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          metric_column: metricColumn,
          group_by: groupByColumn || null,
          z_threshold: Number.parseFloat(zThreshold) || 3,
          max_results: 20,
          max_rows: 20000,
        }),
      })

      const payload = await response.json()
      if (!response.ok) {
        throw new Error(payload.detail || "Anomaly detection failed")
      }
      setAnomalyResult(payload as AnomalyResult)
    } catch (error) {
      setAnomalyError(error instanceof Error ? error.message : "Anomaly detection failed")
    } finally {
      setAnomalyLoading(false)
    }
  }

  if (!sessionId) {
    return null
  }

  if (!numericColumns.length) {
    return (
      <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-white">ML Lab</h3>
        <p className="text-xs text-neutral-400 mt-1">
          This dataset does not expose numeric columns, so regression and anomaly detection are unavailable.
        </p>
      </div>
    )
  }

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4 space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-white">ML Lab</h3>
        <p className="text-xs text-neutral-400 mt-1">
          Run fast regression and anomaly detection on your uploaded dataset.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-3">
          <div className="text-sm font-medium text-white">Linear Regression</div>
          <label className="block text-xs text-neutral-400">
            Target column
            <select
              className="mt-1 w-full bg-neutral-950 border border-neutral-800 rounded px-3 py-2 text-sm text-white"
              value={targetColumn}
              onChange={(event) => setTargetColumn(event.target.value)}
            >
              {numericColumns.map((column) => (
                <option key={column} value={column}>
                  {column}
                </option>
              ))}
            </select>
          </label>

          <div>
            <div className="text-xs text-neutral-400 mb-1">Feature columns</div>
            <div className="max-h-36 overflow-y-auto border border-neutral-800 rounded p-2 space-y-1">
              {numericColumns
                .filter((column) => column !== targetColumn)
                .map((column) => (
                  <label key={column} className="flex items-center gap-2 text-xs text-neutral-300">
                    <input
                      type="checkbox"
                      checked={selectedFeatures.includes(column)}
                      onChange={() => toggleFeature(column)}
                    />
                    <span>{column}</span>
                  </label>
                ))}
            </div>
          </div>

          <button
            type="button"
            onClick={runRegression}
            disabled={regressionLoading || !targetColumn}
            className="text-xs border border-neutral-700 px-3 py-2 rounded text-neutral-200 hover:text-white hover:border-neutral-500 disabled:opacity-50"
          >
            {regressionLoading ? "Running regression..." : "Run Regression"}
          </button>

          {regressionError && <div className="text-xs text-red-400">{regressionError}</div>}
          {regressionResult && (
            <div className="text-xs text-neutral-300 space-y-1">
              <div>R²: {regressionResult.metrics?.r_squared ?? "n/a"}</div>
              <div>RMSE: {regressionResult.metrics?.rmse ?? "n/a"}</div>
              <div>MAE: {regressionResult.metrics?.mae ?? "n/a"}</div>
              {Array.isArray(regressionResult.top_drivers) && regressionResult.top_drivers.length > 0 && (
                <div className="mt-2">
                  <div className="text-neutral-400 mb-1">Top drivers</div>
                  {regressionResult.top_drivers.slice(0, 6).map((driver) => (
                    <div key={driver.feature}>
                      {driver.feature}: {driver.coefficient}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="space-y-3">
          <div className="text-sm font-medium text-white">Anomaly Detection</div>
          <label className="block text-xs text-neutral-400">
            Metric column
            <select
              className="mt-1 w-full bg-neutral-950 border border-neutral-800 rounded px-3 py-2 text-sm text-white"
              value={metricColumn}
              onChange={(event) => setMetricColumn(event.target.value)}
            >
              {numericColumns.map((column) => (
                <option key={column} value={column}>
                  {column}
                </option>
              ))}
            </select>
          </label>

          <label className="block text-xs text-neutral-400">
            Group by (optional)
            <select
              className="mt-1 w-full bg-neutral-950 border border-neutral-800 rounded px-3 py-2 text-sm text-white"
              value={groupByColumn}
              onChange={(event) => setGroupByColumn(event.target.value)}
            >
              <option value="">None</option>
              {allColumns.map((column) => (
                <option key={column} value={column}>
                  {column}
                </option>
              ))}
            </select>
          </label>

          <label className="block text-xs text-neutral-400">
            Z-score threshold
            <input
              className="mt-1 w-full bg-neutral-950 border border-neutral-800 rounded px-3 py-2 text-sm text-white"
              value={zThreshold}
              onChange={(event) => setZThreshold(event.target.value)}
            />
          </label>

          <button
            type="button"
            onClick={runAnomalyDetection}
            disabled={anomalyLoading || !metricColumn}
            className="text-xs border border-neutral-700 px-3 py-2 rounded text-neutral-200 hover:text-white hover:border-neutral-500 disabled:opacity-50"
          >
            {anomalyLoading ? "Detecting anomalies..." : "Detect Anomalies"}
          </button>

          {anomalyError && <div className="text-xs text-red-400">{anomalyError}</div>}
          {anomalyResult && (
            <div className="text-xs text-neutral-300 space-y-1">
              <div>Rows analyzed: {anomalyResult.rows_analyzed ?? "n/a"}</div>
              <div>Anomalies found: {anomalyResult.anomaly_count ?? "n/a"}</div>
              {Array.isArray(anomalyResult.anomalies) && anomalyResult.anomalies.length > 0 && (
                <div className="mt-2 space-y-1">
                  <div className="text-neutral-400 mb-1">Top anomalies</div>
                  {anomalyResult.anomalies.slice(0, 6).map((item) => (
                    <div key={`${item.source_row_index}-${item.abs_z_score}`}>
                      row {item.source_row_index}: value={item.metric_value}, |z|={item.abs_z_score}
                      {item.group_value ? `, group=${item.group_value}` : ""}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
