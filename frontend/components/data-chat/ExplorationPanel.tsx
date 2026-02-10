'use client'

import { ExplorationSummary } from "@/types/chat"

interface ExplorationPanelProps {
  exploration: ExplorationSummary
}

export function ExplorationPanel({ exploration }: ExplorationPanelProps) {
  const probes = Array.isArray(exploration.probes) ? exploration.probes : []
  if (!probes.length) return null

  return (
    <div className="mb-3 rounded border border-indigo-900/60 bg-indigo-950/20 p-3 space-y-2">
      <div className="text-xs text-indigo-200 font-medium">
        Multi-step exploration: {exploration.analysis_goal}
      </div>
      <div className="space-y-1.5">
        {probes.map((probe) => {
          const isPrimary = probe.probe_id === exploration.primary_probe_id
          return (
            <div
              key={probe.probe_id}
              className={`rounded border p-2 text-xs ${
                isPrimary
                  ? "border-indigo-700 bg-indigo-900/30 text-indigo-100"
                  : "border-neutral-800 bg-neutral-950 text-neutral-300"
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-medium">{probe.question}</span>
                <span className="uppercase tracking-wide">{probe.analysis_type}</span>
              </div>
              <div className="mt-1 text-neutral-400">rows: {probe.row_count}</div>
              {probe.rationale && <div className="mt-1 text-neutral-400">{probe.rationale}</div>}
            </div>
          )
        })}
      </div>
    </div>
  )
}
