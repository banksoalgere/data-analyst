'use client'

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
