'use client'

import { FullMessage } from "@/types/chat"
import { DynamicChart } from "@/components/DynamicChart"
import { ActionDraftsPanel } from "./ActionDraftsPanel"
import { TrustPanel } from "./TrustPanel"

interface AssistantMessageContentProps {
  message: FullMessage
  showSql: boolean
  selectedChartIndex: number
  onChartSelect: (index: number) => void
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
  onDraftActions,
  onApproveAction,
  drafting,
  approvingByAction,
}: AssistantMessageContentProps) {
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

      {showSql && message.sql && (
        <pre className="mb-3 bg-black/40 border border-neutral-700 text-neutral-300 text-xs p-3 overflow-auto rounded">
          {message.sql}
        </pre>
      )}

      {message.chartData && message.chartConfig && (
        <div className="mt-4">
          {message.chartOptions && message.chartOptions.length > 1 && (
            <div className="mb-3 flex flex-wrap gap-2">
              {message.chartOptions.map((option, index) => (
                <button
                  key={`${message.id}-${option.type}-${index}`}
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
            data={message.chartData}
            config={message.chartOptions?.[selectedChartIndex] ?? message.chartConfig}
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
