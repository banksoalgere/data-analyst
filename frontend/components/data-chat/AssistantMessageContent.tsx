'use client'

import { useState } from "react"
import { FullMessage } from "@/types/chat"
import { DynamicChart } from "@/components/DynamicChart"
import { ActionDraftsPanel } from "./ActionDraftsPanel"
import { ExplorationPanel } from "./ExplorationPanel"
import { TrustPanel } from "./TrustPanel"

interface AssistantMessageContentProps {
  message: FullMessage
  showSql: boolean
  selectedChartIndex: number
  onChartSelect: (index: number) => void
  selectedProbeId?: string | null
  onProbeSelect: (probeId: string) => void
  onDraftActions: () => void
  onApproveAction: (actionId: string) => void
  drafting: boolean
  approvingByAction: Record<string, boolean>
}

function toNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value
  }
  if (typeof value === "string") {
    const parsed = Number.parseFloat(value)
    if (Number.isFinite(parsed)) {
      return parsed
    }
  }
  return null
}

function countWords(text: string): number {
  const trimmed = text.trim()
  if (!trimmed) return 0
  return trimmed.split(/\s+/).length
}

export function AssistantMessageContent({
  message,
  showSql,
  selectedChartIndex,
  onChartSelect,
  selectedProbeId,
  onProbeSelect,
  onDraftActions,
  onApproveAction,
  drafting,
  approvingByAction,
}: AssistantMessageContentProps) {
  const [showNerdStats, setShowNerdStats] = useState(false)
  const probes = Array.isArray(message.exploration?.probes) ? message.exploration?.probes : []
  const fallbackProbeId = message.exploration?.primary_probe_id ?? probes[0]?.probe_id
  const activeProbeId = selectedProbeId ?? fallbackProbeId
  const activeProbe = probes.find((probe) => probe.probe_id === activeProbeId)

  const activeChartData =
    Array.isArray(activeProbe?.chart_data) && activeProbe.chart_data.length > 0
      ? activeProbe.chart_data
      : message.chartData
  const activeChartOptions =
    Array.isArray(activeProbe?.chart_options) && activeProbe.chart_options.length > 0
      ? activeProbe.chart_options
      : message.chartOptions
  const activeChartConfig = activeProbe?.chart_config ?? message.chartConfig
  const activeSql = activeProbe?.sql ?? message.sql
  const trust = message.trust && typeof message.trust === "object" ? (message.trust as Record<string, unknown>) : null
  const provenance =
    trust && trust.provenance && typeof trust.provenance === "object"
      ? (trust.provenance as Record<string, unknown>)
      : {}
  const limitations = trust && Array.isArray(trust.limitations) ? trust.limitations : []

  const rowCount = message.rowCount ?? toNumber(provenance.rows_analyzed) ?? activeProbe?.row_count ?? null
  const visualizedRowCount =
    message.visualizedRowCount ?? toNumber(provenance.rows_visualized) ?? activeChartData?.length ?? null
  const rowCoverage = rowCount && rowCount > 0 && visualizedRowCount !== null ? (visualizedRowCount / rowCount) * 100 : null
  const activeChart = activeChartOptions?.[selectedChartIndex] ?? activeChartConfig
  const chartTypes = Array.from(
    new Set((activeChartOptions ?? []).map((option) => option.type).filter((type) => Boolean(type)))
  )
  if (activeChart && activeChart.type && !chartTypes.includes(activeChart.type)) {
    chartTypes.push(activeChart.type)
  }
  const probeRowCounts = probes
    .map((probe) => probe.row_count)
    .filter((count): count is number => typeof count === "number")
  const totalProbeRows = probeRowCounts.reduce((sum, count) => sum + count, 0)
  const averageProbeRows = probeRowCounts.length ? totalProbeRows / probeRowCounts.length : null
  const maxProbeRows = probeRowCounts.length ? Math.max(...probeRowCounts) : null
  const minProbeRows = probeRowCounts.length ? Math.min(...probeRowCounts) : null

  const nerdStats = {
    rowCount,
    visualizedRowCount,
    rowCoverage,
    chartPointCount: activeChartData?.length ?? 0,
    chartOptionCount: activeChartOptions?.length ?? (activeChartConfig ? 1 : 0),
    chartTypes,
    activeChartType: activeChart?.type ?? null,
    probeCount: probes.length,
    totalProbeRows,
    averageProbeRows,
    maxProbeRows,
    minProbeRows,
    insightWords: countWords(message.message),
    insightChars: message.message.length,
    sqlLines: activeSql ? activeSql.split(/\r?\n/).length : 0,
    sqlChars: activeSql ? activeSql.length : 0,
    confidenceScore: toNumber(trust?.confidence_score),
    latencyMs: toNumber(provenance.latency_ms),
    provenanceKeyCount: Object.keys(provenance).length,
    limitationCount: limitations.length,
    followUpCount: message.followUpQuestions?.length ?? 0,
    actionDraftCount: message.actionDrafts?.length ?? 0,
    primaryProbeId: message.exploration?.primary_probe_id ?? null,
  }

  return (
    <>
      {message.analysisType && (
        <div className="mb-3 text-xs inline-flex items-center gap-2 border border-neutral-700 text-neutral-300 px-2 py-1 rounded">
          <span className="uppercase tracking-wide">analysis</span>
          <span className="text-white">{message.analysisType}</span>
        </div>
      )}

      {message.trust && typeof message.trust === "object" && (
        <TrustPanel trust={message.trust as Record<string, unknown>} />
      )}

      <div className="mb-3">
        <button
          type="button"
          onClick={() => setShowNerdStats((previous) => !previous)}
          aria-expanded={showNerdStats}
          className="text-xs border border-neutral-700 px-2 py-1 rounded text-neutral-300 hover:text-white hover:border-neutral-500 transition-colors"
        >
          {showNerdStats ? "Hide Nerd Stats" : "Status for Nerds"}
        </button>
      </div>

      {showNerdStats && (
        <div className="mb-3 rounded border border-neutral-800 bg-neutral-950 p-3">
          <div className="text-xs font-medium text-neutral-200">Deep stats for this result</div>
          <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
            <div className="rounded border border-neutral-800 bg-neutral-900 px-2 py-2 text-xs text-neutral-300">
              rows analyzed: {nerdStats.rowCount ?? "n/a"}
            </div>
            <div className="rounded border border-neutral-800 bg-neutral-900 px-2 py-2 text-xs text-neutral-300">
              rows visualized: {nerdStats.visualizedRowCount ?? "n/a"}
            </div>
            <div className="rounded border border-neutral-800 bg-neutral-900 px-2 py-2 text-xs text-neutral-300">
              visualization ratio:{" "}
              {nerdStats.rowCoverage !== null ? `${nerdStats.rowCoverage.toFixed(1)}%` : "n/a"}
            </div>
            <div className="rounded border border-neutral-800 bg-neutral-900 px-2 py-2 text-xs text-neutral-300">
              active chart: {nerdStats.activeChartType ?? "n/a"}
            </div>
            <div className="rounded border border-neutral-800 bg-neutral-900 px-2 py-2 text-xs text-neutral-300">
              chart points: {nerdStats.chartPointCount}
            </div>
            <div className="rounded border border-neutral-800 bg-neutral-900 px-2 py-2 text-xs text-neutral-300">
              chart options: {nerdStats.chartOptionCount}
            </div>
            <div className="rounded border border-neutral-800 bg-neutral-900 px-2 py-2 text-xs text-neutral-300">
              insight size: {nerdStats.insightWords} words / {nerdStats.insightChars} chars
            </div>
            <div className="rounded border border-neutral-800 bg-neutral-900 px-2 py-2 text-xs text-neutral-300">
              SQL size: {nerdStats.sqlLines} lines / {nerdStats.sqlChars} chars
            </div>
            <div className="rounded border border-neutral-800 bg-neutral-900 px-2 py-2 text-xs text-neutral-300">
              confidence: {nerdStats.confidenceScore !== null ? nerdStats.confidenceScore.toFixed(2) : "n/a"}
            </div>
            <div className="rounded border border-neutral-800 bg-neutral-900 px-2 py-2 text-xs text-neutral-300">
              latency: {nerdStats.latencyMs !== null ? `${nerdStats.latencyMs} ms` : "n/a"}
            </div>
            <div className="rounded border border-neutral-800 bg-neutral-900 px-2 py-2 text-xs text-neutral-300">
              follow-ups: {nerdStats.followUpCount}
            </div>
            <div className="rounded border border-neutral-800 bg-neutral-900 px-2 py-2 text-xs text-neutral-300">
              drafted actions: {nerdStats.actionDraftCount}
            </div>
            <div className="rounded border border-neutral-800 bg-neutral-900 px-2 py-2 text-xs text-neutral-300">
              provenance fields: {nerdStats.provenanceKeyCount}
            </div>
            <div className="rounded border border-neutral-800 bg-neutral-900 px-2 py-2 text-xs text-neutral-300">
              limitations: {nerdStats.limitationCount}
            </div>
            <div className="rounded border border-neutral-800 bg-neutral-900 px-2 py-2 text-xs text-neutral-300">
              probes: {nerdStats.probeCount}
            </div>
            <div className="rounded border border-neutral-800 bg-neutral-900 px-2 py-2 text-xs text-neutral-300">
              primary probe: {nerdStats.primaryProbeId ?? "n/a"}
            </div>
          </div>

          <div className="mt-3 text-xs text-neutral-400">
            chart types observed: {nerdStats.chartTypes.length ? nerdStats.chartTypes.join(", ") : "none"}
          </div>

          {nerdStats.probeCount > 0 && (
            <div className="mt-2 text-xs text-neutral-400">
              probe rows total/avg/min/max: {nerdStats.totalProbeRows} /{" "}
              {nerdStats.averageProbeRows !== null ? nerdStats.averageProbeRows.toFixed(1) : "n/a"} /{" "}
              {nerdStats.minProbeRows ?? "n/a"} / {nerdStats.maxProbeRows ?? "n/a"}
            </div>
          )}
        </div>
      )}

      {message.exploration && (
        <ExplorationPanel
          exploration={message.exploration}
          selectedProbeId={activeProbeId}
          onProbeSelect={onProbeSelect}
        />
      )}

      {showSql && activeSql && (
        <pre className="mb-3 bg-black/40 border border-neutral-700 text-neutral-300 text-xs p-3 overflow-auto rounded">
          {activeSql}
        </pre>
      )}

      {activeChartData && activeChartConfig && (
        <div className="mt-4">
          {activeProbe && (
            <div className="mb-3 text-xs text-neutral-400">
              Visualizing: <span className="text-neutral-200">{activeProbe.question}</span>
            </div>
          )}

          {activeChartOptions && activeChartOptions.length > 1 && (
            <div className="mb-3 flex flex-wrap gap-2">
              {activeChartOptions.map((option, index) => (
                <button
                  key={`${message.id}-${activeProbeId ?? "summary"}-${option.type}-${index}`}
                  type="button"
                  onClick={() => onChartSelect(index)}
                  className={`text-xs border px-2 py-1 rounded transition-colors ${
                    selectedChartIndex === index
                      ? 'border-neutral-500 text-white bg-neutral-800'
                      : 'border-neutral-700 text-neutral-300 hover:text-white hover:border-neutral-500'
                  }`}
                >
                  {option.type}
                </button>
              ))}
            </div>
          )}

          <DynamicChart
            data={activeChartData}
            config={activeChartOptions?.[selectedChartIndex] ?? activeChartConfig}
          />
        </div>
      )}

      <div className="mt-3">
        <button
          type="button"
          onClick={onDraftActions}
          className="text-xs border border-neutral-700 px-2 py-1 rounded text-neutral-300 hover:text-white hover:border-neutral-500 transition-colors disabled:opacity-60"
          disabled={drafting || !message.sql}
        >
          {drafting ? "Drafting actions..." : "Ask-Data-Then-Act"}
        </button>
      </div>

      <ActionDraftsPanel
        drafts={message.actionDrafts ?? []}
        approvingByAction={approvingByAction}
        onApprove={onApproveAction}
      />
    </>
  )
}
